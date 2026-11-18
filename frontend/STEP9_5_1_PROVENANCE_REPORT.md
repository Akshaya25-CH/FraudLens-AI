# FraudLens AI — Step 9.5.1: Licensing & Provenance Clarification Report

**Date:** November 18, 2026  
**Audited Commit:** `118179c` (`Initial commit: FraudLens AI scam detection platform`)  
**Branch:** `main`  
**Investigation Scope:** Targeted, strictly read-only reconstruction of training provenance, dataset deduplication reconciliation, model component analysis, CC BY 4.0 / CC BY-NC 4.0 legal review, and repository status.

---

## 1. Reconstruction of Exact Training Data Provenance

An empirical trace of the active production model pipeline (`models/sms_model.joblib`, Config D, $C=10.0$, unweighted) was conducted by tracing `backend/run_experiments_step5b.py` (lines 244–290 and 565–580) and `models/experiments/validation_split.json`.

The active model was fitted on a **Combined Corpus** assembled from three separate input sources:
1. **Academic Baseline Dataset:** `datasets/SMSSpamCollection` (UCI SMS Spam Collection, Almeida & Hidalgo, 2012).
2. **Supplementary Historical Dataset:** `datasets/sms_dataset.csv` (Preserved domain-specific samples).
3. **Project-Authored Synthetic Training Partition:** `datasets/training/indian_sms_train.csv` (Stratified train split of 352 samples, excluding the 88 validation samples).

The training pipeline ingested these three sources, standardized label mappings (`ham -> 0`, `spam -> 1`), stripped whitespace, applied string deduplication, and fitted the scikit-learn `Pipeline([('preprocessor', MultilingualSMSPreprocessor()), ('features', FeatureUnion([...])), ('classifier', LogisticRegression(C=10.0))])`.

---

## 2. Precise Source Files & Row Counts Before and After Deduplication

The exact counts at each stage of dataset assembly are summarized below:

| Source File | Raw Rows | Valid Rows Loaded | Internal Duplicates Removed | Net Unique Rows Contributed |
|---|---|---|---|---|
| `datasets/SMSSpamCollection` | 5,574 | 5,574 | 403 | **5,171** |
| `datasets/sms_dataset.csv` | 30 | 30 | 11 (duplicates/overlaps) | **19** |
| *Subtotal: Legacy Combined* | *5,604* | *5,604* | *414* | ***5,190*** |
| `datasets/training/indian_sms_train.csv` (Train split) | 352 (of 440 total) | 352 | 0 | **352** |
| **Combined Final Training Corpus** | **5,956** | **5,956** | **414** | **5,542** |

### Label Breakdown of the Final 5,542 Training Samples:
- **Class 0 (Legitimate / Ham):** **4,709 samples** (85.0%)
- **Class 1 (Scam / Spam):** **833 samples** (15.0%)
- **Imbalance Ratio:** ~5.65 : 1

---

## 3. Reconciliation: 5,542 vs. (5,574 + 352 + ~30)

The apparent numerical discrepancy identified during the Step 9.5 audit is completely resolved by distinguishing **gross input lines** from **net deduplicated training samples**:

1. **Gross Input Lines (Before Deduplication):**
   $$\text{Gross Total} = 5,574 \text{ (UCI)} + 30 \text{ (Supplementary)} + 352 \text{ (Indian Train Split)} = \mathbf{5,956 \text{ raw samples}}$$
2. **Deduplication Mechanics in Code:**
   In `backend/run_experiments_step5b.py`:
   - `df_legacy = pd.concat([df_uci, df_supp], ignore_index=True)` loads 5,604 records.
   - `df_legacy = df_legacy.drop_duplicates(subset=["message"])` eliminates 414 duplicate or repeated messages (primarily popular spam and greeting messages inside the UCI corpus, plus overlaps with `sms_dataset.csv`), leaving **5,190 unique legacy records**.
   - `df_combined = pd.concat([df_legacy, df_indian_train], ignore_index=True)` concatenates the 5,190 legacy records with the 352 unique Indian training records ($5,190 + 352 = 5,542$).
   - A final `df_combined = df_combined.drop_duplicates(subset=["message"])` is executed. Because the synthetically authored Indian messages have zero text overlap with the legacy corpus, exactly **5,542 unique records** remain.
3. **Conclusion:**
   The figure **5,542 samples** reported in `STEP5B_EXPERIMENT_REPORT.md` is the exact, empirically verified size of the training dataset used to train `models/sms_model.joblib`. The gross total of 5,956 represents un-deduplicated raw file rows.

---

## 4. Verification of `datasets/SMSSpamCollection`

An integrity check was performed on `datasets/SMSSpamCollection`:
- **File Size:** 477,907 bytes.
- **SHA-256 Checksum:** `7d039a24a6083ed9ef0f806ebad56bbb976e3aeb8de05669173bfdc4996c239d`
- **Line Count:** Exactly 5,574 lines.
- **Line Endings:** UNIX LF-only (`\n`), matching the canonical archive.
- **Content Inspection:** First line begins `'ham\tGo until jurong point, crazy..'`; line 5574 ends `'ham\tRofl. Its true to its name'`.
- **Verdict:** `datasets/SMSSpamCollection` is an **unmodified, bit-exact copy** of the original canonical UCI SMS Spam Collection created by Tiago A. Almeida and José María Gómez Hidalgo (2012). No synthetic samples, headers, or text modifications have been introduced into this file.

---

## 5. Model Architecture & Vocabulary Derivation Analysis

### A. Learned Feature Components in `models/sms_model.joblib`
Inspection of the serialized model binary via Python reflection reveals:
1. **Pipeline Components:**
   - `preprocessor`: Multilingual text normalization rules and regular expressions.
   - `features`: `FeatureUnion` combining:
     - `word` (`TfidfVectorizer`): Contains a learned vocabulary dictionary mapping **55,844 word n-gram strings** $(1, 2)$ to feature indices, plus a learned `idf_` weight vector.
     - `char` (`TfidfVectorizer`): Contains a learned vocabulary dictionary mapping **82,778 character n-gram strings** $(3, 5)$ to feature indices, plus a learned `idf_` weight vector.
   - `classifier` (`LogisticRegression`): Contains an intercept (`[-4.0298]`) and a weight matrix `coef_` of shape `(1, 138622)` containing learned float64 regression parameters for every vocabulary feature.

### B. Empirical Vocabulary Origin:
- Out of 55,844 word n-grams in the active model's vocabulary:
  - **49,766 terms (89.12%)** originate from the UCI SMS Spam Collection.
  - **6,078 terms (10.88%)** are unique to the project's synthetic Indian dataset.
- The model binary physically embeds tens of thousands of literal string tokens from the UCI corpus in its pickled Python dictionary.

### C. Does This Alone Establish That the Model is a "Derivative Work"?
**No definitive consensus exists under international copyright law.** The legal status of trained machine learning model weights remains an active, jurisdiction-dependent legal debate:

1. **Arguments That Weights Are NOT a Derivative Work:**
   - Under US copyright doctrine (17 U.S.C. § 101, *Feist Publications*), individual words, short phrases, and statistical facts (word frequencies, TF-IDF weights, logistic regression coefficients) are non-copyrightable.
   - Algorithmic training is transformative use (fair use in the US, Text and Data Mining exceptions under EU DSM Directive Arts. 3–4, and fair dealing under Indian Copyright Act § 52(1)(a)). The model does not memorize or reproduce substantial expressive portions of individual SMS messages.
2. **Arguments That Weights MAY Constitute "Adapted Material" (under Creative Commons):**
   - Section 1(a) of the CC BY 4.0 licence defines "Adapted Material" broadly as material derived from or based upon the licensed material in which the licensed material is "translated, altered, arranged, transformed, or otherwise modified in a manner requiring permission under Copyright and Similar Rights".
   - Because the serialized `joblib` binary stores literal string keys in its `vocabulary_` dictionary directly extracted from the training texts, some legal commentators argue that pickled vectorizer dictionaries embody a transformation of the dataset requiring attribution.
3. **Prudent Finding:**
   While the presence of vocabulary tokens and statistical weights demonstrates clear **factual and functional derivation**, whether it legally constitutes an "Adapted Material" / "Derivative Work" under copyright law cannot be asserted as a settled legal certainty without formal legal advice. Nonetheless, providing complete attribution satisfies the most conservative interpretation of CC BY 4.0 and completely eliminates infringement risk.

---

## 6. Review of Attribution Obligations (CC BY 4.0 vs. CC BY-NC 4.0)

### A. UCI SMS Spam Collection (CC BY 4.0)
Under Section 3(a) of the CC BY 4.0 licence, if the dataset or an adaptation of it is distributed, the licensee must:
1. Retain identification of the creators: **Tiago A. Almeida and José María Gómez Hidalgo**.
2. Retain copyright notices and attribution statements.
3. Provide a URI or hyperlink to the dataset: [https://doi.org/10.24432/C5CC84](https://doi.org/10.24432/C5CC84).
4. Provide a notice referring to CC BY 4.0 and a link to the licence: [https://creativecommons.org/licenses/by/4.0/](https://creativecommons.org/licenses/by/4.0/).
5. Indicate that changes were made (e.g., deduplication and combination with synthetic Indic data for training).
6. **Crucial Term (Section 2(a)(5)(B)):** The distributor may not apply additional legal terms or technological measures that legally restrict others from doing anything the upstream licence permits (which includes commercial reuse).

### B. Project-Authored Synthetic Datasets (CC BY-NC 4.0)
- The synthetic Indian datasets (`indian_sms_train.csv`, `indian_sms_final_locked.csv`, `indian_sms_eval.csv`) were 100% authored by the FraudLens AI project contributors.
- As sole authors of these synthetic corpora, the project contributors have the legal right to designate CC BY-NC 4.0 (Non-Commercial) for their own datasets.

---

## 7. Identification of Licensing Uncertainties Requiring Professional Legal Advice

The following three legal questions involve unsettled doctrine at the intersection of open-source software, machine learning model weights, and open data licensing:

1. **Composite Model Licensing Compatibility:**
   - *Question:* Does distributing `models/sms_model.joblib` under CC BY-NC 4.0 create a licensing conflict with the upstream CC BY 4.0 licence, given that 89.1% of its vocabulary and 93.8% of its training inputs originate from a commercially permissive CC BY 4.0 dataset?
   - *Consideration:* If model weights are deemed "Adapted Material", CC BY 4.0 Section 2(a)(5)(B) prohibits imposing downstream non-commercial restrictions that restrict commercial rights granted by the upstream licensor. If weights are not deemed a derivative work, the project can license them under any terms, but cannot restrict third parties from extracting non-copyrightable statistical weights.
2. **Copyrightability of Pickled Scikit-Learn Pipelines:**
   - *Question:* In a jurisdiction such as India, the United States, or the European Union, does a serialized binary containing `vocabulary_` dictionaries and floating-point coefficients enjoy independent copyright protection, or is it an uncopyrightable functional mathematical artifact?
3. **End-User Operational Use vs. Redistribution:**
   - *Question:* Does a commercial business running FraudLens AI locally to protect its employees from incoming smishing scams violate the CC BY-NC 4.0 restriction on the model weights, or is that permitted under the MIT license governing the software execution?

> **Recommendation:** If FraudLens AI is commercialized, integrated into enterprise threat feeds, or redistributed in commercial products, professional legal advice from an intellectual property attorney specialized in AI licensing should be obtained. For non-commercial, academic, and open-source demonstration purposes on GitHub, explicit dual-attribution and clear provenance disclosure provide practical defensive protection.

---

## 8. Review of `models/NOTICE.md`

- **Current Text in `models/NOTICE.md` (Section 2):**
  > *"The active model (models/sms_model.joblib) was trained on: Primary Training Corpus: datasets/training/indian_sms_train.csv consisting of 400 balanced, synthetically authored messages (200 legitimate, 200 scam)."*
- **Audit Finding:** **Inaccurate and Incomplete.**
- **Details:** This description omits the 5,171 deduplicated UCI messages that constituted the majority of the training set. It also references 400 samples instead of the exact 352 samples utilized in the training split (with 88 reserved for validation).
- **Correction Required:** `models/NOTICE.md` must be updated to accurately describe the Combined Corpus (5,542 unique samples: 5,171 UCI, 19 supplementary, 352 Indian synthetic) and include full CC BY 4.0 attribution to Almeida & Hidalgo.

---

## 9. Current Git Working Tree Status

Execution of `git status --short`:

```
?? frontend/STEP9_4_GIT_INITIALIZATION_REPORT.md
?? frontend/STEP9_5_PRE_PUBLICATION_AUDIT.md
```

- **Status:**
  - `frontend/STEP9_4_GIT_INITIALIZATION_REPORT.md`: **Untracked (`??`)**
  - `frontend/STEP9_5_PRE_PUBLICATION_AUDIT.md`: **Untracked (`??`)**
  - Tracked project files: **0 modified, 0 staged, 0 deleted**. Working tree clean with respect to tracked files.

---

## 10. Confirmation of Commit and Remote Status

- **Current Commit:** `118179c` (`Initial commit: FraudLens AI scam detection platform`)
- **Active Branch:** `main`
- **Configured Remotes:** `git remote -v` returned **empty** (0 remotes configured).
- **Publication Status:** Zero repositories created; zero pushes or external communications executed.
