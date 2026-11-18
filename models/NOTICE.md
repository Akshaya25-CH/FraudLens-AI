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

All checksums are verified against [`models/model_checksums.json`](model_checksums.json).

---

## 2. Training Data Provenance

The active production model (`models/sms_model.joblib`) was trained on a **Combined Corpus** comprising **5,542 unique messages** (4,709 legitimate, 833 scam) assembled and deduplicated from three distinct sources:

### A. Third-Party Academic Baseline: UCI SMS Spam Collection
- **File Location:** `datasets/SMSSpamCollection`
- **Contribution:** **5,171 unique messages** after deduplication (from 5,574 raw input records; 403 duplicate messages removed).
- **Authors:** Tiago A. Almeida and José María Gómez Hidalgo (2012).
- **Academic Citation:** Almeida, T. A., & Gómez Hidalgo, J. M. (2012). *SMS Spam Collection* [Dataset]. UCI Machine Learning Repository.
- **Persistent Identifier (DOI):** [https://doi.org/10.24432/C5CC84](https://doi.org/10.24432/C5CC84)
- **Licence:** Creative Commons Attribution 4.0 International ([CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)).
- **Role:** Foundational corpus providing baseline English mobile spam and legitimate message distributions.

### B. Supplementary Preserved Domain Corpus
- **File Location:** `datasets/sms_dataset.csv`
- **Contribution:** **19 additional unique messages** after deduplication (from 30 valid rows; 11 overlapping/duplicate records removed).
- **Role:** Preserved supplementary domain-specific samples.

### C. Project-Authored Synthetic Indic Threat Corpus
- **File Location:** `datasets/training/indian_sms_train.csv`
- **Contribution:** **352 unique messages** representing the stratified training partition (88 messages were reserved for the frozen validation split documented in `models/experiments/validation_split.json`).
- **Authorship:** Synthetically authored by the FraudLens AI Project Contributors.
- **Linguistic Distribution:** Multi-script coverage containing English, Hindi (Devanagari script), and Hinglish (Latin-script transliterated colloquial Hindi).
- **Threat Archetypes:** Simulated Indian financial smishing patterns:
  - Electricity bill urgent disconnection threats.
  - Bank account KYC and PAN card suspension warnings.
  - Fake lottery, reward points, and cashback claims.
  - Unauthorized loan disbursement approvals.
  - Deceptive Android Application Package (.APK) download links.
- **Synthetic Privacy Assurance:** Zero real user messages, zero personal identifying information (PII), zero real financial accounts, and zero authentic telephone numbers were utilized in the creation or training of these datasets.
- **Licence:** Creative Commons Attribution-NonCommercial 4.0 International ([CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)).

### D. Learned Features & Multi-Source Vocabulary Distribution
The active model was trained using this combined data, and its learned feature space incorporates vocabulary elements originating from multiple sources:
- **Word TF-IDF Vocabulary:** Contains **55,844 total n-grams** $(1, 2)$. Empirical analysis demonstrates that **49,766 terms (89.12%)** originate from the UCI SMS Spam Collection, while **6,078 terms (10.88%)** are unique to the synthetic Indian training dataset.
- **Character TF-IDF Vocabulary:** Contains **82,778 sub-word character n-grams** $(3, 5)$ capturing morphological and script patterns across English, Hindi, and Hinglish.
- **Classifier Parameters:** The fitted Logistic Regression estimator stores **138,622 regression weights** (`coef_`) mapping 1-to-1 to these multi-source features.

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

## 6. Model Licensing, Attribution & Distribution Status

### A. Separation from Software Code
The **[MIT License](LICENSE)** that governs the project's original source code does **not** automatically govern these trained model binary weights and serialized pipeline artifacts (`.joblib` files). Software code and trained model weights are distinct legal and intellectual property artifacts.

### B. Dual Attribution for Training Provenance
In recognition of the multi-source composition of the training corpus:
1. **UCI SMS Spam Collection Attribution:** Full credit is given to **Tiago A. Almeida and José María Gómez Hidalgo** (2012) for the SMS Spam Collection dataset (DOI: [https://doi.org/10.24432/C5CC84](https://doi.org/10.24432/C5CC84)), governed under the Creative Commons Attribution 4.0 International ([CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)) licence.
2. **Synthetic Indic Corpora Attribution:** The synthetic Indian smishing and legitimate training samples are attributed to the **FraudLens AI Contributors** and maintained separately under the Creative Commons Attribution-NonCommercial 4.0 International ([CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)) licence.

### C. Licensing Status of the Combined Model Artifact
The combined model pipeline contains statistical parameters and vocabulary features derived from both CC BY 4.0 academic data (which permits commercial adaptation) and CC BY-NC 4.0 synthetic data (which restricts commercial use):
- **Derivative Work Status:** International copyright law and machine learning jurisprudence remain unsettled regarding whether trained mathematical weights, TF-IDF statistical parameters, and vocabulary dictionaries constitute an "Adapted Material" (derivative work) of training corpora under copyright law, or whether training constitutes non-expressive transformative use (e.g., Fair Use, EU TDM exceptions, Indian Copyright Act § 52(1)(a)). FraudLens AI makes **no definitive legal claim** that the model is automatically a derivative work.
- **Attribution Scope:** While attribution to Almeida & Hidalgo is provided in full compliance with academic ethics and the spirit of CC BY 4.0, FraudLens AI **does not claim that attribution alone definitively resolves every downstream licensing question**.
- **No Automatic CC BY-NC 4.0 Imposition:** In light of the upstream CC BY 4.0 licence's commercial permissions and prohibition against additional legal restrictions (Section 2(a)(5)(B)), FraudLens AI **does not automatically impose CC BY-NC 4.0 on the combined binary artifact**.
- **Requirement for Legal Review:** The independent redistribution, sublicensing, and commercial licensing status of the combined model weights **requires further professional legal review** prior to any commercial deployment.

### D. Current Permitted Usage
Pending formal legal clarification, the model binary artifacts are provided strictly for **academic study, cyber defensive research, security evaluation, and non-commercial educational benchmarking**. Commercial deployment or incorporation into automated, unmonitored decision-making systems without human review is not endorsed.
