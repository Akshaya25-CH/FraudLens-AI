import os
import re
import hashlib
import pandas as pd
from dataset_builder.scam_part1 import SCAM_PART1
from dataset_builder.scam_part2 import SCAM_PART2
from dataset_builder.legit_part1 import LEGIT_PART1
from dataset_builder.legit_part2 import LEGIT_PART2

def normalize_text(text):
    return re.sub(r'\s+', ' ', text.strip().lower())

def get_tokens(text):
    # Extract lowercased alphanumeric tokens
    return set(re.findall(r'\w+', text.lower()))

def jaccard_similarity(set_a, set_b):
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    return intersection / union if union > 0 else 0.0

def main():
    print("=" * 60)
    print("FraudLens AI — Indian SMS Training Dataset Builder & Audit")
    print("=" * 60)

    # 1. Combine datasets
    scam_data = SCAM_PART1 + SCAM_PART2
    legit_data = LEGIT_PART1 + LEGIT_PART2
    all_data = scam_data + legit_data

    print(f"Total Scam messages: {len(scam_data)} (Part 1: {len(SCAM_PART1)}, Part 2: {len(SCAM_PART2)})")
    print(f"Total Legit messages: {len(legit_data)} (Part 1: {len(LEGIT_PART1)}, Part 2: {len(LEGIT_PART2)})")
    print(f"Total Combined messages: {len(all_data)}")

    assert len(scam_data) == 220, f"Expected 220 scam messages, got {len(scam_data)}"
    assert len(legit_data) == 220, f"Expected 220 legit messages, got {len(legit_data)}"
    assert len(all_data) == 440, f"Expected 440 total messages, got {len(all_data)}"

    # 2. Build rows with sequential IDs
    rows = []
    for idx, item in enumerate(all_data, start=1):
        rows.append({
            "id": idx,
            "label": item["label"],
            "category": item["category"],
            "language": item["language"],
            "message": item["message"].strip(),
            "source": item["source"]
        })

    df_train = pd.DataFrame(rows)

    # 3. Integrity & Schema Checks
    print("\n--- Integrity & Schema Checks ---")
    null_counts = df_train.isnull().sum().to_dict()
    print("Null value counts per column:", null_counts)
    assert sum(null_counts.values()) == 0, "Dataset contains null values!"

    source_unique = df_train["source"].unique()
    print(f"Unique source values: {source_unique}")
    assert list(source_unique) == ["synthetic_manually_authored"], "Unexpected source value!"

    # Devanagari Unicode check
    devanagari_regex = re.compile(r'[\u0900-\u097F]')
    devanagari_rows = df_train[df_train["language"] == "Hindi_Devanagari"]
    print(f"Total Hindi_Devanagari rows: {len(devanagari_rows)}")
    non_devanagari = []
    for idx, r in devanagari_rows.iterrows():
        if not devanagari_regex.search(r["message"]):
            non_devanagari.append((r["id"], r["message"]))
    print(f"Hindi_Devanagari rows lacking Devanagari Unicode: {len(non_devanagari)}")
    assert len(non_devanagari) == 0, f"Found non-Devanagari Hindi rows: {non_devanagari}"

    # 4. Class & Language Distributions
    print("\n--- Distributions ---")
    print("Class distribution:")
    print(df_train["label"].value_counts())
    print("\nLanguage distribution (overall):")
    print(df_train["language"].value_counts())
    print("\nLanguage by Label:")
    print(pd.crosstab(df_train["label"], df_train["language"]))
    print("\nCategory breakdown:")
    print(df_train["category"].value_counts())

    # 5. Internal Duplicate Check
    print("\n--- Internal Duplicate Check ---")
    normalized_msgs = [normalize_text(m) for m in df_train["message"]]
    unique_normalized = set(normalized_msgs)
    internal_dups = len(normalized_msgs) - len(unique_normalized)
    print(f"Internal exact/normalized duplicates: {internal_dups}")
    if internal_dups > 0:
        seen = {}
        for idx, nm in enumerate(normalized_msgs):
            if nm in seen:
                print(f"Duplicate found: ID {df_train.iloc[idx]['id']} duplicates ID {seen[nm]}: '{df_train.iloc[idx]['message']}'")
            else:
                seen[nm] = df_train.iloc[idx]['id']
    assert internal_dups == 0, f"Found {internal_dups} internal duplicate messages!"

    # 6. Leakage & Overlap Check against Existing Datasets
    print("\n--- Leakage & Overlap Audit ---")
    # Load Evaluation Dataset
    df_eval = pd.read_csv("datasets/evaluation/indian_sms_eval.csv")
    eval_normalized = [normalize_text(m) for m in df_eval["message"]]
    eval_tokens = [(r["id"], r["category"], r["language"], get_tokens(r["message"])) for _, r in df_eval.iterrows()]

    # Load SMSSpamCollection
    sms_spam_lines = []
    if os.path.exists("datasets/SMSSpamCollection"):
        with open("datasets/SMSSpamCollection", "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                parts = line.strip().split("\t", 1)
                if len(parts) == 2:
                    sms_spam_lines.append(normalize_text(parts[1]))
    print(f"Loaded {len(sms_spam_lines)} messages from SMSSpamCollection")

    # Load sms_dataset.csv
    sms_dataset_lines = []
    if os.path.exists("datasets/sms_dataset.csv"):
        df_sms_legacy = pd.read_csv("datasets/sms_dataset.csv")
        if "message" in df_sms_legacy.columns:
            sms_dataset_lines = [normalize_text(m) for m in df_sms_legacy["message"].dropna()]
    print(f"Loaded {len(sms_dataset_lines)} messages from sms_dataset.csv")

    # Exact matches check
    exact_matches_eval = []
    exact_matches_uci = []
    exact_matches_legacy = []

    for idx, r in df_train.iterrows():
        norm_m = normalize_text(r["message"])
        if norm_m in eval_normalized:
            exact_matches_eval.append((r["id"], r["message"]))
        if norm_m in sms_spam_lines:
            exact_matches_uci.append((r["id"], r["message"]))
        if norm_m in sms_dataset_lines:
            exact_matches_legacy.append((r["id"], r["message"]))

    print(f"Exact matches with indian_sms_eval.csv: {len(exact_matches_eval)}")
    print(f"Exact matches with SMSSpamCollection: {len(exact_matches_uci)}")
    print(f"Exact matches with sms_dataset.csv: {len(exact_matches_legacy)}")
    assert len(exact_matches_eval) == 0, f"Exact leakage into evaluation set: {exact_matches_eval}"
    assert len(exact_matches_uci) == 0, f"Exact duplicates with SMSSpamCollection: {exact_matches_uci}"
    assert len(exact_matches_legacy) == 0, f"Exact duplicates with sms_dataset.csv: {exact_matches_legacy}"

    # 7. Token Jaccard Similarity Audit against Evaluation Set
    print("\n--- Token Jaccard Similarity Audit against Diagnostic Evaluation Set ---")
    high_sim_pairs = []
    max_sim = 0.0
    max_sim_pair = None

    for idx, r in df_train.iterrows():
        t_tokens = get_tokens(r["message"])
        for e_id, e_cat, e_lang, e_tokens in eval_tokens:
            sim = jaccard_similarity(t_tokens, e_tokens)
            if sim > max_sim:
                max_sim = sim
                max_sim_pair = (r["id"], r["message"], e_id, e_cat, e_lang, sim)
            if sim >= 0.70:
                high_sim_pairs.append({
                    "train_id": r["id"],
                    "train_message": r["message"],
                    "eval_id": e_id,
                    "eval_category": e_cat,
                    "eval_language": e_lang,
                    "similarity": sim
                })

    print(f"Maximum Jaccard similarity observed: {max_sim:.4f}")
    if max_sim_pair:
        print(f"Pair with max similarity: Train ID {max_sim_pair[0]} vs Eval ID {max_sim_pair[2]} ({max_sim_pair[5]:.4f})")
        print(f"  Train: '{max_sim_pair[1]}'")
        print(f"  Eval: ID {max_sim_pair[2]}")
    print(f"Pairs with Jaccard similarity >= 0.70: {len(high_sim_pairs)}")

    if high_sim_pairs:
        print("\nWARNING: High similarity pairs detected:")
        for p in high_sim_pairs:
            print(f"- Train ID {p['train_id']} vs Eval ID {p['eval_id']} (Sim: {p['similarity']:.4f})")
            print(f"  Train: {p['train_message']}")

    # 8. Write CSV Output
    os.makedirs("datasets/training", exist_ok=True)
    out_csv_path = "datasets/training/indian_sms_train.csv"
    df_train.to_csv(out_csv_path, index=False, encoding="utf-8")
    print(f"\n[SUCCESS] Saved {len(df_train)} messages to {out_csv_path}")

    # 9. Verify saved file
    df_verify = pd.read_csv(out_csv_path)
    assert len(df_verify) == 440, f"Verification failed: expected 440 rows, got {len(df_verify)}"
    print("[SUCCESS] Verified file row count: 440")

    return {
        "df_train": df_train,
        "max_sim": max_sim,
        "max_sim_pair": max_sim_pair,
        "high_sim_pairs": high_sim_pairs,
        "internal_dups": internal_dups,
        "exact_matches_eval": len(exact_matches_eval),
        "exact_matches_uci": len(exact_matches_uci),
        "exact_matches_legacy": len(exact_matches_legacy),
        "null_counts": null_counts,
        "non_devanagari": len(non_devanagari)
    }

if __name__ == "__main__":
    main()
