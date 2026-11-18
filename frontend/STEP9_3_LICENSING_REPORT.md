# FraudLens AI — Step 9.3: Licence & Attribution Report

**Date:** November 18, 2026  
**Status:** Completed & Verified  
**Scope:** Licence creation, dataset attribution notices, model provenance documentation, and integrity audits.

---

## 1. Executive Summary

In Step 9.3, FraudLens AI finalized its intellectual property, attribution, and licensing framework. A clear, legally rigorous distinction has been established between:
1. **Original Software Engineering:** Fully open-sourced under the permissive standard **MIT License**.
2. **Third-Party Academic Corpora:** Attributed to original authors under academic and Creative Commons licenses (**CC BY 4.0**).
3. **Project-Authored Synthetic Datasets:** Documented and distributed for defensive safety research and academic benchmarking (**CC BY-NC 4.0**).
4. **Machine Learning Model Binaries:** Documented independently with complete training provenance, architecture parameters, synthetic benchmark disclaimers, and defensive usage terms (**CC BY-NC 4.0**).

All model binaries and datasets were preserved with 100% cryptographic integrity. In accordance with strict step guidelines, **Git remains uninitialized**, and no files have been committed, published, or pushed.

---

## 2. Deliverables & Implementations

### A. Root `LICENSE`
- **Location:** [`LICENSE`](file:///c:/Users/admin/OneDrive/Desktop/FraudLens-AI/LICENSE)
- **Framework:** Standard MIT License (OSI-compliant).
- **Copyright Holder:** Copyright (c) 2026 FraudLens AI Contributors.
- **Coverage:** Software implementation files in `backend/`, `frontend/`, tests, and orchestration scripts.

### B. Updated `README.md`
- **Location:** [`README.md`](file:///c:/Users/admin/OneDrive/Desktop/FraudLens-AI/README.md)
- **Section Updated:** `## 📄 Licensing Information`
- **Modifications:** Explicitly clarified that the MIT License applies strictly to original source code and software documentation. Clarified that third-party datasets (UCI SMS Spam Collection), synthetic threat corpora, and compiled model weights (`.joblib` binaries) are governed independently by their respective notices.

### C. Dataset Notice & Academic Attribution (`datasets/NOTICE`)
- **Location:** [`datasets/NOTICE`](file:///c:/Users/admin/OneDrive/Desktop/FraudLens-AI/datasets/NOTICE)
- **Third-Party Academic Dataset Attribution:**
  - **Dataset Title:** SMS Spam Collection
  - **Authors:** Tiago A. Almeida and José María Gómez Hidalgo (2012)
  - **Persistent Identifier (DOI):** [https://doi.org/10.24432/C5CC84](https://doi.org/10.24432/C5CC84)
  - **Licence Reference:** Creative Commons Attribution 4.0 International ([CC BY 4.0](https://creativecommons.org/licenses/by/4.0/))
  - **Project Ownership Disclaimer:** Explicit statement that the dataset is third-party material not owned by FraudLens AI.
- **Project-Authored Synthetic Datasets:**
  - **Corpora:** `datasets/training/indian_sms_train.csv` (400 samples), `datasets/evaluation/indian_sms_final_locked.csv` (300 locked samples), and `datasets/evaluation/indian_sms_eval.csv` (100 validation samples).
  - **Linguistic Coverage:** English, Hindi (Devanagari), and Hinglish (Latin transliteration).
  - **Synthetic Privacy Guarantee:** 100% synthetically authored; zero real personal information (PII), zero real telephone numbers, zero authentic bank accounts.
  - **Licensing:** [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) for defensive security research and academic benchmarking.

### D. Model Provenance & Limitations Documentation (`models/NOTICE.md`)
- **Location:** [`models/NOTICE.md`](file:///c:/Users/admin/OneDrive/Desktop/FraudLens-AI/models/NOTICE.md)
- **Artifacts Documented:**
  - Active model: `models/sms_model.joblib` (SHA-256: `F17D1222624071530CE770540894B1AA9F36FF16DCD3D894DE005A61F2FE701A`).
  - Baseline model: `models/sms_model_baseline.joblib` (SHA-256: `C47360251F4A7C89C21B02D448CBEA6192A1A72D76B06C40ED6497CDB0B91DDA`).
  - Pre-Step 7 immutable backup: `models/sms_model_pre_step7_backup.joblib` (SHA-256: `C47360251F4A7C89C21B02D448CBEA6192A1A72D76B06C40ED6497CDB0B91DDA`).
- **Architecture Specifications:** Complete breakdown of the active Scikit-learn Pipeline (`MultilingualSMSPreprocessor`, `FeatureUnion` combining word $(1,2)$ and character $(3,5)$ TF-IDF with `sublinear_tf=True`, and `LogisticRegression(C=10.0, class_weight=None, max_iter=1000)`).
- **Synthetic Evaluation Disclaimers:** Explicit documentation that the 99.67% accuracy and 100% scam recall were evaluated on a curated 300-sample synthetic test set and do not constitute guaranteed in-the-wild detection accuracy.
- **Independent Model Licensing:** Clarified that binary `.joblib` files are not automatically MIT-licensed; distributed under CC BY-NC 4.0 for non-commercial security research and academic study.

---

## 3. Cryptographic Integrity Audit

All model weights, serialized pipelines, and locked evaluation benchmarks were re-verified against reference checksums:

| File Path | Verified SHA-256 Hash | Reference Match |
|---|---|---|
| `models/sms_model.joblib` | `F17D1222624071530CE770540894B1AA9F36FF16DCD3D894DE005A61F2FE701A` | Matches Config D Frozen Candidate |
| `models/sms_model_baseline.joblib` | `C47360251F4A7C89C21B02D448CBEA6192A1A72D76B06C40ED6497CDB0B91DDA` | Matches Archived Baseline |
| `models/sms_model_pre_step7_backup.joblib` | `C47360251F4A7C89C21B02D448CBEA6192A1A72D76B06C40ED6497CDB0B91DDA` | Matches Pre-Step 7 Backup |
| `datasets/evaluation/indian_sms_final_locked.csv` | `87713F0B44359A58E59E87F5E0AB0BD6CC41B9715CA7101A0812E0B0B56D6905` | Matches Locked Evaluation Reference |

**Audit Result:** 100% integrity preserved. Zero byte corruption or alteration.

---

## 4. Verification & Quality Assurance

- **Backend Unit Tests:** `python -m unittest discover tests` executed:
  - 13 passed, 0 failed, 0 errors (0.048s).
- **Frontend Linter:** `oxlint` executed:
  - 0 warnings, 0 errors across all 6 frontend files.
- **Frontend Production Build:** `npm run build` executed:
  - Client bundle built successfully with Vite in 3.74s (`dist/assets/index-CizflVx3.js`: 284.64 kB).

---

## 5. Repository & Publication Safety Status

Strict constraints confirmed:
- **Git Initialized:** No (`fatal: not a git repository`).
- **Files Staged:** 0.
- **Commits Created:** 0.
- **Remote Configured:** None.
- **Publish / Push Actions:** None taken.

The repository is now fully structured, legally compliant, and ready for initialization and initial commit upon user command.
