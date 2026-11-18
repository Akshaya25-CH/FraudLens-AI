# Script to generate datasets/training/FINAL_QUALITY_AUDIT.md
import os

report_content = """# FraudLens AI — Step 3.1: Final Quality Audit Report

**Target Dataset:** `datasets/training/indian_sms_train.csv`  
**Audit Type:** Read-Only Methodological & Quality Audit  
**Audit Date:** November 15, 2026  
**Total Records Audited:** 440  
**Overall Audit Status:** **PASS WITH METHODOLOGICAL ADVISORIES (NO BLOCKERS)**  

---

## Executive Summary

This read-only audit evaluates `datasets/training/indian_sms_train.csv` (440 samples: 220 scam, 220 legitimate) across five core data quality dimensions:
1. **Phone Numbers & Personal Data Privacy**
2. **Template Diversity & Structural Repetition**
3. **Classification Shortcuts & Spurious Correlations**
4. **Language Authenticity (English, Hinglish, Devanagari Hindi)**
5. **Label Ground Truth & Boundary Ambiguity**

No modifications have been made to the dataset, model joblib, training code, or frozen evaluation set.

---

## Summary Scorecard

| Quality Dimension | Status | Key Finding | Primary Action / Advisory |
| :--- | :---: | :--- | :--- |
| **1. Phone Numbers & Personal Data** | **WARNING** | 51 messages contain 10-digit mobile numbers; 40 have masked accounts; 26 have vehicle plates. | Implement tokenization placeholders (`[PHONE]`, `[ACCOUNT]`, `[VEHICLE]`) during training. |
| **2. Template Diversity** | **PASS** | 220/220 unique abstract templates in Scam (100%); 220/220 in Legit (100%). | 0 exact structural duplicate skeletons. |
| **3. Classification Shortcuts** | **WARNING** | URLs appear in 65.5% of Scams vs 0% of Legitimate messages (4.1% bare domains). | Add URL normalization (`[URL]`) and augment training with URL-containing legit messages in future. |
| **4. Language Authenticity** | **PASS** | 100% Devanagari script integrity (110/110); 100% authentic Hinglish syntax (154/154). | No misclassified language rows; no machine-translation artifacts. |
| **5. Label Quality & Ambiguity** | **PASS** | Zero incorrect ground truth labels; includes valuable hard negatives and hard positives. | Retain challenging boundary cases (e.g. DTH expiry, bank dispute alerts). |

---

## Detailed Audit Findings

### 1. Phone Numbers and Personal Data
**Status: WARNING**

#### Observations
1. **10-Digit Mobile Numbers:**
   - Detected in **51 messages** (46 Scam messages, 5 Legitimate messages).
   - *Scam context:* Call-to-actions prompting victims to contact fraudulent helpline numbers or personal scam coordinators (e.g., `Contact Electricity Officer at 9876504321`, `Call nodal manager at 9811223344`, `WhatsApp HR Sneha at 9876012345`).
   - *Legitimate context:* Security dispatch or SMS shortcode escalation (e.g., Kotak `SMS BLOCK to 9971056767`).
   - *Privacy Risk Assessment:* Although all numbers were synthetically authored using dummy patterns (`98765...`, `981100...`, `991122...`), under the Indian Department of Telecommunications (DoT) National Numbering Plan, any 10-digit sequence starting with 6, 7, 8, or 9 could coincide with active civilian subscribers.
2. **Toll-Free Numbers:**
   - 3 legitimate messages cite official institutional toll-free / customer care lines (`1800112211` for SBI, `18002008` for ICICI, `18604195555` for Axis).
3. **Financial & Account Identifiers:**
   - 40 messages cite masked account numbers (`A/C ending with 4821`, `A/C XX9012`, `A/C XX1829`).
   - 12 messages cite masked credit/debit card numbers (`Credit Card XX4019`, `Debit Card XX7102`).
   - None contain unmasked 16-digit PANs or full 11-16 digit bank accounts.
4. **Vehicle Numbers:**
   - 26 messages in `echallan_scam` feature realistic RTO plate numbers (e.g., `DL04CQ9102`, `MH02DE4819`, `HR26BQ8192`, `KA01MJ3920`).
5. **Personal Names:**
   - 15 messages mention common Indian names (e.g., `Ramesh Kumar`, `HR Pooja`, `Sneha`, `Rider Akash`, `Deepak`).

#### Safe Placeholder Recommendations
To prevent memorization of specific numbers or plate formats by NLP models, the text preprocessing pipeline should normalize tokens prior to vectorization:
- Raw 10-digit mobile numbers $\\rightarrow$ `[PHONE]`
- Official toll-free prefixes (`1800...`, `1860...`) $\\rightarrow$ `[TOLLFREE]`
- Masked accounts / card numbers $\\rightarrow$ `[ACCOUNT]` / `[CARD]`
- Vehicle registration plates $\\rightarrow$ `[VEHICLE]`
- Transactional amounts $\\rightarrow$ `[AMOUNT]`

---

### 2. Template Diversity
**Status: PASS**

#### Observations
To test structural diversity, messages were abstracted by replacing all entities (banks, amounts, numbers, URLs, phones, dates) with generic semantic tokens (`<BRAND>`, `<AMT>`, `<NUM>`, `<URL>`, `<PHONE>`, `<VEHICLE>`).

- **Scam Class (220 samples):** **220 unique abstract templates (100.0%)**
- **Legitimate Class (220 samples):** **220 unique abstract templates (100.0%)**
- **Template Repetition Count (>1 exact structural duplicate):** **0 in Scam, 0 in Legit**

#### Analysis
- Even within standardized categories such as `echallan_scam` or `bank_alert`, every message exhibits natural lexical and syntactic variability (e.g., varying word order, alternative postpositions, different phrasing of consequences and reporting instructions).
- No robotic copy-paste patterns where only the bank name or amount was substituted into an identical template.

---

### 3. Classification Shortcuts (Spurious Correlations)
**Status: WARNING**

#### Observations

| Feature / Signal | Scam Prevalence (`label=1`) | Legit Prevalence (`label=0`) | Disparity Ratio | Risk Description |
| :--- | :---: | :---: | :---: | :--- |
| **HTTP/HTTPS URLs** | **144 / 220 (65.5%)** | **0 / 220 (0.0%)** | $\\infty$ | Extreme shortcut risk. Linear models can assign overwhelmingly heavy weights to URL tokens (`http`, `https`, `test`). |
| **Bare Domain Mentions** | **0 / 220 (0.0%)** | **9 / 220 (4.1%)** | 0.0x | Legit utility bills mention bare official portals (`bescom.karnataka.gov.in`, `uppcl.org`, `bsesdelhi.com`). |
| **Urgency Indicators** | **84 / 220 (38.2%)** | **22 / 220 (10.0%)** | 3.82x | Scam messages heavily emphasize immediate threats (`immediately`, `24 hours`, `tonight`, `turant`, `काट दी जाएगी`). |
| **Security Disclaimers** | **1 / 220 (0.5%)** | **27 / 220 (12.3%)** | 0.04x | OTP alerts heavily feature "Do not share OTP / बैंक कभी ओटीपी नहीं मांगता". |
| **Monetary Amounts** | **99 / 220 (45.0%)** | **143 / 220 (65.0%)** | 0.69x | Legitimate transactional notifications are more likely to feature exact debit/credit figures. |
| **Major Brand Distribution** | Balanced across both classes | Balanced across both classes | ~1.0x | Brands (SBI, HDFC, ICICI, PhonePe, Paytm, Amazon) are evenly distributed between scam and legitimate classes. |

#### Shortcut Mitigation Recommendations
1. **URL Presence vs Semantics:** 76 scam messages (34.5%) do not contain URLs (relying instead on QR codes, collect requests, or phone calls). This prevents URLs from being an absolute necessity for scam classification.
2. **URL Token Normalization:** The ML pipeline should normalize all URLs to a single token (e.g. `[URL]`) rather than letting the model memorize specific dummy domains (`.test`) or individual URL path components.
3. **Hard Negatives:** Legitimate utility bill reminders that contain official government/utility URLs (e.g., IDs 335, 336, 339, 344) must be preserved to penalize models that treat any domain as hostile.

---

### 4. Language Authenticity
**Status: PASS**

#### Observations
1. **Devanagari Hindi:**
   - 110 messages (55 scam, 55 legit) verified.
   - 100% of rows contain valid Unicode Devanagari characters (`\\u0900-\\u097F`).
   - Average Devanagari character ratio is **74.8%** (with remaining characters comprising ASCII digits, brand names, and currency symbols).
   - Natural Hindi grammatical phrasing and idioms confirmed:
     - Scam: `अंतिम डिस्कनेक्शन नोटिस: उपकेंद्र से आपके घरेलू मीटर की विद्युत सप्लाई आज दोपहर 2 बजे बंद करने की टीम रवाना हो चुकी है।`
     - Legit: `एसबीआई वेतन सूचना: आपके खाते XX5821 में टीसीएस द्वारा अक्टूबर माह का वेतन रु 54,200 क्रेडिट किया गया है।`
2. **Hinglish:**
   - 154 messages (77 scam, 77 legit) verified.
   - Checked for presence of colloquial Hindi lexical markers (`aapka`, `hai`, `kare`, `hoga`, `turant`, `khate me`, `bachane ke liye`).
   - 150 / 154 messages contain $\\ge 2$ core marker words.
   - The remaining 4 messages (IDs 104, 423, 427, 432) are concise merchant receipts/promos that naturally mix English terms with postpositions (`Chai Point par Rs 90 ka payment successful hua`, `Grocery bill Rs 1,650 ka bhugtan PhonePe se complete hua`).
   - Zero English messages misclassified as Hinglish.

---

### 5. Label Quality & Boundary Ambiguity
**Status: PASS**

#### Observations
All 440 labels were audited for ground truth correctness. No mislabelled messages were identified.

#### Valuable Boundary / Edge Cases Identified:
1. **Hard Negatives (Legitimate messages with scam-like vocabulary):**
   - **ID 223 (`bank_alert`):**
     > `ICICI Bank: INR 599.00 spent on your Credit Card XX4019 on 15-Nov-26 at NETFLIX INDIA. Available Limit: INR 1,42,800.00. Call 18002008 for dispute.`
     *(Contains "dispute" and an unexpected subscription charge alert; tests false positive resistance).*
   - **ID 225 (`bank_alert`):**
     > `Kotak Bank: Rs 1,890.00 debited from A/C 908123 for UPI/592019482019/Zomato. Avl Bal: Rs 31,450.25. If not you, SMS BLOCK to 9971056767.`
     *(Contains "SMS BLOCK" instructions; could mislead models biased on "BLOCK").*
   - **ID 357 (`utility_bill`):**
     > `Tata Play DTH: Subscriber ID 30192847 ka account 21-Nov-26 ko deactivate hoga. Nirantar entertainment ke liye Rs 299 ka recharge kare.`
     *(Contains "account ... deactivate hoga"; resembles account suspension scam pretexts but is a legitimate DTH recharge reminder).*
2. **Hard Positives (Scam messages without URLs):**
   - **ID 29 (`upi_collect_scam`):**
     > `Google Pay Notification: An approved refund of Rs 6,850 is waiting. Click approve on the pending collect request and submit UPI PIN to claim money to bank.`
     *(No URL; operates entirely within UPI collect-request deception).*
   - **ID 67 (`electricity_threat`):**
     > `Electricity Office Alert: Power supply for meter 982019482 will be disconnected tonight at 9:30 PM due to unpaid balance. Contact field officer immediately at 9876504321.`
     *(No URL; operates via phone social engineering).*
   - **ID 90 (`job_scam`):**
     > `Amazon Online Recruitment: Work from home 2 hours daily and earn Rs 3,500 to Rs 9,000 per day by rating products. Message HR Ananya on WhatsApp at 9876512340 to register.`
     *(No URL; operates via WhatsApp recruiting bait).*

These boundary cases are methodologically sound and improve model robustness against superficial keyword matching.

---

## Conclusion & Readiness Assessment

The dataset `datasets/training/indian_sms_train.csv` has successfully passed the final quality audit. 

- **Data Integrity:** 100% complete, 0 nulls, 0 duplicate templates.
- **Language Coverage:** Clean representation across English (40%), Hinglish (35%), and Devanagari Hindi (25%).
- **Pre-Training Advice:** During training pipeline implementation (Step 4), text preprocessing should incorporate token normalization for URLs (`[URL]`), phone numbers (`[PHONE]`), and account masks (`[ACCOUNT]`) to neutralize potential shortcut features.
"""

with open("datasets/training/FINAL_QUALITY_AUDIT.md", "w", encoding="utf-8") as f:
    f.write(report_content)

print("[SUCCESS] datasets/training/FINAL_QUALITY_AUDIT.md successfully generated.")
