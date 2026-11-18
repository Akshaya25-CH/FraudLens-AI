import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json
from backend.main import (
    app, home, health_check,
    scan_message, ScanRequest,
    scan_url, UrlScanRequest,
    scan_payment, PaymentScanRequest
)

def test_endpoints_direct():
    print("=" * 70)
    print("FRAUDLENS AI - BACKEND COMBINED ENDPOINTS VERIFICATION")
    print("=" * 70)

    # 1. Test GET /
    print("\n[TEST 1] Testing GET / (home)")
    res_home = home()
    print("Result:", json.dumps(res_home, indent=2))
    assert "FraudLens AI" in res_home["message"]
    assert "version" in res_home
    assert len(res_home["modules"]) == 3

    # 2. Test GET /health
    print("\n[TEST 2] Testing GET /health (health_check)")
    res_health = health_check()
    print("Result:", json.dumps(res_health, indent=2))
    assert res_health["status"] == "healthy"
    assert res_health["model_loaded"] is True
    assert "payment_scanner" in res_health["modules"]

    # 3. Test POST /scan with suspicious SMS
    suspicious_sms = "URGENT! Your bank account is blocked. Verify your KYC immediately."
    print(f"\n[TEST 3] Testing POST /scan (Suspicious SMS)")
    print(f"Input: \"{suspicious_sms}\"")
    req_scam = ScanRequest(message=suspicious_sms)
    res_scam = scan_message(req_scam)
    print("Result:", json.dumps(res_scam, indent=2))
    assert res_scam["prediction"] == 1
    assert res_scam["risk_level"] == "POTENTIAL_FRAUD"
    assert "model_score" in res_scam

    # 4. Test POST /scan with legitimate SMS
    legit_sms = "Your bank account has been credited with 5000 rupees."
    print(f"\n[TEST 4] Testing POST /scan (Legitimate SMS)")
    print(f"Input: \"{legit_sms}\"")
    req_legit = ScanRequest(message=legit_sms)
    res_legit = scan_message(req_legit)
    print("Result:", json.dumps(res_legit, indent=2))
    assert res_legit["prediction"] == 0
    assert res_legit["risk_level"] == "NO_FRAUD_PATTERN_DETECTED"

    # 5. Test POST /scan-url with normal legitimate URL
    legit_url = "https://www.google.com/search?q=fraudlens"
    print(f"\n[TEST 5] Testing POST /scan-url (Legitimate URL)")
    print(f"Input: \"{legit_url}\"")
    req_url_legit = UrlScanRequest(url=legit_url)
    res_url_legit = scan_url(req_url_legit)
    print("Result:", json.dumps(res_url_legit, indent=2))
    assert res_url_legit["risk_category"] == "LOW"
    assert res_url_legit["structural_risk_score"] < 25

    # 6. Test POST /scan-url with High Risk Phishing URL
    phish_url = "http://192.168.1.1/admin/login?dest=http://evil.com"
    print(f"\n[TEST 6] Testing POST /scan-url (High Risk Phishing URL)")
    print(f"Input: \"{phish_url}\"")
    req_url_phish = UrlScanRequest(url=phish_url)
    res_url_phish = scan_url(req_url_phish)
    print("Result:", json.dumps(res_url_phish, indent=2))
    assert res_url_phish["risk_category"] == "HIGH"

    # 7. Test POST /scan-payment with UPI PIN Cashback Scam
    upi_scam_msg = "Congratulations! You won cashback of Rs 2,500. Enter your UPI PIN to claim money into your account."
    print(f"\n[TEST 7] Testing POST /scan-payment (UPI PIN Scam)")
    print(f"Input: \"{upi_scam_msg}\"")
    req_upi_scam = PaymentScanRequest(message=upi_scam_msg)
    res_upi_scam = scan_payment(req_upi_scam)
    print("Result:", json.dumps(res_upi_scam, indent=2))
    assert res_upi_scam["risk_category"] == "HIGH"
    assert "pin_to_receive_scam" in res_upi_scam["detected_patterns"]

    # 8. Test POST /scan-payment with Legitimate Bank Transaction
    upi_legit_msg = "A/C *1234 debited for Rs. 450.00 on 14-Nov-26 via UPI ref 123456789012. Bal: Rs. 12,450.50 - HDFC Bank"
    print(f"\n[TEST 8] Testing POST /scan-payment (Legitimate Bank Alert)")
    print(f"Input: \"{upi_legit_msg}\"")
    req_upi_legit = PaymentScanRequest(message=upi_legit_msg)
    res_upi_legit = scan_payment(req_upi_legit)
    print("Result:", json.dumps(res_upi_legit, indent=2))
    assert res_upi_legit["risk_category"] == "LOW"

    # 9. Test POST /scan-payment with Standalone Suspicious VPA
    print(f"\n[TEST 9] Testing POST /scan-payment (Suspicious VPA Check)")
    req_vpa = PaymentScanRequest(message="", upi_id="sbi-refund-support@ybl")
    res_vpa = scan_payment(req_vpa)
    print("Result:", json.dumps(res_vpa, indent=2))
    assert len(res_vpa["vpa_evaluations"]) > 0
    assert res_vpa["vpa_evaluations"][0]["has_suspicious_keywords"] is True

    print("\n" + "=" * 70)
    print("ALL COMBINED BACKEND ENDPOINTS & DETECTION TESTS PASSED!")
    print("=" * 70)

if __name__ == "__main__":
    test_endpoints_direct()
