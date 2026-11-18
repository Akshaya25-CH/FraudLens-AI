import csv
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import joblib
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

EVAL_PATH = PROJECT_ROOT / "datasets" / "evaluation" / "indian_sms_eval.csv"
MODEL_PATH = PROJECT_ROOT / "models" / "sms_model.joblib"
TRAIN_UCI_PATH = PROJECT_ROOT / "datasets" / "SMSSpamCollection"
TRAIN_CSV_PATH = PROJECT_ROOT / "datasets" / "sms_dataset.csv"


def verify_dataset_separation(eval_df: pd.DataFrame):
    """
    Verifies that the evaluation dataset is strictly separate from all training data
    and contains zero overlaps or copies from training files.
    """
    print("\n[VERIFICATION] Checking for dataset overlap with training sources...")
    train_texts = set()

    if TRAIN_UCI_PATH.exists():
        with open(TRAIN_UCI_PATH, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                parts = line.strip().split("\t", 1)
                if len(parts) == 2:
                    train_texts.add(parts[1].strip().lower())

    if TRAIN_CSV_PATH.exists():
        df_csv = pd.read_csv(TRAIN_CSV_PATH)
        if "message" in df_csv.columns:
            for msg in df_csv["message"].dropna():
                train_texts.add(str(msg).strip().lower())

    eval_texts = eval_df["message"].str.strip().str.lower().tolist()
    overlaps = [msg for msg in eval_texts if msg in train_texts]

    if overlaps:
        print(f"  WARNING: Detected {len(overlaps)} overlapping samples in training set!")
        for o in overlaps:
            print(f"    Overlap: {o}")
        raise ValueError("Evaluation dataset must not contain training examples!")
    else:
        print(f"  CONFIRMED: 0 overlaps found. Evaluation set is 100% held-out from training ({len(eval_texts)} unique samples).")


def run_evaluation():
    print("=" * 75)
    print("FRAUDLENS AI - STEP 2: INDIAN SMS SCAM EVALUATION BASELINE AUDIT")
    print("=" * 75)

    # 1. Load evaluation dataset
    if not EVAL_PATH.exists():
        raise FileNotFoundError(f"Evaluation dataset not found at: {EVAL_PATH}")

    df_eval = pd.read_csv(EVAL_PATH)
    print(f"\nLoaded Evaluation Dataset: {EVAL_PATH.name}")
    print(f"Total Samples: {len(df_eval)}")
    print("Schema Columns:", list(df_eval.columns))

    verify_dataset_separation(df_eval)

    # Validate class counts
    class_counts = df_eval["label"].value_counts().to_dict()
    print("\nClass Distribution:")
    print(f"  Legitimate (0): {class_counts.get(0, 0)}")
    print(f"  Scam / Fraud (1): {class_counts.get(1, 0)}")
    assert class_counts.get(0, 0) == 50 and class_counts.get(1, 0) == 50, "Expected exactly 50 scam and 50 legit samples."

    # Language distribution
    print("\nLanguage Distribution:")
    for lang, count in df_eval["language"].value_counts().items():
        print(f"  {lang:<18}: {count} samples")

    # 2. Load currently saved baseline model
    print("\nLoading current baseline model pipeline from:", MODEL_PATH.name)
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model file not found at: {MODEL_PATH}")

    model = joblib.load(MODEL_PATH)
    print("Model steps:", [name for name, _ in model.steps])
    print("Model classes:", list(model.classes_))

    # 3. Perform inference
    messages = df_eval["message"].tolist()
    y_true = df_eval["label"].tolist()

    y_pred = model.predict(messages)
    y_proba = model.predict_proba(messages)
    fraud_index = list(model.classes_).index(1)
    fraud_scores = [round(float(p[fraud_index]) * 100, 2) for p in y_proba]

    df_eval["predicted"] = y_pred
    df_eval["fraud_score"] = fraud_scores
    df_eval["correct"] = df_eval["label"] == df_eval["predicted"]

    # 4. Overall Baseline Metrics
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, pos_label=1, zero_division=0)
    rec = recall_score(y_true, y_pred, pos_label=1, zero_division=0)
    f1 = f1_score(y_true, y_pred, pos_label=1, zero_division=0)
    cm = confusion_matrix(y_true, y_pred) # [[TN, FP], [FN, TP]]
    tn, fp, fn, tp = cm.ravel()

    print("\n" + "=" * 75)
    print("INITIAL BASELINE MODEL EVALUATION METRICS (INDIAN SMS BENCHMARK)")
    print("=" * 75)
    print(f"Total Evaluation Samples: {len(df_eval)}")
    print(f"Overall Accuracy:         {acc:.4f} ({acc * 100:.2f}%)")
    print(f"Scam Precision (Class 1): {prec:.4f} ({prec * 100:.2f}%)")
    print(f"Scam Recall (Class 1):    {rec:.4f} ({rec * 100:.2f}%)")
    print(f"Scam F1-Score (Class 1):  {f1:.4f} ({f1 * 100:.2f}%)")
    print(f"Legit Specificity (0):    {tn / (tn + fp):.4f} ({tn / (tn + fp) * 100:.2f}%)")

    print("\nConfusion Matrix:")
    print("                          Predicted Legit (0)    Predicted Scam (1)    Total")
    print(f"  Actual Legit (0)              {tn:<22} {fp:<21} {tn + fp}")
    print(f"  Actual Scam (1)               {fn:<22} {tp:<21} {fn + tp}")
    print(f"  Total                         {tn + fn:<22} {fp + tp:<21} {len(df_eval)}")
    print(f"\n  True Positives (TP):  {tp}  (Scams correctly caught)")
    print(f"  True Negatives (TN):  {tn}  (Legitimate correctly permitted)")
    print(f"  False Positives (FP): {fp}  (Legitimate wrongly flagged as scam)")
    print(f"  False Negatives (FN): {fn}  (Scams missed as legitimate)")

    # 5. Breakdown by Language
    print("\n" + "-" * 75)
    print("PERFORMANCE BREAKDOWN BY LANGUAGE")
    print("-" * 75)
    print(f"{'Language':<18} {'Total':<6} {'Scam':<6} {'Legit':<6} {'Acc %':<8} {'Scam Rec %':<12} {'FP':<4} {'FN':<4}")
    print("-" * 75)
    for lang in ["English", "Hinglish", "Hindi_Devanagari"]:
        sub = df_eval[df_eval["language"] == lang]
        sub_y_true = sub["label"]
        sub_y_pred = sub["predicted"]
        s_tot = len(sub)
        s_scam = (sub_y_true == 1).sum()
        s_legit = (sub_y_true == 0).sum()
        s_acc = accuracy_score(sub_y_true, sub_y_pred) * 100
        s_rec = recall_score(sub_y_true, sub_y_pred, pos_label=1, zero_division=0) * 100 if s_scam > 0 else 0
        s_fp = ((sub_y_true == 0) & (sub_y_pred == 1)).sum()
        s_fn = ((sub_y_true == 1) & (sub_y_pred == 0)).sum()
        print(f"{lang:<18} {s_tot:<6} {s_scam:<6} {s_legit:<6} {s_acc:<8.1f} {s_rec:<12.1f} {s_fp:<4} {s_fn:<4}")

    # 6. Breakdown by Scam Category
    print("\n" + "-" * 75)
    print("DETECTION BREAKDOWN BY SCAM CATEGORY (Actual label = 1)")
    print("-" * 75)
    print(f"{'Scam Category':<28} {'Count':<6} {'Caught (TP)':<13} {'Missed (FN)':<13} {'Detection Rate %'}")
    print("-" * 75)
    scam_cats = df_eval[df_eval["label"] == 1]["category"].unique()
    for cat in sorted(scam_cats):
        sub_c = df_eval[(df_eval["label"] == 1) & (df_eval["category"] == cat)]
        c_tot = len(sub_c)
        c_tp = (sub_c["predicted"] == 1).sum()
        c_fn = (sub_c["predicted"] == 0).sum()
        c_rate = (c_tp / c_tot) * 100 if c_tot > 0 else 0
        print(f"{cat:<28} {c_tot:<6} {c_tp:<13} {c_fn:<13} {c_rate:.1f}%")

    # 7. Breakdown by Legitimate Category
    print("\n" + "-" * 75)
    print("FALSE POSITIVE BREAKDOWN BY LEGITIMATE CATEGORY (Actual label = 0)")
    print("-" * 75)
    print(f"{'Legitimate Category':<28} {'Count':<6} {'Clean (TN)':<13} {'False Alarm (FP)':<18} {'Clean Rate %'}")
    print("-" * 75)
    legit_cats = df_eval[df_eval["label"] == 0]["category"].unique()
    for cat in sorted(legit_cats):
        sub_l = df_eval[(df_eval["label"] == 0) & (df_eval["category"] == cat)]
        l_tot = len(sub_l)
        l_tn = (sub_l["predicted"] == 0).sum()
        l_fp = (sub_l["predicted"] == 1).sum()
        l_rate = (l_tn / l_tot) * 100 if l_tot > 0 else 0
        print(f"{cat:<28} {l_tot:<6} {l_tn:<13} {l_fp:<18} {l_rate:.1f}%")

    # 8. List Actual Misclassified Examples
    print("\n" + "=" * 75)
    print(f"MISCLASSIFIED EXAMPLES ANALYSIS (Total Errors: {fn + fp})")
    print("=" * 75)

    false_negatives = df_eval[(df_eval["label"] == 1) & (df_eval["predicted"] == 0)]
    print(f"\nA. FALSE NEGATIVES (Scam missed as Legitimate): {len(false_negatives)}")
    print("-" * 75)
    for idx, row in false_negatives.iterrows():
        print(f"[ID {row['id']:03d}] Lang: {row['language']} | Category: {row['category']} | Model Score: {row['fraud_score']}%")
        print(f"  Message: {row['message']}")
        print()

    false_positives = df_eval[(df_eval["label"] == 0) & (df_eval["predicted"] == 1)]
    print(f"\nB. FALSE POSITIVES (Legitimate misclassified as Scam): {len(false_positives)}")
    print("-" * 75)
    if len(false_positives) == 0:
        print("  None! No legitimate Indian communications were falsely flagged as scams.")
    else:
        for idx, row in false_positives.iterrows():
            print(f"[ID {row['id']:03d}] Lang: {row['language']} | Category: {row['category']} | Model Score: {row['fraud_score']}%")
            print(f"  Message: {row['message']}")
            print()

    print("=" * 75)
    print("BASELINE EVALUATION COMPLETE. MODEL REMAINS UNTOUCHED.")
    print("=" * 75)

    return {
        "acc": acc,
        "prec": prec,
        "rec": rec,
        "f1": f1,
        "cm": cm,
        "fn_count": len(false_negatives),
        "fp_count": len(false_positives),
        "df": df_eval
    }

if __name__ == "__main__":
    run_evaluation()
