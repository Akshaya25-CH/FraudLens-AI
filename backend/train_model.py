import csv
import sys
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

# ---------------------------------------------------------------------------
# Path Configuration
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
PRIMARY_DATA_PATH = BASE_DIR / "datasets" / "SMSSpamCollection"
SUPPLEMENTARY_DATA_PATH = BASE_DIR / "datasets" / "sms_dataset.csv"
MODEL_PATH = BASE_DIR / "models" / "sms_model.joblib"


def load_and_preprocess_data() -> pd.DataFrame:
    """
    Loads the primary UCI SMSSpamCollection dataset, standardizes labels,
    merges preserved domain-specific samples, and performs data cleaning.
    """
    if not PRIMARY_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Primary dataset not found at: {PRIMARY_DATA_PATH}. "
            "Ensure datasets/SMSSpamCollection is placed correctly."
        )

    print(f"Loading primary dataset from: {PRIMARY_DATA_PATH.name}")
    try:
        # The UCI dataset is tab-separated: label (ham/spam) \t message text
        # Using csv.QUOTE_NONE ensures messages containing quotation marks are not truncated
        df_primary = pd.read_csv(
            PRIMARY_DATA_PATH,
            sep="\t",
            header=None,
            names=["label_raw", "message"],
            quoting=csv.QUOTE_NONE,
            encoding="utf-8"
        )
    except Exception as e:
        raise RuntimeError(f"Failed to read {PRIMARY_DATA_PATH}: {e}")

    # Standardize labels: ham = 0, spam = 1
    label_mapping = {"ham": 0, "spam": 1}
    df_primary["label"] = df_primary["label_raw"].astype(str).str.strip().str.lower().map(label_mapping)
    df_primary = df_primary[["message", "label"]].copy()

    # Verify no unmapped labels
    if df_primary["label"].isnull().any():
        unmapped = df_primary[df_primary["label"].isnull()]["label_raw"].unique()
        raise ValueError(f"Unrecognized labels detected in primary dataset: {unmapped}")

    print(f"Primary dataset loaded: {len(df_primary)} rows")

    # Load and preserve existing supplementary dataset (sms_dataset.csv) if present
    dataframes = [df_primary]
    if SUPPLEMENTARY_DATA_PATH.exists():
        print(f"Loading preserved domain-specific dataset: {SUPPLEMENTARY_DATA_PATH.name}")
        try:
            df_supp = pd.read_csv(SUPPLEMENTARY_DATA_PATH)
            if "message" in df_supp.columns and "label" in df_supp.columns:
                df_supp = df_supp[["message", "label"]].copy()
                df_supp["label"] = df_supp["label"].astype(int)
                dataframes.append(df_supp)
                print(f"Supplementary dataset loaded: {len(df_supp)} rows")
        except Exception as e:
            print(f"Warning: Could not read supplementary dataset ({e}). Proceeding with primary.")

    # Combine datasets
    df = pd.concat(dataframes, ignore_index=True)

    # Clean and validate data
    initial_count = len(df)
    df = df.dropna(subset=["message", "label"])
    df["message"] = df["message"].astype(str).str.strip()
    df = df[df["message"].str.len() > 0]
    df["label"] = df["label"].astype(int)

    # Check and report duplicates
    dup_count = df.duplicated(subset=["message"]).sum()
    print(f"Duplicate messages detected: {dup_count} (removing duplicates)")
    df = df.drop_duplicates(subset=["message"], keep="first").copy()

    cleaned_count = len(df)
    print(f"Cleaned dataset rows: {cleaned_count} (removed {initial_count - cleaned_count} rows)")
    print("\nClass distribution:")
    counts = df["label"].value_counts()
    for lbl, count in counts.items():
        name = "Ham / Legitimate (0)" if lbl == 0 else "Spam / Fraud (1)"
        pct = (count / cleaned_count) * 100
        print(f"  {name}: {count} ({pct:.1f}%)")

    # Ensure both classes exist
    if set(df["label"].unique()) != {0, 1}:
        raise ValueError("Dataset must contain both classes 0 (ham) and 1 (spam).")

    return df


def train_and_evaluate(df: pd.DataFrame):
    """
    Splits data with 80/20 stratified split, trains a TF-IDF + LogisticRegression
    pipeline, evaluates on the held-out test set, and saves the trained model.
    """
    print("\nSplitting dataset into 80% training and 20% testing sets (stratified, seed=42)...")
    X_train, X_test, y_train, y_test = train_test_split(
        df["message"],
        df["label"],
        test_size=0.20,
        random_state=42,
        stratify=df["label"]
    )

    print(f"Training set size: {len(X_train)} samples")
    print(f"Test set size:     {len(X_test)} samples")

    # Build scikit-learn Pipeline
    # TfidfVectorizer extracts unigram and bigram word features with sublinear term-frequency scaling
    # LogisticRegression with C=5.0 provides balanced regularization for imbalanced text classification
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 2),
            sublinear_tf=True
        )),
        ("classifier", LogisticRegression(
            C=5.0,
            max_iter=1000,
            random_state=42
        ))
    ])

    print("\nTraining TF-IDF + Logistic Regression pipeline...")
    pipeline.fit(X_train, y_train)

    # Evaluate on held-out test split
    print("\nEvaluating model on held-out test data (20% split)...")
    predictions = pipeline.predict(X_test)

    acc = accuracy_score(y_test, predictions)
    prec = precision_score(y_test, predictions, zero_division=0)
    rec = recall_score(y_test, predictions, zero_division=0)
    f1 = f1_score(y_test, predictions, zero_division=0)
    cm = confusion_matrix(y_test, predictions)

    print("\n" + "=" * 60)
    print("MODEL EVALUATION RESULTS (HELD-OUT TEST SET)")
    print("=" * 60)
    print(f"Accuracy:         {acc:.4f} ({acc * 100:.2f}%)")
    print(f"Precision (Spam): {prec:.4f} ({prec * 100:.2f}%)")
    print(f"Recall (Spam):    {rec:.4f} ({rec * 100:.2f}%)")
    print(f"F1-Score:         {f1:.4f}")

    print("\nConfusion Matrix:")
    print("               Predicted Ham (0)   Predicted Spam (1)")
    print(f"Actual Ham (0)       {cm[0][0]:<19} {cm[0][1]}")
    print(f"Actual Spam (1)      {cm[1][0]:<19} {cm[1][1]}")

    print("\nDetailed Classification Report:")
    print(classification_report(
        y_test,
        predictions,
        target_names=["Ham / Legitimate", "Spam / Fraud"],
        digits=4,
        zero_division=0
    ))
    print("Note: Reported metrics reflect performance on the held-out test split.")
    print("Real-world fraud detection may encounter novel adversarial patterns.")
    print("=" * 60)

    # Verify model class labels and predict_proba compatibility
    assert hasattr(pipeline, "classes_"), "Pipeline must expose classes_"
    assert list(pipeline.classes_) == [0, 1], f"Expected classes [0, 1], got {pipeline.classes_}"

    # Save trained pipeline
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH)
    print(f"\nTrained model pipeline saved successfully to:\n{MODEL_PATH}")

    # Quick sanity check with sample messages
    print("\nPerforming sanity checks on sample inputs:")
    sample_tests = [
        ("URGENT! Your bank account is blocked. Verify your KYC immediately.", 1),
        ("Congratulations! You won a lottery. Pay a fee to claim your prize.", 1),
        ("Your bank account has been credited with 5000 rupees.", 0),
        ("Your monthly electricity bill is due on 20 November.", 0)
    ]
    for text, expected in sample_tests:
        pred = int(pipeline.predict([text])[0])
        proba = float(pipeline.predict_proba([text])[0][1]) * 100
        status = "PASS" if pred == expected else "MISMATCH"
        label_str = "SPAM/FRAUD" if pred == 1 else "HAM/LEGIT"
        print(f"  [{status}] '{text[:42]}...' -> {label_str} (Score: {proba:.1f}%)")


if __name__ == "__main__":
    try:
        dataset = load_and_preprocess_data()
        train_and_evaluate(dataset)
    except Exception as err:
        print(f"\n[ERROR] Pipeline training failed: {err}", file=sys.stderr)
        sys.exit(1)
