import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import joblib
from backend.url_scanner import analyze_url_structure
from backend.upi_scanner import analyze_payment_fraud, validate_upi_id_format

def audit_everything():
    print("=" * 70)
    print("FRAUDLENS AI - DEEP END-TO-END AUDIT & REGRESSION SUITE")
    print("=" * 70)

    # -------------------------------------------------------------
    # 1. Audit SMS Model
    # -------------------------------------------------------------
    print("\n--- [AUDIT 1] SMS Model Scenarios ---")
    model_path = PROJECT_ROOT / "models" / "sms_model.joblib"
    model = joblib.load(model_path)

    sms_cases = [
        # (text, expected_label, description)
        ("URGENT! Your bank account is blocked. Verify your KYC immediately.", 1, "KYC Phishing Scam"),
        ("Congratulations! You won a lottery. Pay a fee to claim your prize.", 1, "Lottery Prize Scam"),
        ("Your salary has been credited successfully.", 0, "Salary Credit Notice"),
        ("Your monthly electricity bill is due on 20 November.", 0, "Monthly Utility Due"),
        ("Free entry in 2 a weekly comp to win FA Cup final tkts 21st May 2005.", 1, "Classic Spam/Scam Contest"),
        ("Hey, are we still meeting for lunch at 1 PM today?", 0, "Personal Conversational Message"),
        ("Dear customer, your card ending in 4321 was charged 1500 INR at Starbucks.", 0, "Card Transaction Alert"),
        ("CLAIM YOUR 5000 CASH PRIZE NOW! CALL 09061743810 IMMEDIATELY TO RECEIVE", 1, "Cash Prize Urgent Demand")
    ]

    sms_failures = []
    for text, expected, desc in sms_cases:
        pred = int(model.predict([text])[0])
        score = float(model.predict_proba([text])[0][1]) * 100
        status = "PASS" if pred == expected else "FAIL"
        if status == "FAIL":
            sms_failures.append((desc, text, expected, pred, score))
        print(f"[{status}] {desc:<30} -> Pred: {pred} (Score: {score:.1f}%)")

    # -------------------------------------------------------------
    # 2. Audit URL Scanner
    # -------------------------------------------------------------
    print("\n--- [AUDIT 2] URL Scanner Scenarios ---")
    url_cases = [
        # Legitimate
        ("https://www.google.com/search?q=financial+fraud+prevention", "LOW", "Legitimate Google Search"),
        ("https://github.com/fastapi/fastapi", "LOW", "Legitimate GitHub Repo"),
        ("https://en.wikipedia.org/wiki/Phishing", "LOW", "Legitimate Wikipedia"),
        ("https://medium.com/@johndoe", "LOW", "Medium User Profile with @ in Path"),
        ("https://twitter.com/@support", "LOW", "Twitter Profile with @ in Path"),
        ("https://www.npmjs.com/package/@angular/core", "LOW", "NPM Scoped Package with @ in Path"),
        ("https://www.amazon.com/dp/B08N5WRWNW", "LOW", "Legitimate Amazon Product URL"),
        ("https://apple.com/iphone", "LOW", "Legitimate Apple Domain"),
        ("https://paypal.com/signin", "LOW", "Legitimate PayPal Domain"),
        # Suspicious / Phishing
        ("https://paypal.com.verify-billing-update.xyz/login", "HIGH", "Subdomain Brand Spoof"),
        ("http://192.168.1.100/admin/bank-login", "HIGH", "Direct IP Hostname"),
        ("http://xn--pple-43d.com/support/login", "HIGH", "Punycode Homograph"),
        ("https://bit.ly/3xY7zQ", "MEDIUM", "URL Shortener Link"),
        ("http://admin:secret@chase-portal.com/login", "HIGH", "Embedded Userinfo Credentials"),
        ("http://paypal.com@verification-auth-portal.com", "HIGH", "Spoofed Authority with @"),
        ("javascript:alert(document.cookie)", "HIGH", "Dangerous JavaScript Protocol"),
        ("http://secure-banking-portal.com:8443/auth", "MEDIUM", "Non-Standard Port 8443"),
        ("http://192.168.1.1/admin/login?dest=http://evil.com", "HIGH", "Open Redirect Parameter"),
    ]

    url_failures = []
    for raw_url, expected_risk, desc in url_cases:
        res = analyze_url_structure(raw_url)
        risk = res.get("risk_category")
        score = res.get("structural_risk_score")
        status = "PASS" if risk == expected_risk else "FAIL"
        if status == "FAIL":
            url_failures.append((desc, raw_url, expected_risk, risk, score, res.get("warning_signs")))
        print(f"[{status}] {desc:<40} -> Risk: {risk:<6} (Score: {score}/100)")

    # -------------------------------------------------------------
    # 3. Audit UPI Scanner
    # -------------------------------------------------------------
    print("\n--- [AUDIT 3] UPI Scanner Scenarios ---")
    upi_cases = [
        # 7 Quick Test Scenarios
        ("Congratulations! You have received cashback of Rs 2,500. Enter your 6-digit UPI PIN in Google Pay to claim money into your bank account.", "rewards-dept@okhdfcbank", "HIGH", "PIN to Receive Cashback"),
        ("I am sending advance payment of Rs 15,000 for your furniture. Please scan this QR code with PhonePe to receive money directly into your account.", "olx-buyer-pay@paytm", "HIGH", "Scan QR Code to Receive Money"),
        ("Dear customer, approve the collect request of Rs 4,999 in Paytm to accept payment from the buyer.", "payment-accept@ybl", "HIGH", "Collect Request Approval Trap"),
        ("Hello, I sent Rs 10,000 to your PhonePe by mistake instead of my brother. Please return and refund back to my UPI ID immediately.", "rahul.kumar@okaxis", "HIGH", "Fake Accidental Transfer Refund"),
        ("Pay your penalty fee to unblock your account before 6 PM.", "sbi-customercare-refund@ybl", "HIGH", "Suspicious VPA Keyword Spoofing"),
        ("A/C *1234 debited for Rs. 450.00 on 14-Nov-26 via UPI ref 123456789012. Bal: Rs. 12,450.50 - HDFC Bank", "swiggy@icici", "LOW", "Legitimate HDFC Debit Alert"),
        ("Your A/C *5678 credited with Rs. 5,000.00 on 14-Nov-26 by UPI ref 987654321098. - SBI", "amit.verma@oksbi", "LOW", "Legitimate SBI Credit Notification"),
        # Additional edge cases
        ("Your UPI services are on hold. Install AnyDesk and share the code.", None, "HIGH", "Remote Desktop (AnyDesk) Theft"),
        ("URGENT! Your SBI UPI account blocked today due to pending KYC.", None, "HIGH", "Urgent KYC Suspension Threat"),
        ("Payment of Rs 199.00 to Swiggy via UPI successful. Transaction ID: UPI123456789.", None, "LOW", "Merchant Payment Receipt"),
    ]

    upi_failures = []
    for msg, vpa, expected_risk, desc in upi_cases:
        res = analyze_payment_fraud(msg, vpa)
        risk = res.get("risk_category")
        score = res.get("structural_risk_score")
        status = "PASS" if risk == expected_risk else "FAIL"
        if status == "FAIL":
            upi_failures.append((desc, msg, vpa, expected_risk, risk, score, res.get("detected_patterns")))
        print(f"[{status}] {desc:<40} -> Risk: {risk:<6} (Score: {score}/100)")

    # -------------------------------------------------------------
    # 4. Audit Edge Cases & Invalid Inputs
    # -------------------------------------------------------------
    print("\n--- [AUDIT 4] Edge Cases & Input Validation ---")
    # Empty URL
    empty_url_res = analyze_url_structure("")
    print(f"Empty URL -> is_valid: {empty_url_res['is_valid']}, risk: {empty_url_res['risk_category']}")
    assert empty_url_res["is_valid"] is False

    # Empty Payment
    empty_payment_res = analyze_payment_fraud("", None)
    print(f"Empty Payment -> is_valid: {empty_payment_res['is_valid']}, risk: {empty_payment_res['risk_category']}")
    assert empty_payment_res["is_valid"] is False

    # Standalone VPA Validation
    vpa1 = validate_upi_id_format("user@okhdfcbank")
    vpa2 = validate_upi_id_format("refund-desk@ybl")
    vpa3 = validate_upi_id_format("invalid@@vpa")
    assert vpa1["is_valid_format"] is True and vpa1["has_suspicious_keywords"] is False
    assert vpa2["is_valid_format"] is True and vpa2["has_suspicious_keywords"] is True
    assert vpa3["is_valid_format"] is False
    print("VPA format validations passed!")

    print("\n" + "=" * 70)
    print(f"AUDIT SUMMARY: SMS Failures={len(sms_failures)}, URL Failures={len(url_failures)}, UPI Failures={len(upi_failures)}")
    if url_failures:
        print("\nURL FAILURES DETAILS:")
        for f in url_failures:
            print(" ", f)
    print("=" * 70)

if __name__ == "__main__":
    audit_everything()
