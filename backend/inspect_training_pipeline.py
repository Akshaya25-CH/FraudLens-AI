import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import joblib
import pandas as pd
import numpy as np

MODEL_PATH = PROJECT_ROOT / "models" / "sms_model.joblib"
PRIMARY_DATA_PATH = PROJECT_ROOT / "datasets" / "SMSSpamCollection"
SUPP_DATA_PATH = PROJECT_ROOT / "datasets" / "sms_dataset.csv"

def inspect_pipeline():
    print("=" * 70)
    print("FRAUDLENS AI - SMS TRAINING PIPELINE & VOCABULARY AUDIT")
    print("=" * 70)

    # 1. Inspect Saved Model Pipeline
    print("\n--- 1. Pipeline Architecture ---")
    if not MODEL_PATH.exists():
        print(f"Model file not found: {MODEL_PATH}")
        return

    model = joblib.load(MODEL_PATH)
    print("Pipeline Components:", model.named_steps)

    tfidf = model.named_steps["tfidf"]
    clf = model.named_steps["classifier"]

    print("\nTF-IDF Configuration:")
    print("  lowercase:       ", tfidf.lowercase)
    print("  ngram_range:     ", tfidf.ngram_range)
    print("  sublinear_tf:    ", tfidf.sublinear_tf)
    print("  token_pattern:   ", tfidf.token_pattern)
    print("  stop_words:      ", tfidf.stop_words)
    print("  min_df:          ", tfidf.min_df)
    print("  max_df:          ", tfidf.max_df)
    print("  Total Features:  ", len(tfidf.vocabulary_))

    print("\nLogistic Regression Configuration:")
    print("  C (inv reg):     ", clf.C)
    print("  penalty:         ", clf.penalty)
    print("  solver:          ", clf.solver)
    print("  max_iter:        ", clf.max_iter)
    print("  class_weight:    ", clf.class_weight)
    print("  classes_:        ", clf.classes_)

    # 2. Vocabulary Inspection: Devanagari & Hinglish Presence
    print("\n--- 2. Vocabulary Representation Analysis ---")
    vocab = tfidf.vocabulary_
    
    # Check Devanagari characters in vocabulary
    devanagari_tokens = [w for w in vocab.keys() if any('\u0900' <= char <= '\u097F' for char in w)]
    print(f"Devanagari Hindi tokens in vocabulary: {len(devanagari_tokens)}")
    if devanagari_tokens:
        print("  Sample Devanagari tokens:", devanagari_tokens[:10])

    # Check common Hinglish tokens in vocabulary
    hinglish_test_words = [
        "aapka", "karo", "kare", "turant", "khata", "paise", "bijli", "bheje", "bhejo",
        "rupaye", "badhai", "inam", "jeeta", "adhikari", "sampark", "band", "khate"
    ]
    present_hinglish = [w for w in hinglish_test_words if w in vocab]
    print(f"Hinglish probe tokens found in vocabulary: {len(present_hinglish)} / {len(hinglish_test_words)}")
    print(f"  Present: {present_hinglish}")
    print(f"  Missing: {[w for w in hinglish_test_words if w not in vocab]}")

    # 3. Training Data Composition
    print("\n--- 3. Training Data Composition & Class Balance ---")
    if PRIMARY_DATA_PATH.exists():
        df_pri = pd.read_csv(PRIMARY_DATA_PATH, sep="\t", header=None, names=["label", "text"])
        print(f"Primary Dataset ({PRIMARY_DATA_PATH.name}): {len(df_pri)} raw rows")
        print("  Class counts:\n", df_pri["label"].value_counts().to_dict())

    if SUPP_DATA_PATH.exists():
        df_sup = pd.read_csv(SUPP_DATA_PATH)
        print(f"Supplementary Dataset ({SUPP_DATA_PATH.name}): {len(df_sup)} raw rows")
        print("  Class counts:\n", df_sup["label"].value_counts().to_dict())

    # 4. Feature Extraction Test on Different Language Modalities
    print("\n--- 4. Feature Representation Test (Non-zero TF-IDF entries) ---")
    test_cases = [
        ("English Spam", "URGENT! Your bank account is blocked. Verify KYC immediately at http://sbi.vip"),
        ("Hinglish Spam", "Aapka SBI account block ho gaya hai. Turant link pe click karke KYC verify kare."),
        ("Devanagari Spam", "प्रिय ग्राहक, आपका बैंक खाता ब्लॉक कर दिया गया है। तुरंत लिंक पर क्लिक करें।"),
        ("English Legit OTP", "Your OTP for login to SBI Card is 849201. Valid for 5 minutes. NEVER share your OTP.")
    ]

    for label, text in test_cases:
        vec = tfidf.transform([text])
        non_zeros = vec.nnz
        matched_features = [tfidf.get_feature_names_out()[i] for i in vec.indices]
        proba = model.predict_proba([text])[0][1] * 100
        pred = model.predict([text])[0]
        print(f"\n[{label}]")
        print(f"  Input: {text}")
        print(f"  Non-zero features matched: {non_zeros} / {len(text.split())} words")
        print(f"  Sample matched tokens: {matched_features[:8]}")
        print(f"  Prediction: {pred} | Scam Probability: {proba:.2f}%")

    # 5. Top Positive & Negative Model Weights
    print("\n--- 5. Top Logistic Regression Feature Weights ---")
    feature_names = tfidf.get_feature_names_out()
    coefs = clf.coef_[0]
    
    top_spam_indices = np.argsort(coefs)[-15:][::-1]
    top_ham_indices = np.argsort(coefs)[:15]

    print("\nTop 15 SPAM Predictive Features (Positive weights):")
    for idx in top_spam_indices:
        print(f"  {feature_names[idx]:<20}: +{coefs[idx]:.4f}")

    print("\nTop 15 HAM Predictive Features (Negative weights):")
    for idx in top_ham_indices:
        print(f"  {feature_names[idx]:<20}: {coefs[idx]:.4f}")

    print("\n" + "=" * 70)

if __name__ == "__main__":
    inspect_pipeline()
