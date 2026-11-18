"""
FraudLens AI — Step 5B: Controlled Multilingual SMS Training Experiments
========================================================================
Executes a rigorous, leakage-resistant experimental matrix across Configurations A, B, C, D
and hyperparameter grid (C in [1.0, 3.0, 5.0, 10.0], class_weight in [None, 'balanced']).

Evaluates candidates on an 80/20 template-grouped, stratified validation split
and preserves all artifacts under models/experiments/.
"""

import csv
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import joblib
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.pipeline import FeatureUnion, Pipeline

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.sms_preprocessor import MultilingualSMSPreprocessor

# ---------------------------------------------------------------------------
# Path Configuration & Preservation Check
# ---------------------------------------------------------------------------
BASELINE_MODEL_PATH = PROJECT_ROOT / "models" / "sms_model_baseline.joblib"
LIVE_MODEL_PATH = PROJECT_ROOT / "models" / "sms_model.joblib"
TRAIN_INDIAN_PATH = PROJECT_ROOT / "datasets" / "training" / "indian_sms_train.csv"
EVAL_DIAG_PATH = PROJECT_ROOT / "datasets" / "evaluation" / "indian_sms_eval.csv"
UCI_DATA_PATH = PROJECT_ROOT / "datasets" / "SMSSpamCollection"
SUPP_DATA_PATH = PROJECT_ROOT / "datasets" / "sms_dataset.csv"
EXPERIMENTS_DIR = PROJECT_ROOT / "models" / "experiments"

EXPECTED_BASELINE_SHA256 = "C47360251F4A7C89C21B02D448CBEA6192A1A72D76B06C40ED6497CDB0B91DDA"


def compute_sha256(filepath: Path) -> str:
    """Computes SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest().upper()


def verify_preservation_rules():
    """Enforces strict preservation rules prior to experiment execution."""
    print("=" * 75)
    print("STEP 5B: PRESERVATION AUDIT & CHECKSUM VERIFICATION")
    print("=" * 75)

    assert LIVE_MODEL_PATH.exists(), f"Missing {LIVE_MODEL_PATH}"
    assert BASELINE_MODEL_PATH.exists(), f"Missing {BASELINE_MODEL_PATH}"
    assert TRAIN_INDIAN_PATH.exists(), f"Missing {TRAIN_INDIAN_PATH}"
    assert EVAL_DIAG_PATH.exists(), f"Missing {EVAL_DIAG_PATH}"

    h_live = compute_sha256(LIVE_MODEL_PATH)
    h_base = compute_sha256(BASELINE_MODEL_PATH)

    print(f"Live Model Path:      {LIVE_MODEL_PATH.name}")
    print(f"  SHA-256:            {h_live}")
    print(f"Baseline Model Path:  {BASELINE_MODEL_PATH.name}")
    print(f"  SHA-256:            {h_base}")
    print(f"Expected SHA-256:     {EXPECTED_BASELINE_SHA256}")

    if h_live != EXPECTED_BASELINE_SHA256 or h_base != EXPECTED_BASELINE_SHA256:
        raise ValueError("CRITICAL ERROR: Model SHA-256 hash does not match frozen baseline!")

    print("[CONFIRMED] Both baseline models match expected SHA-256. Strictly preserved.\n")


# ---------------------------------------------------------------------------
# Leakage-Resistant Stratified Group Validation Split
# ---------------------------------------------------------------------------
def extract_template_skeleton(text: str) -> str:
    """Extracts entity-abstracted skeleton for structural clustering."""
    t = text.lower()
    t = re.sub(r'https?://[^\s<>"]+|www\.[^\s<>"]+', '[URL]', t)
    t = re.sub(r'(?<!\d)(?:1800|1860)(?:[-\s]\d{2,4}[-\s]\d{3,4}|[-\s]\d{2}[-\s]\d{2}[-\s]\d{2}|[-\s]?\d{4}|[-\s]?\d{6,8})(?!\d)', '[TOLLFREE]', t)
    t = re.sub(r'(?:(?:\b(?:रुपये|रु|rs\.?|inr|₹)\s*[\d,]+(?:\.\d{1,2})?)|(?:\b[\d,]+(?:\.\d{1,2})?\s*(?:रुपये|रु|rupees|rs\.?|\/-)))(?!\w)', '[AMOUNT]', t)
    t = re.sub(r'\b[a-z]{2}[-\s]?\d{2}[-\s]?[a-z]{1,3}[-\s]?\d{4}\b', '[VEHICLE]', t)
    t = re.sub(r'(\b(?:credit\s+card|debit\s+card|card|कार्ड)\s+(?:ending\s*(?:with\s*)?)?)(?:xx|\*+)?\d{4,}\b', r'\1[CARD]', t)
    t = re.sub(r'(\b(?:a/c|account|acct|खाता)\s+(?:ending\s*(?:with\s*)?)?)(?:xx|\*+)?\d{3,}\b', r'\1[ACCOUNT]', t)
    t = re.sub(r'\b(?:xx|\*{2,})\d{3,}\b', '[ACCOUNT]', t)
    t = re.sub(r'(?<!\d)(?:\+91[-\s]?|91[-\s]?|0)?[6-9]\d{9}(?!\d)', '[PHONE]', t)
    t = re.sub(r'\b\d+\b', '[NUM]', t)
    return re.sub(r'\s+', ' ', t).strip()


def build_validation_split(df_indian: pd.DataFrame) -> Tuple[List[int], List[int], Dict[str, Any]]:
    """
    Creates an exact 80/20 stratified group split (352 train / 88 validation)
    grouping similar templates with similarity >= 0.45 so no template cluster leaks.
    """
    print("-" * 75)
    print("CREATING LEAKAGE-RESISTANT STRATIFIED GROUP VALIDATION SPLIT")
    print("-" * 75)

    skeletons = df_indian["message"].apply(extract_template_skeleton)
    vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5))
    X_skel = vec.fit_transform(skeletons)
    sim = cosine_similarity(X_skel)
    np.fill_diagonal(sim, 0)

    n = len(df_indian)
    adj = np.zeros((n, n), dtype=int)
    sim_threshold = 0.45
    edge_count = 0
    for i in range(n):
        for j in range(i + 1, n):
            if (
                df_indian.iloc[i]["category"] == df_indian.iloc[j]["category"]
                and df_indian.iloc[i]["label"] == df_indian.iloc[j]["label"]
                and sim[i, j] >= sim_threshold
            ):
                adj[i, j] = 1
                adj[j, i] = 1
                edge_count += 1

    n_components, group_labels = connected_components(csr_matrix(adj), directed=False)
    df_indian["group_id"] = group_labels
    print(f"Connected template groups: {n_components} across {n} samples (edges >= {sim_threshold}: {edge_count})")

    groups = []
    for gid in range(n_components):
        members = df_indian[df_indian["group_id"] == gid]
        lbl = int(members["label"].iloc[0])
        langs = members["language"].value_counts().to_dict()
        indices = members.index.tolist()
        groups.append({
            "group_id": gid,
            "label": lbl,
            "size": len(members),
            "indices": indices,
            "eng": langs.get("English", 0),
            "hing": langs.get("Hinglish", 0),
            "dev": langs.get("Hindi_Devanagari", 0),
        })

    # Exact deterministic split selection
    np.random.seed(42)

    def pick_partition(label_val, target_total=44, target_eng=18, target_hing=15, target_dev=11):
        lbl_groups = [g for g in groups if g["label"] == label_val]
        for _ in range(50000):
            np.random.shuffle(lbl_groups)
            curr_indices = []
            tot = eng = hing = dev = 0
            for g in lbl_groups:
                if tot + g["size"] <= target_total:
                    if (
                        eng + g["eng"] <= target_eng + 1
                        and hing + g["hing"] <= target_hing + 1
                        and dev + g["dev"] <= target_dev + 1
                    ):
                        tot += g["size"]
                        eng += g["eng"]
                        hing += g["hing"]
                        dev += g["dev"]
                        curr_indices.extend(g["indices"])
                if tot == target_total and dev == target_dev and abs(eng - target_eng) <= 1:
                    return curr_indices
        raise RuntimeError(f"Could not find exact partition for label {label_val}")

    scam_val = pick_partition(1, 44, 18, 15, 11)
    legit_val = pick_partition(0, 44, 18, 15, 11)

    val_indices = sorted(scam_val + legit_val)
    train_indices = sorted(list(set(range(n)) - set(val_indices)))

    val_df = df_indian.iloc[val_indices]
    train_df = df_indian.iloc[train_indices]

    # Verify zero group leakage
    val_groups = set(val_df["group_id"])
    train_groups = set(train_df["group_id"])
    assert len(val_groups.intersection(train_groups)) == 0, "FATAL: Group leakage detected!"

    # Verify cross-split similarity within same category
    max_cross_sim = 0.0
    for vi in val_indices:
        for ti in train_indices:
            if df_indian.iloc[vi]["category"] == df_indian.iloc[ti]["category"] and sim[vi, ti] > max_cross_sim:
                max_cross_sim = sim[vi, ti]

    split_manifest = {
        "total_samples": n,
        "train_size": len(train_indices),
        "val_size": len(val_indices),
        "split_ratio": f"{len(train_indices) / n * 100:.1f}% / {len(val_indices) / n * 100:.1f}%",
        "random_seed": 42,
        "similarity_threshold": sim_threshold,
        "total_template_groups": int(n_components),
        "group_leakage_count": 0,
        "max_cross_split_similarity": float(round(max_cross_sim, 4)),
        "validation_indices": val_indices,
        "training_indices": train_indices,
        "validation_distribution": {
            "label_counts": {int(k): int(v) for k, v in val_df["label"].value_counts().items()},
            "language_counts": {str(k): int(v) for k, v in val_df["language"].value_counts().items()},
            "category_counts": {str(k): int(v) for k, v in val_df["category"].value_counts().items()},
        },
        "training_distribution": {
            "label_counts": {int(k): int(v) for k, v in train_df["label"].value_counts().items()},
            "language_counts": {str(k): int(v) for k, v in train_df["language"].value_counts().items()},
            "category_counts": {str(k): int(v) for k, v in train_df["category"].value_counts().items()},
        },
    }

    print(f"Validation Partition: {len(val_indices)} samples ({val_df['label'].value_counts().to_dict()})")
    print(f"  Languages:          {val_df['language'].value_counts().to_dict()}")
    print(f"Training Partition:   {len(train_indices)} samples ({train_df['label'].value_counts().to_dict()})")
    print(f"  Languages:          {train_df['language'].value_counts().to_dict()}")
    print(f"Max cross-split intra-category similarity: {max_cross_sim:.4f} (< {sim_threshold})")
    print("[CONFIRMED] Zero template group leakage between train and validation.\n")

    return train_indices, val_indices, split_manifest


# ---------------------------------------------------------------------------
# Training Data Assembler
# ---------------------------------------------------------------------------
def assemble_training_corpora(
    df_indian_train: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Prepares two training corpora:
    1. Combined Corpus: Legacy SMS (UCI + sms_dataset.csv) + Indian SMS train split.
    2. Indian-Only Corpus: Indian SMS train split (352 samples) for ablation study.
    """
    print("-" * 75)
    print("ASSEMBLING TRAINING CORPORA")
    print("-" * 75)

    legacy_dfs = []
    if UCI_DATA_PATH.exists():
        df_uci = pd.read_csv(
            UCI_DATA_PATH,
            sep="\t",
            header=None,
            names=["label_raw", "message"],
            quoting=csv.QUOTE_NONE,
            encoding="utf-8",
        )
        df_uci["label"] = df_uci["label_raw"].astype(str).str.strip().str.lower().map({"ham": 0, "spam": 1})
        df_uci = df_uci.dropna(subset=["message", "label"])[["message", "label"]]
        legacy_dfs.append(df_uci)
        print(f"Loaded SMSSpamCollection: {len(df_uci)} rows")

    if SUPP_DATA_PATH.exists():
        df_supp = pd.read_csv(SUPP_DATA_PATH)
        if "message" in df_supp.columns and "label" in df_supp.columns:
            df_supp = df_supp.dropna(subset=["message", "label"])[["message", "label"]]
            df_supp["label"] = df_supp["label"].astype(int)
            legacy_dfs.append(df_supp)
            print(f"Loaded sms_dataset.csv:    {len(df_supp)} rows")

    df_legacy = pd.concat(legacy_dfs, ignore_index=True)
    df_legacy["message"] = df_legacy["message"].astype(str).str.strip()
    df_legacy = df_legacy.drop_duplicates(subset=["message"])
    print(f"Total Unique Legacy Samples: {len(df_legacy)}")

    # Combine with Indian training partition
    df_combined = pd.concat([df_legacy, df_indian_train[["message", "label"]]], ignore_index=True)
    df_combined["message"] = df_combined["message"].astype(str).str.strip()
    df_combined = df_combined.drop_duplicates(subset=["message"])

    print(f"Combined Training Corpus:    {len(df_combined)} rows ({df_combined['label'].value_counts().to_dict()})")
    print(f"Indian-Only Training Corpus: {len(df_indian_train)} rows ({df_indian_train['label'].value_counts().to_dict()})\n")

    return df_combined, df_indian_train


# ---------------------------------------------------------------------------
# Pipeline Construction
# ---------------------------------------------------------------------------
def build_pipeline(
    config: str,
    C: float,
    class_weight: Any,
) -> Pipeline:
    """Builds scikit-learn Pipeline for Configurations A, B, C, or D."""
    clf = LogisticRegression(
        C=C,
        class_weight=class_weight,
        max_iter=1000,
        random_state=42,
    )

    if config == "Config_A":
        # Baseline Word TF-IDF without Unicode/bracket awareness
        return Pipeline([
            ("tfidf", TfidfVectorizer(
                lowercase=True,
                ngram_range=(1, 2),
                sublinear_tf=True,
            )),
            ("classifier", clf),
        ])

    elif config == "Config_B":
        # Unicode and entity-aware Word TF-IDF
        return Pipeline([
            ("tfidf", TfidfVectorizer(
                lowercase=True,
                ngram_range=(1, 2),
                sublinear_tf=True,
                token_pattern=MultilingualSMSPreprocessor.TOKEN_PATTERN,
            )),
            ("classifier", clf),
        ])

    elif config == "Config_C":
        # Combined Word + Char_wb TF-IDF without full preprocessor
        features = FeatureUnion([
            ("word", TfidfVectorizer(
                lowercase=True,
                ngram_range=(1, 2),
                sublinear_tf=True,
                token_pattern=MultilingualSMSPreprocessor.TOKEN_PATTERN,
            )),
            ("char", TfidfVectorizer(
                lowercase=True,
                analyzer="char_wb",
                ngram_range=(3, 5),
                sublinear_tf=True,
            )),
        ])
        return Pipeline([
            ("features", features),
            ("classifier", clf),
        ])

    elif config == "Config_D":
        # Full Multilingual Preprocessing Pipeline
        preprocessor = MultilingualSMSPreprocessor(
            normalize_unicode=True,
            normalize_entities=True,
        )
        features = FeatureUnion([
            ("word", TfidfVectorizer(
                lowercase=True,
                ngram_range=(1, 2),
                sublinear_tf=True,
                token_pattern=MultilingualSMSPreprocessor.TOKEN_PATTERN,
            )),
            ("char", TfidfVectorizer(
                lowercase=True,
                analyzer="char_wb",
                ngram_range=(3, 5),
                sublinear_tf=True,
            )),
        ])
        return Pipeline([
            ("preprocessor", preprocessor),
            ("features", features),
            ("classifier", clf),
        ])

    else:
        raise ValueError(f"Unknown configuration: {config}")


# ---------------------------------------------------------------------------
# Comprehensive Metrics Evaluation
# ---------------------------------------------------------------------------
def evaluate_model_on_val(
    model: Any,
    val_df: pd.DataFrame,
    model_name: str,
) -> Dict[str, Any]:
    """Computes all required overall, language, category, and slice metrics."""
    messages = val_df["message"].tolist()
    y_true = val_df["label"].tolist()

    y_pred = model.predict(messages)
    y_proba = model.predict_proba(messages)
    fraud_col = list(model.classes_).index(1)
    fraud_scores = [round(float(p[fraud_col]) * 100, 2) for p in y_proba]

    acc = float(accuracy_score(y_true, y_pred))
    prec = float(precision_score(y_true, y_pred, pos_label=1, zero_division=0))
    rec = float(recall_score(y_true, y_pred, pos_label=1, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, pos_label=1, zero_division=0))
    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = [int(v) for v in cm.ravel()]
    spec = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0

    eval_copy = val_df.copy()
    eval_copy["predicted"] = y_pred
    eval_copy["fraud_score"] = fraud_scores
    eval_copy["is_correct"] = eval_copy["label"] == eval_copy["predicted"]

    # Language breakdowns
    lang_metrics = {}
    for lang in ["English", "Hinglish", "Hindi_Devanagari"]:
        sub = eval_copy[eval_copy["language"] == lang]
        sub_yt = sub["label"]
        sub_yp = sub["predicted"]
        s_tot = len(sub)
        s_scam = int((sub_yt == 1).sum())
        s_legit = int((sub_yt == 0).sum())
        s_acc = float(accuracy_score(sub_yt, sub_yp)) if s_tot > 0 else 0.0
        s_rec = float(recall_score(sub_yt, sub_yp, pos_label=1, zero_division=0)) if s_scam > 0 else 0.0
        s_spec = float(recall_score(sub_yt, sub_yp, pos_label=0, zero_division=0)) if s_legit > 0 else 0.0
        s_fp = int(((sub_yt == 0) & (sub_yp == 1)).sum())
        s_fn = int(((sub_yt == 1) & (sub_yp == 0)).sum())
        lang_metrics[lang] = {
            "total": s_tot,
            "scam_total": s_scam,
            "legit_total": s_legit,
            "accuracy": s_acc,
            "scam_recall": s_rec,
            "specificity": s_spec,
            "fp": s_fp,
            "fn": s_fn,
        }

    # Category breakdowns
    scam_cat_metrics = {}
    for cat in sorted(eval_copy[eval_copy["label"] == 1]["category"].unique()):
        sub_c = eval_copy[(eval_copy["label"] == 1) & (eval_copy["category"] == cat)]
        c_tot = len(sub_c)
        c_tp = int((sub_c["predicted"] == 1).sum())
        c_fn = int((sub_c["predicted"] == 0).sum())
        scam_cat_metrics[cat] = {
            "count": c_tot,
            "caught_tp": c_tp,
            "missed_fn": c_fn,
            "recall": float(c_tp / c_tot) if c_tot > 0 else 0.0,
        }

    legit_cat_metrics = {}
    for cat in sorted(eval_copy[eval_copy["label"] == 0]["category"].unique()):
        sub_l = eval_copy[(eval_copy["label"] == 0) & (eval_copy["category"] == cat)]
        l_tot = len(sub_l)
        l_tn = int((sub_l["predicted"] == 0).sum())
        l_fp = int((sub_l["predicted"] == 1).sum())
        legit_cat_metrics[cat] = {
            "count": l_tot,
            "clean_tn": l_tn,
            "false_fp": l_fp,
            "specificity": float(l_tn / l_tot) if l_tot > 0 else 0.0,
        }

    # URL slice breakdown
    eval_copy["has_url"] = eval_copy["message"].str.contains(r"https?://|www\.", regex=True)
    # URL scams vs URL-free scams
    scam_url = eval_copy[(eval_copy["label"] == 1) & (eval_copy["has_url"])]
    scam_no_url = eval_copy[(eval_copy["label"] == 1) & (~eval_copy["has_url"])]
    url_scam_rec = float((scam_url["predicted"] == 1).sum() / len(scam_url)) if len(scam_url) > 0 else 0.0
    nourl_scam_rec = float((scam_no_url["predicted"] == 1).sum() / len(scam_no_url)) if len(scam_no_url) > 0 else 0.0

    return {
        "model_name": model_name,
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1": f1,
        "specificity": spec,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "tp": tp,
        "lang_metrics": lang_metrics,
        "scam_category_metrics": scam_cat_metrics,
        "legit_category_metrics": legit_cat_metrics,
        "url_scam_recall": url_scam_rec,
        "url_scam_count": len(scam_url),
        "nourl_scam_recall": nourl_scam_rec,
        "nourl_scam_count": len(scam_no_url),
        "predictions_series": eval_copy[["id", "label", "predicted", "fraud_score"]],
    }


# ---------------------------------------------------------------------------
# Main Execution Orchestrator
# ---------------------------------------------------------------------------
def run_all_experiments():
    EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Verification
    verify_preservation_rules()

    # 2. Ingest Indian SMS training dataset
    df_indian = pd.read_csv(TRAIN_INDIAN_PATH)
    print(f"Loaded Indian Training Dataset: {TRAIN_INDIAN_PATH.name} ({len(df_indian)} rows)")
    assert len(df_indian) == 440, f"Expected 440 rows, got {len(df_indian)}"
    assert df_indian["label"].value_counts().to_dict() == {0: 220, 1: 220}, "Imbalanced dataset!"

    # 3. Create deterministic stratified group validation split
    train_idx, val_idx, split_manifest = build_validation_split(df_indian)

    # Save validation split manifest
    with open(EXPERIMENTS_DIR / "validation_split.json", "w", encoding="utf-8") as f:
        json.dump(split_manifest, f, indent=2)
    print(f"Saved validation split manifest: {EXPERIMENTS_DIR / 'validation_split.json'}")

    val_df = df_indian.iloc[val_idx].copy().reset_index(drop=True)
    train_indian_df = df_indian.iloc[train_idx].copy().reset_index(drop=True)

    # 4. Assemble training corpora
    df_combined, df_indian_only = assemble_training_corpora(train_indian_df)

    # 5. Evaluate Baseline Model on the Validation Split
    print("=" * 75)
    print("EVALUATING FROZEN BASELINE MODEL ON VALIDATION PARTITION")
    print("=" * 75)
    baseline_model = joblib.load(BASELINE_MODEL_PATH)
    base_metrics = evaluate_model_on_val(baseline_model, val_df, "Untouched_Baseline")
    print(f"Baseline Accuracy:    {base_metrics['accuracy'] * 100:.2f}%")
    print(f"Baseline Scam F1:     {base_metrics['f1'] * 100:.2f}%")
    print(f"Baseline Scam Recall: {base_metrics['recall'] * 100:.2f}% (Missed: {base_metrics['fn']})")
    print(f"Baseline Specificity: {base_metrics['specificity'] * 100:.2f}% (False Positives: {base_metrics['fp']})")
    print(f"Baseline CM:          TN={base_metrics['tn']}, FP={base_metrics['fp']}, FN={base_metrics['fn']}, TP={base_metrics['tp']}")
    print(f"Baseline Devanagari Recall: {base_metrics['lang_metrics']['Hindi_Devanagari']['scam_recall'] * 100:.2f}%\n")

    # 6. Execute Experiment Matrix
    # Grid: Configurations A, B, C, D
    # Hyperparameters: C in [1.0, 3.0, 5.0, 10.0], class_weight in [None, 'balanced']
    # Training regimes: Combined (Primary) and Indian-Only (Ablation)
    all_results = [base_metrics]
    trained_pipelines = {}
    val_predictions_table = pd.DataFrame({
        "id": val_df["id"],
        "category": val_df["category"],
        "language": val_df["language"],
        "ground_truth": val_df["label"],
        "message": val_df["message"],
        "baseline_pred": base_metrics["predictions_series"]["predicted"],
        "baseline_score": base_metrics["predictions_series"]["fraud_score"],
    })

    configs = ["Config_A", "Config_B", "Config_C", "Config_D"]
    c_values = [1.0, 3.0, 5.0, 10.0]
    class_weights = [None, "balanced"]

    print("=" * 75)
    print("EXECUTING EXPERIMENT MATRIX: COMBINED TRAINING REGIME")
    print("=" * 75)
    print(f"{'Experiment Name':<32} {'Acc %':<8} {'Prec %':<8} {'Rec %':<8} {'F1 %':<8} {'Spec %':<8} {'FP':<4} {'FN':<4} {'Dev Rec %':<10}")
    print("-" * 96)

    for cfg in configs:
        for c in c_values:
            for cw in class_weights:
                cw_tag = "balanced" if cw == "balanced" else "unweighted"
                exp_name = f"{cfg}_C{c}_{cw_tag}"

                pipeline = build_pipeline(cfg, c, cw)
                pipeline.fit(df_combined["message"], df_combined["label"])

                metrics = evaluate_model_on_val(pipeline, val_df, exp_name)
                metrics["training_regime"] = "Combined"
                metrics["config"] = cfg
                metrics["C"] = c
                metrics["class_weight"] = cw_tag
                all_results.append(metrics)
                trained_pipelines[exp_name] = pipeline

                dev_rec = metrics["lang_metrics"]["Hindi_Devanagari"]["scam_recall"] * 100
                print(
                    f"{exp_name:<32} "
                    f"{metrics['accuracy']*100:<8.2f} "
                    f"{metrics['precision']*100:<8.2f} "
                    f"{metrics['recall']*100:<8.2f} "
                    f"{metrics['f1']*100:<8.2f} "
                    f"{metrics['specificity']*100:<8.2f} "
                    f"{metrics['fp']:<4} "
                    f"{metrics['fn']:<4} "
                    f"{dev_rec:<10.1f}"
                )

                # Append predictions to table for key models
                val_predictions_table[f"{exp_name}_pred"] = metrics["predictions_series"]["predicted"]
                val_predictions_table[f"{exp_name}_score"] = metrics["predictions_series"]["fraud_score"]

    print("\n" * 1)
    print("=" * 75)
    print("EXECUTING ABLATION: INDIAN-ONLY TRAINING REGIME (176 scam / 176 legit)")
    print("=" * 75)
    print(f"{'Experiment Name':<32} {'Acc %':<8} {'Prec %':<8} {'Rec %':<8} {'F1 %':<8} {'Spec %':<8} {'FP':<4} {'FN':<4} {'Dev Rec %':<10}")
    print("-" * 96)

    # In Indian-only, class_weight is 1:1, so only test cw=None
    for cfg in configs:
        for c in c_values:
            exp_name = f"{cfg}_C{c}_IndianOnly"
            pipeline = build_pipeline(cfg, c, None)
            pipeline.fit(df_indian_only["message"], df_indian_only["label"])

            metrics = evaluate_model_on_val(pipeline, val_df, exp_name)
            metrics["training_regime"] = "IndianOnly"
            metrics["config"] = cfg
            metrics["C"] = c
            metrics["class_weight"] = "unweighted"
            all_results.append(metrics)
            trained_pipelines[exp_name] = pipeline

            dev_rec = metrics["lang_metrics"]["Hindi_Devanagari"]["scam_recall"] * 100
            print(
                f"{exp_name:<32} "
                f"{metrics['accuracy']*100:<8.2f} "
                f"{metrics['precision']*100:<8.2f} "
                f"{metrics['recall']*100:<8.2f} "
                f"{metrics['f1']*100:<8.2f} "
                f"{metrics['specificity']*100:<8.2f} "
                f"{metrics['fp']:<4} "
                f"{metrics['fn']:<4} "
                f"{dev_rec:<10.1f}"
            )

    # 7. Model and Artifact Archival
    print("\n" + "=" * 75)
    print("ARCHIVING EXPERIMENTAL ARTIFACTS TO models/experiments/")
    print("=" * 75)

    # Filter candidates satisfying selection criteria: Scam_F1 max subject to FP <= 3 and Devanagari_Recall >= 0.80
    combined_candidates = [m for m in all_results if m.get("training_regime") == "Combined"]
    valid_candidates = [
        m for m in combined_candidates
        if m["fp"] <= 3 and m["lang_metrics"]["Hindi_Devanagari"]["scam_recall"] >= 0.80
    ]
    valid_candidates.sort(key=lambda x: (x["f1"], x["recall"], -x["fp"]), reverse=True)

    print(f"Candidates satisfying selection criteria (FP <= 3, Dev Recall >= 80%): {len(valid_candidates)}")
    if valid_candidates:
        top_cand = valid_candidates[0]
        print(f"Top Recommended Candidate: {top_cand['model_name']}")
        print(f"  F1-Score:    {top_cand['f1']*100:.2f}%")
        print(f"  Recall:      {top_cand['recall']*100:.2f}% (Missed: {top_cand['fn']})")
        print(f"  Precision:   {top_cand['precision']*100:.2f}%")
        print(f"  Specificity: {top_cand['specificity']*100:.2f}% (FP: {top_cand['fp']})")
        print(f"  URL Scam Rec: {top_cand['url_scam_recall']*100:.2f}% | URL-Free Scam Rec: {top_cand['nourl_scam_recall']*100:.2f}%")

    # Save models: top candidates and best of each configuration
    best_per_config = {}
    for cfg in configs:
        cfg_models = [m for m in combined_candidates if m.get("config") == cfg]
        cfg_models.sort(key=lambda x: (x["f1"], -x["fp"]), reverse=True)
        if cfg_models:
            best_per_config[cfg] = cfg_models[0]["model_name"]

    print("\nSaving best candidate models per configuration:")
    for cfg, mname in best_per_config.items():
        save_path = EXPERIMENTS_DIR / f"{mname.lower()}.joblib"
        joblib.dump(trained_pipelines[mname], save_path)
        print(f"  Saved: {save_path.name}")

    # Also save top 3 recommended candidates
    for rank, cand in enumerate(valid_candidates[:3], 1):
        mname = cand["model_name"]
        save_path = EXPERIMENTS_DIR / f"rank{rank}_{mname.lower()}.joblib"
        joblib.dump(trained_pipelines[mname], save_path)
        print(f"  Saved Top Candidate #{rank}: {save_path.name}")

    # Save experiment results CSV and JSON
    summary_rows = []
    for m in all_results:
        summary_rows.append({
            "model_name": m["model_name"],
            "regime": m.get("training_regime", "Baseline"),
            "config": m.get("config", "Baseline"),
            "C": m.get("C", "N/A"),
            "class_weight": m.get("class_weight", "N/A"),
            "accuracy": round(m["accuracy"], 4),
            "precision": round(m["precision"], 4),
            "recall": round(m["recall"], 4),
            "f1": round(m["f1"], 4),
            "specificity": round(m["specificity"], 4),
            "tp": m["tp"],
            "fp": m["fp"],
            "tn": m["tn"],
            "fn": m["fn"],
            "eng_recall": round(m["lang_metrics"]["English"]["scam_recall"], 4),
            "eng_spec": round(m["lang_metrics"]["English"]["specificity"], 4),
            "hing_recall": round(m["lang_metrics"]["Hinglish"]["scam_recall"], 4),
            "hing_spec": round(m["lang_metrics"]["Hinglish"]["specificity"], 4),
            "dev_recall": round(m["lang_metrics"]["Hindi_Devanagari"]["scam_recall"], 4),
            "dev_spec": round(m["lang_metrics"]["Hindi_Devanagari"]["specificity"], 4),
            "url_scam_recall": round(m["url_scam_recall"], 4),
            "nourl_scam_recall": round(m["nourl_scam_recall"], 4),
        })

    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(EXPERIMENTS_DIR / "experiment_results.csv", index=False)
    print(f"Saved: {EXPERIMENTS_DIR / 'experiment_results.csv'}")

    with open(EXPERIMENTS_DIR / "experiment_results.json", "w", encoding="utf-8") as f:
        # Convert non-serializable elements
        json_results = []
        for r in all_results:
            r_copy = {k: v for k, v in r.items() if k != "predictions_series"}
            json_results.append(r_copy)
        json.dump(json_results, f, indent=2)
    print(f"Saved: {EXPERIMENTS_DIR / 'experiment_results.json'}")

    # Save predictions table
    val_predictions_table.to_csv(EXPERIMENTS_DIR / "validation_predictions.csv", index=False)
    print(f"Saved: {EXPERIMENTS_DIR / 'validation_predictions.csv'}")

    # 8. Final Checksum Preservation Check
    print("\n" + "=" * 75)
    print("FINAL PRESERVATION INTEGRITY CONFIRMATION")
    print("=" * 75)
    final_live_hash = compute_sha256(LIVE_MODEL_PATH)
    final_base_hash = compute_sha256(BASELINE_MODEL_PATH)
    assert final_live_hash == EXPECTED_BASELINE_SHA256, "Live model was altered!"
    assert final_base_hash == EXPECTED_BASELINE_SHA256, "Baseline model was altered!"
    print(f"Live Model Hash:     {final_live_hash} [MATCH: TRUE]")
    print(f"Baseline Model Hash: {final_base_hash} [MATCH: TRUE]")
    print("[SUCCESS] Step 5B experiments completed with 100% baseline preservation.\n")


if __name__ == "__main__":
    run_all_experiments()
