import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.main import scan_payment, PaymentScanRequest
from backend.upi_scanner import analyze_payment_fraud, validate_upi_id_format
from fastapi import HTTPException

def test_upi_comprehensive():
    print("=" * 70)
    print("FRAUDLENS AI - UPI & PAYMENT COMPREHENSIVE REGRESSION AUDIT")
    print("=" * 70)

    # 1. Test all 7 quick-test scenarios
    quick_test_cases = [
        (
            "Quick-Test 1: PIN to Receive Cashback",
            "Congratulations! You have received cashback of Rs 2,500. Enter your 6-digit UPI PIN in Google Pay to claim money into your bank account.",
            "rewards-dept@okhdfcbank",
            "HIGH",
            "pin_to_receive_scam"
        ),
        (
            "Quick-Test 2: Scan QR Code to Receive Money",
            "I am sending advance payment of Rs 15,000 for your furniture. Please scan this QR code with PhonePe to receive money directly into your account.",
            "olx-buyer-pay@paytm",
            "HIGH",
            "qr_receive_scam"
        ),
        (
            "Quick-Test 3: Collect Request Approval Trap",
            "Dear customer, approve the collect request of Rs 4,999 in Paytm to accept payment from the buyer.",
            "payment-accept@ybl",
            "HIGH",
            "collect_request_trap"
        ),
        (
            "Quick-Test 4: Fake Accidental Transfer Refund",
            "Hello, I sent Rs 10,000 to your PhonePe by mistake instead of my brother. Please return and refund back to my UPI ID immediately.",
            "rahul.kumar@okaxis",
            "HIGH",
            "accidental_transfer_refund_scam"
        ),
        (
            "Quick-Test 5: Suspicious VPA Keyword Spoofing",
            "Pay your penalty fee to unblock your account before 6 PM.",
            "sbi-customercare-refund@ybl",
            "HIGH",
            "suspicious_vpa_sbi-customercare-refund"
        ),
        (
            "Quick-Test 6: Legitimate HDFC Debit Alert",
            "A/C *1234 debited for Rs. 450.00 on 14-Nov-26 via UPI ref 123456789012. Bal: Rs. 12,450.50 - HDFC Bank",
            "swiggy@icici",
            "LOW",
            None
        ),
        (
            "Quick-Test 7: Legitimate SBI Credit Notification",
            "Your A/C *5678 credited with Rs. 5,000.00 on 14-Nov-26 by UPI ref 987654321098. - SBI",
            "amit.verma@oksbi",
            "LOW",
            None
        ),
    ]

    all_passed = True
    for name, msg, vpa, expected_risk, expected_pattern in quick_test_cases:
        print(f"\n--- Testing [{name}] ---")
        req = PaymentScanRequest(message=msg, upi_id=vpa)
        res = scan_payment(req)
        risk = res["risk_category"]
        score = res["structural_risk_score"]
        patterns = res["detected_patterns"]
        print(f"  Risk: {risk}, Score: {score}/100, Patterns: {patterns}")
        assert risk == expected_risk, f"FAILED: Expected {expected_risk}, got {risk}"
        if expected_pattern:
            assert expected_pattern in patterns, f"FAILED: Expected pattern {expected_pattern} in {patterns}"
        print(f"  [PASS] Matches expected {expected_risk}")

    # 2. Test Invalid VPA Formats
    print("\n--- Testing Invalid VPA Formats ---")
    vpa_tests = [
        ("user@okhdfcbank", True, "Standard bank handle"),
        ("9876543210@paytm", True, "Standard phone number handle"),
        ("invalid-no-at-sign", False, "Missing @ symbol"),
        ("user@@multiple-at.com", False, "Multiple @ symbols"),
        ("user*special!#@ybl", False, "Invalid characters in username"),
        ("", False, "Empty VPA"),
    ]
    for vpa_str, expected_valid, desc in vpa_tests:
        v_eval = validate_upi_id_format(vpa_str)
        is_val = v_eval["is_valid_format"]
        print(f"VPA: {vpa_str!r:<25} -> Valid: {is_val!s:<5} (Expected: {expected_valid!s:<5}) -> {desc}")
        assert is_val == expected_valid, f"FAILED for {vpa_str}: Expected {expected_valid}, got {is_val}"

    # 3. Check Disclaimers & Accuracy Claims
    print("\n--- Verifying VPA & Privacy Claims ---")
    dummy_res = analyze_payment_fraud("Pay money", "sbi-support@ybl")
    disclaimer = dummy_res["disclaimer"]
    print(f"Disclaimer text:\n  \"{disclaimer}\"")
    assert "does NOT connect to live NPCI databases" in disclaimer
    assert "does NOT verify bank account ownership" in disclaimer
    assert "NEVER initiates real financial transactions" in disclaimer
    print("[PASS] Disclaimers are explicit and make zero false claims of account verification!")

    # 4. Test Empty / Whitespace Inputs on /scan-payment
    print("\n--- Testing Empty / Whitespace Input on /scan-payment ---")
    try:
        req_empty = PaymentScanRequest(message="", upi_id=None)
        scan_payment(req_empty)
        print("  [FAIL] Expected 400 for empty input, but succeeded!")
        all_passed = False
    except HTTPException as e:
        print(f"  [PASS] Correctly raised HTTPException: {e.status_code} - {e.detail}")

    try:
        req_ws = PaymentScanRequest(message="   ", upi_id="   ")
        scan_payment(req_ws)
        print("  [FAIL] Expected 400 for whitespace input, but succeeded!")
        all_passed = False
    except HTTPException as e:
        print(f"  [PASS] Correctly raised HTTPException: {e.status_code} - {e.detail}")

    print("\n" + "=" * 70)
    assert all_passed, "Some UPI comprehensive tests failed!"
    print("ALL UPI COMPREHENSIVE TESTS EXECUTED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    test_upi_comprehensive()
