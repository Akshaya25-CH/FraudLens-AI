# FraudLens AI — Step 6A: Independent Locked SMS Test Dataset Report

**Dataset Identifier:** `datasets/evaluation/indian_sms_final_locked.csv`  
**Dataset Release Date:** 2026-11-16  
**Cryptographic Lockdown Hash (SHA-256):** `87713F0B44359A58E59E87F5E0AB0BD6CC41B9715CA7101A0812E0B0B56D6905`  
**Authoring Paradigm:** 100% Synthetic Manually Authored (`source = synthetic_manually_authored`)  
**Evaluation Status:** **LOCKED & UNTOUCHED** (No candidate model, hyperparameter tuner, or training pipeline has been evaluated on this dataset)

---

## 1. Executive Summary

Step 6A establishes the **final, independent, cryptographically locked evaluation benchmark** for FraudLens AI's SMS classification system. 

To overcome historical data contamination, diagnostic dataset exhaustion, and western-centric linguistic bias, this dataset provides a completely fresh test corpus consisting of **300 newly authored synthetic Indian SMS messages**. 

### Key Characteristics:
1. **Strict 50/50 Class Parity**: Exactly 150 scam messages (`label = 1`) and 150 legitimate messages (`label = 0`).
2. **Trilingual Linguistic Representation**:
   - English: 120 messages (40.0% — 60 scam, 60 legitimate)
   - Hinglish: 100 messages (33.3% — 50 scam, 50 legitimate)
   - Hindi (Devanagari): 80 messages (26.7% — 40 scam, 40 legitimate)
3. **Comprehensive Typology Coverage**:
   - 8 Scam Categories (150 messages): Authority impersonation, courier customs extortion, traffic e-Challan summons, electricity cutoff extortion, lottery/cashback scams, KYC/account deactivation threats, part-time job review fraud, and reverse UPI collect mandate fraud.
   - 6 Legitimate Categories (150 messages): Bank transaction debits/credits, two-factor OTP verifications, corporate salary payroll credits, utility/discom bill notifications, logistics package delivery dispatches, and merchant/ride payment receipts.
4. **URL-Balanced Scams**: 78 scams (52.0%) utilize suspicious/phishing URL links (`.test` TLDs), while 72 scams (48.0%) are completely URL-free (relying on social engineering, phone calls, WhatsApp contacts, or UPI collect mandates).
5. **Zero Data Leakage / Complete Independence**: Rigorously verified against all 6,144 historical reference messages (`SMSSpamCollection`, `sms_dataset.csv`, `indian_sms_train.csv`, `indian_sms_eval.csv`). Confirmed **0 exact matches**, **0 normalized matches**, and **maximum character n-gram near-duplicate similarity of 0.4995** (mean 0.3659).

---

## 2. Dataset Composition & Distribution Analysis

### 2.1 Overall Dimensions
- **Total Records:** 300 rows
- **Columns:** `id`, `label`, `category`, `language`, `message`, `source`
- **Missing / Null Values:** 0 across all columns
- **Duplicate Records:** 0 internal duplicates

### 2.2 Class & Language Matrix

| Language | Legitimate (`label = 0`) | Scam (`label = 1`) | Total | Share (%) |
| :--- | :---: | :---: | :---: | :---: |
| **English** | 60 | 60 | 120 | 40.0% |
| **Hinglish** | 50 | 50 | 100 | 33.3% |
| **Hindi (Devanagari)** | 40 | 40 | 80 | 26.7% |
| **Total** | **150** | **150** | **300** | **100.0%** |

### 2.3 Category Distribution

#### Legitimate Categories (`label = 0`, Total = 150)
| Category | English | Hinglish | Hindi (Devanagari) | Total |
| :--- | :---: | :---: | :---: | :---: |
| `bank_alert` | 10 | 8 | 7 | 25 |
| `courier_delivery` | 10 | 8 | 7 | 25 |
| `merchant_receipt` | 10 | 8 | 7 | 25 |
| `otp_2fa` | 10 | 8 | 7 | 25 |
| `salary_payroll` | 10 | 8 | 7 | 25 |
| `utility_bill` | 10 | 8 | 7 | 25 |
| **Subtotal** | **60** | **50** | **40** | **150** |

#### Scam Categories (`label = 1`, Total = 150)
| Category | English | Hinglish | Hindi (Devanagari) | Total | URL-Bearing | URL-Free |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `authority_impersonation` | 8 | 6 | 5 | 19 | 6 | 13 |
| `courier_scam` | 7 | 6 | 5 | 18 | 11 | 7 |
| `echallan_scam` | 7 | 6 | 5 | 18 | 12 | 6 |
| `electricity_threat` | 8 | 6 | 5 | 19 | 9 | 10 |
| `fake_cashback` | 8 | 6 | 5 | 19 | 13 | 6 |
| `fake_kyc` | 7 | 7 | 5 | 19 | 12 | 7 |
| `job_scam` | 8 | 6 | 5 | 19 | 8 | 11 |
| `upi_collect_scam` | 7 | 7 | 5 | 19 | 7 | 12 |
| **Subtotal** | **60** | **50** | **40** | **150** | **78 (52.0%)** | **72 (48.0%)** |

### 2.4 Structural Feature Analysis

- **Scam URL Profile**: 78 / 150 scam messages (52.0%) contain fake phishing domains using RFC-standard non-resolving `.test` top-level domains. 72 / 150 scam messages (48.0%) do NOT contain any URLs, preventing models from relying on simple regex or URL tokens as a classification heuristic shortcut.
- **Legitimate Security Features**: Legitimate messages incorporate authentic Indian banking patterns:
  - Masked account indicators (`XX4910`, `XX8192`, `A/C 908123`).
  - Standard toll-free numbers (`1800 11 2211`, `1800 2008`, `1860 123 4567`).
  - Strict security advisories (`Never share your OTP or password`, `Bank kabhi bhi aapse phone par OTP nahi mangta`).
  - Real corporate and municipal entities (TCS, Infosys, Wipro, L&T, AIIMS, DRDO, Tata Motors, BESCOM, MGL, IGL, UPPCL, Zepto, Dunzo, BigBasket, BookMyShow, Wave Cinemas).

---

## 3. Independence & Data Leakage Audit

To guarantee that the final evaluation score is completely uncompromised, the 300 test messages underwent exhaustive duplicate, near-duplicate, and template-leakage audits against all **6,144 reference messages** currently existing in the repository:
1. `datasets/SMSSpamCollection` (UCI SMS Spam Collection, 5,574 messages)
2. `datasets/sms_dataset.csv` (Supplemental SMS dataset, 30 messages)
3. `datasets/training/indian_sms_train.csv` (Indian SMS Training Dataset, 440 messages)
4. `datasets/evaluation/indian_sms_eval.csv` (Diagnostic Indian SMS Evaluation Benchmark, 100 messages)

### 3.1 Exact Duplicate Audit
Each of the 300 test messages was compared verbatim against every reference message.
- **Exact Duplicates Found:** **0**
- **Exact Match Rate:** **0.00%**

### 3.2 Normalized Duplicate Audit
Each message was normalized using Unicode NFC decomposition, lowercased, stripped of all punctuation/symbols, and whitespace-collapsed.
- **Normalized Duplicates Found:** **0**
- **Normalized Match Rate:** **0.00%**

### 3.3 Category-Agnostic Near-Duplicate Cosine Similarity
To catch paraphrased templates or sentence-structure copies, a high-dimensional character n-gram TF-IDF vectorizer (`analyzer='char_wb'`, `ngram_range=(3, 5)`) was fitted across the entire 6,144 reference corpus and used to transform all 300 test messages.

| Metric | Score across 300 Test Messages |
| :--- | :---: |
| **Minimum Maximum-Similarity** | 0.1931 |
| **Mean Maximum-Similarity** | 0.3659 |
| **Median Maximum-Similarity** | 0.3689 |
| **90th Percentile** | 0.4500 |
| **95th Percentile** | 0.4763 |
| **Absolute Maximum Similarity** | **0.4995** |
| **Messages with Similarity $\ge 0.50$** | **0 (0.00%)** |

#### Similarity Distribution Breakdown:
- **[0.00, 0.20):** 1 message (0.3%)
- **[0.20, 0.30):** 59 messages (19.7%)
- **[0.30, 0.40):** 132 messages (44.0%)
- **[0.40, 0.50):** 108 messages (36.0%)
- **[0.50, 1.00]:** **0 messages (0.0%)**

### 3.4 Top 5 Near-Duplicate Matches Analysis
Even among the highest-similarity pairs (which all remain strictly below 0.50), structural inspection demonstrates that similarities arise from generic domain syntax (such as banking balance statements or Aadhaar disclaimers) rather than shared templates:

1. **Similarity: 0.4995**
   - *Test ID 213 (salary_payroll, Hinglish):* `ICICI Bank: Wipro se Rs 52,000 salary account XX9012 me jama hui hai. Net available balance: Rs 59,800.`
   - *Reference (indian_sms_train.csv, row 316):* `Axis Bank: Rs 48,000 monthly salary Wipro se aapke account XX4821 me jama ho gayi hai. Total balance: Rs 59,400.`
   - *Distinction:* Different banking institution, different account identifier, different financial sum, and altered sentence construction.
2. **Similarity: 0.4972**
   - *Test ID 105 (echallan_scam, Hinglish):* `Delhi Traffic alert: Gadi HR26DK3910 par signal jumping ka challan generate hua hai. Challan photo dekhne aur bhugtan karne ke liye visit kare https://delhi-traffic-notice.test`
   - *Reference (indian_sms_train.csv, row 127):* `Traffic department: Aapki car RJ45CE1029 ka CCTV photo challan generate hua hai. Proof dekhne aur fine bharne ke liye link https://traffic-fine-notice.test par jaye.`
   - *Distinction:* Different jurisdiction, vehicle registration plate, violation type, URL endpoint, and imperative phrasing.
3. **Similarity: 0.4940**
   - *Test ID 185 (otp_2fa, English):* `UIDAI Aadhaar OTP: 739102 is your OTP for e-Aadhaar download. Valid for 10 minutes. Sharing OTP can lead to identity misuse.`
   - *Reference (indian_sms_eval.csv, row 61):* `Your Aadhaar OTP for EPFO authentication is 482019. Do not disclose this OTP to any person. Valid for 10 minutes. - UIDAI`
   - *Distinction:* Distinct purpose (e-Aadhaar download vs. EPFO auth), OTP code, and security warning phrasing.
4. **Similarity: 0.4929**
   - *Test ID 165 (bank_alert, Hinglish):* `Axis Bank: Rs 12,000.00 aapke khate XX6019 me NEFT se credit ho gaya hai. Total balance: Rs 58,400.00.`
   - *Reference (indian_sms_train.csv, row 237):* `HDFC Bank: Rs 2,500.00 aapke khate XX8192 me NEFT dwara transfer ho gaya hai. Kul uplabdh balance: Rs 45,800.00.`
   - *Distinction:* Distinct banking institution, transaction value, account identifier, and phrasing.
5. **Similarity: 0.4917**
   - *Test ID 40 (electricity_threat, English):* `BESCOM Alert: Your electric meter connection is scheduled for cutoff today. To avoid disconnection and reconnection penalty, pay at https://bescom-bill-online.test`
   - *Reference (indian_sms_train.csv, row 68):* `BESCOM alert: Aapka meter connection aaj sham 8 baje disconnect ho jayega. Disconnection rokne ke liye bijli officer number 9845112233 par turant contact kare.`
   - *Distinction:* Distinct language (English vs. Hinglish), resolution action (online link payment vs. lineman telephone extortion), and sentence cadence.

---

## 4. Internal Diversity & Semantic Orthogonality

An internal similarity matrix computed across all 300 test messages verifies high diversity within the test set itself:
- **Internal Mean Similarity:** 0.3180
- **Internal Median Similarity:** 0.3122
- **Internal Maximum Similarity:** 0.5483

The highest internal similarities occur naturally between semantically related financial categories:
- `bank_alert` (ID 170) vs `salary_payroll` (ID 220) at 0.5483 (both Devanagari Punjab National Bank credit notifications).
- `bank_alert` (ID 172) vs `salary_payroll` (ID 222) at 0.5021 (both Devanagari HDFC Bank transaction updates).

No scam messages or legitimate messages share identical boilerplates, ensuring that a classifier cannot achieve high test performance by memorizing a few repeated sentence frames.

---

## 5. Cryptographic Locking & Asset Verification

To prevent accidental modification, silent overwriting, or premature evaluation, all evaluation and model assets have their SHA-256 cryptographic hashes verified and locked:

| Asset Path | Asset Role | Status | SHA-256 Checksum |
| :--- | :--- | :---: | :--- |
| `datasets/evaluation/indian_sms_final_locked.csv` | **New Locked Final Test Set** | **CREATED & LOCKED** | `87713F0B44359A58E59E87F5E0AB0BD6CC41B9715CA7101A0812E0B0B56D6905` |
| `models/sms_model.joblib` | Production Baseline Model | UNTOUCHED | `C47360251F4A7C89C21B02D448CBEA6192A1A72D76B06C40ED6497CDB0B91DDA` |
| `models/sms_model_baseline.joblib` | Archived Baseline Model | UNTOUCHED | `C47360251F4A7C89C21B02D448CBEA6192A1A72D76B06C40ED6497CDB0B91DDA` |
| `datasets/training/indian_sms_train.csv` | Training Corpus (440 samples) | UNTOUCHED | `737DF7C9C3D3525F079A08775E0C093389BE72D4B77460F63DB65A39EAD8DBF8` |
| `datasets/evaluation/indian_sms_eval.csv` | Diagnostic Eval (100 samples) | UNTOUCHED | `BA0A9AA4D9B336B1473C8C26F6A23EF2981D44C273986340F23FAFEA0DBCE1C6` |
| `datasets/SMSSpamCollection` | Legacy UCI Corpus (5,574 samples)| UNTOUCHED | `7D039A24A6083ED9EF0F806EBAD56BBB976E3AEB8DE05669173BFDC4996C239D` |
| `datasets/sms_dataset.csv` | Supplemental Corpus (30 samples) | UNTOUCHED | `776F656F59F48EE6BCDF5EAD08B6E8B024B041014F0AB7CE5F99695C684F1256` |

---

## 6. Strict Preservation & Next Steps Protocol

In accordance with strict evaluation integrity principles:
1. **Zero Retraining**: No model was retrained during Step 6A.
2. **Zero Evaluation**: Neither the baseline model (`sms_model.joblib`) nor any candidate models from Step 5B (`Multilingual-Only Candidate 1`, `Combined Candidate 2`) have been run against `datasets/evaluation/indian_sms_final_locked.csv`.
3. **No Hyperparameter Tuning**: Hyperparameters remain frozen.
4. **Readiness for Step 6B**: The locked dataset is ready for an unbiased, independent evaluation run in Step 6B to determine final generalization metrics (Precision, Recall, F1, Latency, and False Positive Rate on Indian SMS).
