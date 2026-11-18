# FraudLens AI — Model Artifacts Provenance, Limitations & Licensing Notice

This notice provides complete documentation of the machine learning model artifacts included in the `models/` directory, detailing their training provenance, mathematical architecture, operational limitations, and independent licensing framework.

---

## 1. Model Artifact Inventory

| Model Artifact | File Path | SHA-256 Checksum | Status |
|---|---|---|---|
| **Active Production Pipeline** | `models/sms_model.joblib` | `F17D1222624071530CE770540894B1AA9F36FF16DCD3D894DE005A61F2FE701A` | Production Active (Config D) |
| **Archived Baseline Model** | `models/sms_model_baseline.joblib` | `C47360251F4A7C89C21B02D448CBEA6192A1A72D76B06C40ED6497CDB0B91DDA` | Frozen Baseline |
| **Pre-Step 7 Backup** | `models/sms_model_pre_step7_backup.joblib` | `C47360251F4A7C89C21B02D448CBEA6192A1A72D76B06C40ED6497CDB0B91DDA` | Immutable Backup |
| **Rank-1 Candidate Source** | `models/experiments/config_d_c10.0_unweighted.joblib` | `F17D1222624071530CE770540894B1AA9F36FF16DCD3D894DE005A61F2FE701A` | Validation Candidate |

All checksums are verified against [`models/model_checksums.json`](file:///c:/Users/admin/OneDrive/Desktop/FraudLens-AI/models/model_checksums.json).

---

## 2. Training Data Provenance

The active model (`models/sms_model.joblib`) was trained on:
- **Primary Training Corpus:** `datasets/training/indian_sms_train.csv` consisting of 400 balanced, synthetically authored messages (200 legitimate, 200 scam).
- **Linguistic Distribution:** Multi-script coverage containing English, Hindi (Devanagari script), and Hinglish (Latin-script transliterated Hindi).
- **Threat Archetypes:** Synthetic simulations of prevalent Indian financial smishing attack surfaces:
  - Electricity bill urgent disconnection threats.
  - Bank account KYC and PAN card suspension warnings.
  - Fake lottery, reward points, and cashback claims.
  - Unauthorized loan disbursement approvals.
  - Deceptive Android Application Package (.APK) download links.
- **Privacy Assurance:** Zero real user messages, zero personal identifying information (PII), zero real financial accounts, and zero authentic telephone numbers were utilized in the creation or training of these models.

---

## 3. Architecture Specification

The active classifier is serialized as a Scikit-learn Pipeline comprising:
1. **Multilingual SMS Preprocessor:** Custom transformer (`backend.sms_preprocessor.MultilingualSMSPreprocessor`) performing URL tokenization (`[URL]`), phone masking (`[PHONE]`), currency standardisation (`[CURRENCY]`), number masking (`[NUM]`), and script-aware normalization.
2. **Feature Extraction (`FeatureUnion`):**
   - **Word TF-IDF:** `ngram_range=(1, 2)`, `sublinear_tf=True`, max features unconstrained.
   - **Character TF-IDF:** `analyzer='char_wb'`, `ngram_range=(3, 5)`, `sublinear_tf=True`, capturing sub-word morphological patterns across transliterated Indic text.
3. **Classification Estimator:**
   - `LogisticRegression(C=10.0, class_weight=None, max_iter=1000, random_state=42)`

---

## 4. Evaluation Metrics & Strict Scope Disclaimer

- **Evaluation Benchmark:** Evaluated against `datasets/evaluation/indian_sms_final_locked.csv` (300 locked synthetic messages: 150 legitimate, 150 scam).
- **Benchmark Results:**
  - Accuracy: 99.67% (299/300 correct classifications)
  - Scam Recall: 100.00% (150/150 scam messages detected)
  - Legitimate Specificity: 99.33% (149/150 legitimate messages preserved; 1 false positive)
  - F1-Score: 0.9967
- **Important Qualification:**
  > **These metrics were measured strictly on a curated, synthetic 300-sample benchmark.**  
  > **They do NOT represent guaranteed or proven real-world accuracy.** Real-world smishing campaigns continuously evolve with polymorphic phrasings, homoglyph character substitutions, and novel social engineering pretexts not represented in static evaluation benchmarks.

---

## 5. Operational Limitations

1. **Static Weights:** The models do not adapt or learn online from user scans. New threat vectors require deliberate retraining and validation.
2. **Adversarial Robustness:** Highly obfuscated inputs (such as zero-width Unicode characters or radical homoglyphs) may bypass lexical feature union extractors.
3. **Probabilistic Scoring:** Risk scores represent statistical probabilities rather than definitive determinations of legality or maliciousness.
4. **Offline Heuristics Boundary:** URL and UPI scanning modules in FraudLens AI do **not** use this model; they operate on independent rule-based heuristic engines.

---

## 6. Model Licensing & Distribution Terms

- **Separation from Software Code:** The MIT License that governs the project's source code does **not** automatically extend to these trained model weights and serialized binary artifacts (`.joblib` files).
- **Model Distribution Framework:** The model binary artifacts are provided under the terms of the [Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)](https://creativecommons.org/licenses/by-nc/4.0/) license for academic study, cyber defensive research, and personal evaluation.
- **Commercial Use:** Commercial redistribution, sublicensing, or integration into automated, unmonitored decision-making systems without human review is strictly prohibited.
