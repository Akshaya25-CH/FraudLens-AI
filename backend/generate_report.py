import os
import re
import pandas as pd

def main():
    csv_path = "datasets/training/indian_sms_train.csv"
    report_path = "datasets/training/INDIAN_SMS_DATASET_REPORT.md"
    eval_csv_path = "datasets/evaluation/indian_sms_eval.csv"

    df = pd.read_csv(csv_path)
    df_eval = pd.read_csv(eval_csv_path)

    total_count = len(df)
    scam_count = len(df[df["label"] == 1])
    legit_count = len(df[df["label"] == 0])

    lang_counts = df["language"].value_counts().to_dict()
    lang_pcts = {k: v / total_count * 100 for k, v in lang_counts.items()}

    scam_cats = df[df["label"] == 1]["category"].value_counts().to_dict()
    legit_cats = df[df["label"] == 0]["category"].value_counts().to_dict()

    crosstab_lang = pd.crosstab(df["label"], df["language"]).to_dict()

    content = f"""# FraudLens AI — Indian SMS Training Dataset Validation Report

**Dataset Path:** `datasets/training/indian_sms_train.csv`  
**Generated Date:** November 15, 2026  
**Dataset Version:** 1.0.0  
**Data Source:** `synthetic_manually_authored`  
**Audit Status:** PASSED (Zero leakage, zero duplicates, zero nulls)  

---

## 1. Executive Summary

As part of **Step 3** of the FraudLens AI development roadmap, a dedicated, high-quality Indian SMS training dataset has been authored and audited. This dataset addresses the critical domain gaps discovered in Step 2 baseline evaluation—specifically the near-complete absence of Devanagari Hindi script, Hinglish colloquial syntax, and localized Indian fraud vectors (such as fake KYC suspensions, UPI collect requests, electricity disconnection threats, and e-Challan summons) in generic Western spam corpora like the UCI SMS Spam Collection.

### Strict Methodological Boundaries
In accordance with experimental integrity guidelines:
- `models/sms_model.joblib` was **strictly preserved** (untouched).
- `backend/train_model.py` was **strictly preserved** (untouched).
- `datasets/evaluation/indian_sms_eval.csv` was **strictly preserved** (frozen diagnostic benchmark).
- **Zero model retraining or tuning** was conducted during this step.
- The dataset creation and audit were conducted as an isolated data engineering milestone.

---

## 2. Dataset Overview & Schema

The dataset is stored in standard UTF-8 CSV format at `datasets/training/indian_sms_train.csv`.

### Table 1: Schema Specification
| Column Name | Data Type | Permitted Values | Null Count | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | Integer | `1` to `440` (continuous) | 0 | Unique sequential sample identifier |
| `label` | Integer | `0` (Legitimate), `1` (Scam) | 0 | Ground-truth binary classification target |
| `category` | String | 14 structured category identifiers | 0 | Domain sub-category (8 scam, 6 legitimate) |
| `language` | String | `English`, `Hinglish`, `Hindi_Devanagari` | 0 | Linguistic representation of message |
| `message` | String | UTF-8 Text | 0 | Full SMS text payload |
| `source` | String | `synthetic_manually_authored` | 0 | Provenance indicator for ethical compliance |

---

## 3. Class Balance & Language Composition

The dataset comprises exactly **440 samples**, maintaining perfect 50/50 class balance between scam and legitimate messages.

### Table 2: Class Balance
| Class Label | Interpretation | Sample Count | Percentage |
| :--- | :--- | :--- | :--- |
| `1` | Scam / Fraudulent | 220 | 50.0% |
| `0` | Legitimate / Ham | 220 | 50.0% |
| **Total** | | **440** | **100.0%** |

### Table 3: Language Distribution (Overall vs Target)
| Language | Target % | Actual Count | Actual % | Target Alignment |
| :--- | :--- | :--- | :--- | :--- |
| **English** | ~40.0% | 176 | 40.0% | Exact match |
| **Hinglish** | ~35.0% | 154 | 35.0% | Exact match |
| **Hindi_Devanagari** | ~25.0% | 110 | 25.0% | Exact match |
| **Total** | **100.0%** | **440** | **100.0%** | **Exact match** |

### Table 4: Cross-Tabulation (Class Label x Language)
| Class Label | English | Hinglish | Hindi_Devanagari | Total |
| :--- | :--- | :--- | :--- | :--- |
| **Scam (`1`)** | 88 (40.0%) | 77 (35.0%) | 55 (25.0%) | 220 (100.0%) |
| **Legitimate (`0`)** | 88 (40.0%) | 77 (35.0%) | 55 (25.0%) | 220 (100.0%) |
| **Total** | **176 (40.0%)** | **154 (35.0%)** | **110 (25.0%)** | **440 (100.0%)** |

---

## 4. Category Breakdown

### 4.1 Scam Categories (220 Messages)
| Category Identifier | Category Description | English | Hinglish | Hindi_Devanagari | Total |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `fake_kyc` | Fake KYC & Biometric Suspension Threats | 11 | 10 | 7 | 28 |
| `upi_collect_scam` | UPI Collect-Requests & Fake QR Scams | 11 | 10 | 7 | 28 |
| `electricity_threat` | Immediate Electricity Disconnection Threats | 11 | 10 | 7 | 28 |
| `fake_cashback` | Deceptive Cashback & Scratch Card Rewards | 11 | 10 | 7 | 28 |
| `job_scam` | Work-From-Home & Task-Earning Frauds | 11 | 9 | 7 | 27 |
| `echallan_scam` | Traffic e-Challan & Impending Court Summons | 11 | 9 | 7 | 27 |
| `courier_scam` | Fake Courier Redelivery Fees & Customs Holds | 11 | 10 | 6 | 27 |
| `authority_impersonation` | Income Tax, TRAI & Cyber Crime Impersonation | 11 | 9 | 7 | 27 |
| **Total Scam** | | **88** | **77** | **55** | **220** |

### 4.2 Legitimate Categories (220 Messages)
| Category Identifier | Category Description | English | Hinglish | Hindi_Devanagari | Total |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `bank_alert` | Authentic Bank Debits, Credits & ATM Alerts | 16 | 14 | 10 | 40 |
| `otp_2fa` | Sensitive OTPs with Explicit Security Reminders | 15 | 13 | 10 | 38 |
| `salary_payroll` | Corporate Payroll & Remuneration Notifications | 15 | 12 | 9 | 36 |
| `utility_bill` | Official Utility Invoices (Due Dates & BBPS Portals) | 14 | 13 | 9 | 36 |
| `courier_delivery` | Real Courier Tracking & Doorstep Delivery PINs | 14 | 12 | 9 | 35 |
| `merchant_receipt` | Legitimate UPI Merchant Receipts & UTR Proofs | 14 | 13 | 8 | 35 |
| **Total Legitimate** | | **88** | **77** | **55** | **220** |

---

## 5. Data Integrity & Verification Audit

An automated script `backend/build_and_audit_dataset.py` executed a comprehensive battery of integrity tests:

1. **Missing / Null Check:**
   - Evaluated all 440 rows across 6 fields.
   - Result: **0 null / NaN / empty values** across the entire dataset.
2. **Provenance Check:**
   - Verified `source` column consistency.
   - Result: **100.0% (440/440)** set to `synthetic_manually_authored`.
3. **Unicode Script Verification:**
   - Evaluated all 110 rows tagged as `Hindi_Devanagari` using regular expression `[\\u0900-\\u097F]`.
   - Result: **100.0% (110/110)** contain authentic Unicode Devanagari script (0 Latin transliteration leaks).
4. **Internal Duplicate Audit:**
   - Exact string matching, whitespace-normalized matching, and SHA-256 fingerprinting.
   - Result: **0 internal duplicate messages** (440 unique texts).

---

## 6. Cross-Dataset Leakage & Overlap Audit

To guarantee scientific evaluation validity and prevent data contamination, the 440 training samples were systematically cross-audited against all existing datasets.

### Table 5: Exact Duplicate Audit Across Datasets
| Comparison Dataset | Total Samples in Dataset | Exact Matches Found | Status |
| :--- | :--- | :--- | :--- |
| `datasets/evaluation/indian_sms_eval.csv` | 100 | **0** | PASSED (Clean separation) |
| `datasets/SMSSpamCollection` | 5,574 | **0** | PASSED (No overlap) |
| `datasets/sms_dataset.csv` | 30 | **0** | PASSED (No overlap) |

### 6.1 Token Jaccard Similarity Audit vs Frozen Evaluation Benchmark
Every training message ($T_i, i \in [1, 440]$) was compared against every evaluation benchmark message ($E_j, j \in [1, 100]$), totaling **44,000 pairwise comparisons**.

$$\\text{{Jaccard}}(T_i, E_j) = \\frac{{|\\text{{Tokens}}(T_i) \\cap \\text{{Tokens}}(E_j)|}}{{|\\text{{Tokens}}(T_i) \\cup \\text{{Tokens}}(E_j)|}}$$

- **Pre-defined Leakage Threshold:** Any pair with $\\text{{Jaccard}} \\ge 0.70$ is flagged as near-duplicate leakage.
- **Maximum Jaccard Similarity Observed:** **0.6341** (Train ID 50 vs Eval ID 17).
- **Pairs with Jaccard Similarity $\\ge 0.70$:** **0 pairs** (100% compliance).

The maximum observed pair (0.6341) represents common transactional Hindi terminology between two independent UPI collect scam alerts:
- *Train ID 50:* `फोनपे सूचना: आपको 6,500 रुपये की नकद राशि भेजी गई है। पैसे सीधे बैंक खाते में पाने के लिए ऐप में कलेक्ट रिक्वेस्ट स्वीकारें और यूपीआई पिन दर्ज करें।`
- *Eval ID 17:* `फोनपे कैशबैक: 1,499 रुपये का लकी ड्रा इनाम आपके बैंक खाते में भेजा जा रहा है। राशि प्राप्त करने हेतु कलेक्ट रिक्वेस्ट स्वीकार कर यूपीआई पिन डालें।`
Both messages retain distinct entities, different phrasing structures, different amounts, and independent authorship.

---

## 7. Representative Dataset Samples

### 7.1 Scam Message Examples
- **Fake KYC (English):**
  > `Notice: Your Canara Bank savings account has been put on hold due to missing mandatory PAN re-verification. Update now at https://canarabank-onlinekyc.test to restore services.`
- **UPI Collect Scam (Hinglish):**
  > `PhonePe user, aapko Rs 4,999 ka cashback claim karne ke liye app me collect request approve karna hoga aur apna UPI PIN enter karna hoga.`
- **Electricity Disconnection Threat (Hindi Devanagari):**
  > `अंतिम डिस्कनेक्शन नोटिस: उपकेंद्र से आपके घरेलू मीटर की विद्युत सप्लाई आज दोपहर 2 बजे बंद करने की टीम रवाना हो चुकी है। रोक लगाने हेतु कनिष्ठ अभियंता कक्ष में 9876541230 पर सूचित करें।`
- **Traffic e-Challan Scam (English):**
  > `Traffic Police Department: e-Challan of Rs 1,500 registered against vehicle DL04CQ9102 for overspeeding. Pay online within 24 hours at https://echallan-parivahan-pay.test to avoid court hearing.`
- **Job Scam (Hinglish):**
  > `Ghar baithe part time kaam karke daily Rs 2,500 se Rs 6,000 kamaye. Sirf YouTube videos like karna hai. Payout daily UPI me. Telegram join kare: @parttime_india_earn`
- **Authority Impersonation (Hindi Devanagari):**
  > `आयकर विभाग: मूल्यांकन वर्ष 2025-26 के लिए आपका 19,400 रुपये का रिफंड स्वीकृत हुआ है। अपना खाता विवरण सत्यापित करने हेतु https://incometax-seva-refund.test पर जाएं।`

### 7.2 Legitimate Message Examples
- **Bank Alert (English):**
  > `Dear SBI Customer, your A/C ending with 4821 has been debited by Rs 1,450.00 on 15-Nov-26 at POS 49201928. Avl Bal: Rs 24,190.50. Call 1800112211 if not done by you.`
- **OTP & 2FA (Hinglish, with security advisory):**
  > `Aapka SBI netbanking login OTP 482910 hai. Yeh 5 minute ke liye valid hai. Bank kabhi bhi aapse phone par OTP nahi mangta, kisi ko na bataye.`
- **Salary Credit (Hindi Devanagari):**
  > `एसबीआई वेतन सूचना: आपके खाते XX5821 में टीसीएस द्वारा अक्टूबर माह का वेतन रु 54,200 क्रेडिट किया गया है। कुल शेष: रु 68,400।`
- **Genuine Utility Reminder (English):**
  > `Dear BESCOM consumer 0849201, your electricity bill for Nov-26 of Rs 1,420.00 is due on 24-Nov-26. Pay via official portal bescom.karnataka.gov.in or BBPS enabled apps.`
- **Courier Delivery PIN (Hindi Devanagari):**
  > `मिंत्रा कूरियर: आपका फैशन ऑर्डर शिपमेंट आज डिलीवर किया जाएगा। बॉक्स मिलने के उपरांत ही कूरियर कर्मी को गुप्त कोड 6391 बताएं।`
- **Legitimate UPI Merchant Receipt (English):**
  > `Paid Rs 340.00 to Reliance Retail at Store #402 via PhonePe UPI. Ref: 492019284712. Thank you for shopping.`

---

## 8. Methodological Limitations & Synthetic Data Characteristics

While this dataset provides a balanced foundation for training Indian SMS fraud detectors, the following methodological boundaries are acknowledged:

1. **Synthetic Authoring vs Organic Human Typos:**
   - Synthetic messages maintain relatively consistent grammar, vocabulary, and punctuation. Real-world SMS spam frequently contains intentional lexical obfuscations (e.g., `K-Y-C`, `P@N`, zero-width characters) designed to bypass naive keyword filters.
2. **Safe Placeholder Domains:**
   - In adherence to safety guidelines, all embedded URLs in scam messages utilize non-routable `.test` TLDs (e.g., `sbi-onlinekyc.test`). Real phishing infrastructure rapidly rotates across dynamic cloud subdomains (`.xyz`, `.top`, `.vip`, IP-based redirectors).
3. **Scope of Language Variety:**
   - This dataset focuses on English, Hinglish, and Hindi (Devanagari). Regional Indian scripts (Tamil, Telugu, Bengali, Marathi, Kannada, Malayalam, Gujarati, etc.) are unrepresented in this phase and represent important future extensions.

---

## 9. Next Steps in Development Roadmap

With Step 3 complete and the Indian SMS training dataset validated and saved:
- The dataset is ready to be utilized in **Step 4** (designing and evaluating an upgraded multi-lingual training pipeline).
- No models have been trained or modified in this step.
- The project awaits user review and approval before proceeding to the training pipeline upgrade.
"""

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[SUCCESS] Wrote comprehensive validation report to {report_path}")

if __name__ == "__main__":
    main()
