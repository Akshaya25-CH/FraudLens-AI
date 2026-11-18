import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json
from backend.upi_scanner import analyze_payment_fraud, validate_upi_id_format


def test_upi_scanner():
    print("=" * 70)
    print("FRAUDLENS AI - UPI & PAYMENT FRAUD DETECTION TEST SUITE")
    print("=" * 70)

    test_cases = [
        # 1. PIN to Receive Money (Golden Rule Violation)
        {
            "name": "PIN to Receive Money Scam (Google Pay Cashback)",
            "text": "Congratulations! You have received cashback of Rs 2,500. Enter your 6-digit UPI PIN in Google Pay to claim money into your bank account.",
            "expected_risk": "HIGH",
            "expected_pattern": "pin_to_receive_scam"
        },

        # 2. Scan QR to Receive Money Scam
        {
            "name": "Scan QR to Receive Funds (OLX / Marketplace Scam)",
            "text": "I am sending advance payment of Rs 15,000 for your furniture. Please scan this QR code with PhonePe to receive money directly into your account.",
            "expected_risk": "HIGH",
            "expected_pattern": "qr_receive_scam"
        },

        # 3. Collect Request Approval Trap
        {
            "name": "Collect Request Approval Trap",
            "text": "Dear customer, approve the collect request of Rs 4,999 in Paytm to accept payment from the buyer.",
            "expected_risk": "HIGH",
            "expected_pattern": "collect_request_trap"
        },

        # 4. Fake Cashback & Scratch Card Scam
        {
            "name": "Unsolicited Scratch Card & Reward Scam",
            "text": "You won a scratch card reward worth Rs 1,999 on PhonePe! Click link to claim your reward before it expires.",
            "expected_risk": "HIGH",
            "expected_pattern": "fake_cashback_reward"
        },

        # 5. Remote Access Screen Sharing Prompt
        {
            "name": "Remote Screen Sharing for UPI Activation (AnyDesk)",
            "text": "Your UPI services are on hold. Install AnyDesk and share the 9-digit code with our customer care agent to complete verification.",
            "expected_risk": "HIGH",
            "expected_pattern": "remote_access_tool"
        },

        # 6. Urgent KYC / Bank Account Blocking Threat
        {
            "name": "Urgent SBI YONO UPI Suspension Threat",
            "text": "URGENT! Your SBI UPI account blocked today due to pending KYC. Update PAN card immediately to avoid permanent deactivation.",
            "expected_risk": "HIGH",
            "expected_pattern": "account_suspension_threat"
        },

        # 7. Fake Accidental Transfer Refund Scam
        {
            "name": "Fake Accidental Transfer Refund Demand",
            "text": "Hello, I sent Rs 10,000 to your PhonePe by mistake instead of my brother. Please return and refund back to my UPI ID immediately.",
            "expected_risk": "HIGH",
            "expected_pattern": "accidental_transfer_refund_scam"
        },

        # 8. Legitimate Bank UPI Debit Alert
        {
            "name": "Legitimate Bank Debit Alert (HDFC Bank)",
            "text": "A/C *1234 debited for Rs. 450.00 on 14-Nov-26 via UPI ref 123456789012. Bal: Rs. 12,450.50 - HDFC Bank",
            "expected_risk": "LOW",
            "max_score": 20
        },

        # 9. Legitimate Bank UPI Credit Notification
        {
            "name": "Legitimate Bank Credit Notification (SBI)",
            "text": "Your A/C *5678 credited with Rs. 5,000.00 on 14-Nov-26 by UPI ref 987654321098. - SBI",
            "expected_risk": "LOW",
            "max_score": 20
        },

        # 10. Legitimate Merchant Bill Confirmation
        {
            "name": "Legitimate Merchant Receipt",
            "text": "Payment of Rs 199.00 to Swiggy via UPI successful. Transaction ID: SWIGGY123456.",
            "expected_risk": "LOW",
            "max_score": 20
        },

        # 11. Suspicious VPA Keyword Stuffing
        {
            "name": "Suspicious Support Keyword in UPI VPA",
            "text": "Pay your penalty fee to sbi-customercare-refund@ybl to unblock your account.",
            "expected_risk": "HIGH",
            "expected_pattern": "suspicious_vpa"
        },

        # 12. Empty Input Edge Case
        {
            "name": "Empty Input Validation",
            "text": "",
            "expected_risk": "HIGH",
            "expected_pattern": "empty_input"
        }
    ]

    passed_count = 0
    total_count = len(test_cases)

    for i, test in enumerate(test_cases, 1):
        name = test["name"]
        text = test["text"]
        exp_risk = test["expected_risk"]
        exp_pat = test.get("expected_pattern")

        result = analyze_payment_fraud(text)
        risk = result.get("risk_category")
        score = result.get("structural_risk_score")
        patterns = result.get("detected_patterns", [])

        print(f"\n[TEST {i}/{total_count}] {name}")
        print(f"  Input:         \"{text[:60]}...\"" if len(text) > 60 else f"  Input:         \"{text}\"")
        print(f"  Risk Category: {risk} (Expected: {exp_risk})")
        print(f"  Score:         {score}/100")
        print(f"  Patterns:      {patterns}")

        # Assertions
        assert risk == exp_risk, f"FAILED: Expected risk {exp_risk}, got {risk}"
        if exp_pat:
            assert any(p.startswith(exp_pat) for p in patterns), f"FAILED: Expected pattern {exp_pat} in {patterns}"
        if "max_score" in test:
            assert score <= test["max_score"], f"FAILED: Expected score <= {test['max_score']}, got {score}"

        # Verify disclaimer and safety recommendation exist
        assert "disclaimer" in result and len(result["disclaimer"]) > 0
        assert "recommendation" in result and len(result["recommendation"]) > 0
        assert "ML probability" not in json.dumps(result), "Failed: Found reference to ML probability"

        passed_count += 1
        print("  -> STATUS: PASS")

    print("\n--- Testing Standalone UPI ID Format Validation ---")
    vpa_tests = [
        ("user@okhdfcbank", True, True, False),
        ("9876543210@paytm", True, True, False),
        ("merchant-support-refund@ybl", True, True, True),
        ("invalid_vpa_without_at", False, False, False),
        ("user@@multipleat", False, False, False),
    ]

    for vpa, exp_valid, exp_known, exp_sus in vpa_tests:
        v_res = validate_upi_id_format(vpa)
        print(f"VPA: {vpa:<30} -> Valid: {v_res['is_valid_format']}, Known Handle: {v_res['is_known_handle']}, Sus Keyword: {v_res['has_suspicious_keywords']}")
        assert v_res["is_valid_format"] == exp_valid
        assert v_res["is_known_handle"] == exp_known
        assert v_res["has_suspicious_keywords"] == exp_sus

    print("\n" + "=" * 70)
    print(f"ALL {passed_count}/{total_count} UPI SCENARIO & VPA FORMAT TESTS PASSED!")
    print("=" * 70)


if __name__ == "__main__":
    test_upi_scanner()
