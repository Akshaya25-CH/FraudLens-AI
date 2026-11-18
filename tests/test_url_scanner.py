import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json
from backend.url_scanner import analyze_url_structure


def test_url_scanner():
    print("=" * 65)
    print("FRAUDLENS AI - URL PHISHING DETECTION TEST SUITE")
    print("=" * 65)

    test_cases = [
        # 1. Normal Legitimate URLs (Expected: LOW risk)
        {
            "name": "Legitimate Search Engine URL",
            "url": "https://www.google.com/search?q=financial+fraud+prevention",
            "expected_risk": "LOW",
            "max_score": 25
        },
        {
            "name": "Legitimate Open Source Repository URL",
            "url": "https://github.com/fastapi/fastapi",
            "expected_risk": "LOW",
            "max_score": 25
        },
        {
            "name": "Legitimate News/Wikipedia URL",
            "url": "https://en.wikipedia.org/wiki/Phishing",
            "expected_risk": "LOW",
            "max_score": 25
        },

        # 2. IP-based URLs (Expected: HIGH risk)
        {
            "name": "Direct IPv4 Address with Sensitive Path",
            "url": "http://192.168.1.100/admin/bank-login",
            "expected_risk": "HIGH",
            "expected_sign": "ip_hostname"
        },
        {
            "name": "Public IPv4 Host",
            "url": "http://45.33.32.156/portal",
            "expected_risk": "HIGH",
            "expected_sign": "ip_hostname"
        },

        # 3. URL Shorteners (Expected: MEDIUM risk)
        {
            "name": "Bitly Shortened URL",
            "url": "https://bit.ly/3xY7zQ",
            "expected_risk": "MEDIUM",
            "expected_sign": "url_shortener"
        },
        {
            "name": "TinyURL Shortened Link",
            "url": "https://tinyurl.com/bank-verification-link",
            "expected_risk": "MEDIUM",
            "expected_sign": "url_shortener"
        },

        # 4. Embedded Credentials & Userinfo (Expected: HIGH risk)
        {
            "name": "Embedded Userinfo (@ symbol deception)",
            "url": "http://admin:secret@chase-portal.com/login",
            "expected_risk": "HIGH",
            "expected_sign": "embedded_credentials"
        },
        {
            "name": "Spoofed Authority with @ Redirect",
            "url": "http://paypal.com@verification-auth-portal.com",
            "expected_risk": "HIGH",
            "expected_sign": "embedded_credentials"
        },

        # 5. Punycode IDN Homograph Attack (Expected: HIGH risk)
        {
            "name": "Punycode Homograph Domain (e.g. Cyrillic lookalike)",
            "url": "http://xn--pple-43d.com/support/login",
            "expected_risk": "HIGH",
            "expected_sign": "punycode_domain"
        },

        # 6. Brand Spoofing in Subdomains (Expected: HIGH risk)
        {
            "name": "PayPal Brand Spoof in Subdomain of Unrelated Domain",
            "url": "https://paypal.com.verify-billing-update.xyz/login",
            "expected_risk": "HIGH",
            "expected_sign": "subdomain_brand_spoof_paypal"
        },
        {
            "name": "Apple Brand Spoof in Deep Subdomain",
            "url": "https://apple.com.security-alert-center.net/portal",
            "expected_risk": "HIGH",
            "expected_sign": "subdomain_brand_spoof_apple"
        },

        # 7. Unusual Non-Standard Ports (Expected: MEDIUM or HIGH risk)
        {
            "name": "Non-Standard Port Target (:8443)",
            "url": "http://secure-banking-portal.com:8443/auth",
            "expected_risk": "MEDIUM",
            "expected_sign": "unusual_port"
        },

        # 8. Malformed & Dangerous Protocol Edge Cases
        {
            "name": "Dangerous JavaScript Protocol",
            "url": "javascript:alert('xss')",
            "expected_risk": "HIGH",
            "expected_sign": "dangerous_scheme"
        },
        {
            "name": "Empty Input String",
            "url": "",
            "expected_risk": "HIGH",
            "expected_sign": "empty_url"
        },
        {
            "name": "Missing Hostname",
            "url": "https://",
            "expected_risk": "HIGH",
            "expected_sign": "missing_hostname"
        },
        # 9. Legitimate Path with '@' Symbols (Social Media / Scoped Packages)
        {
            "name": "Medium User Profile with @ in Path",
            "url": "https://medium.com/@johndoe",
            "expected_risk": "LOW",
            "max_score": 0
        },
        {
            "name": "Twitter/X Profile with @ in Path",
            "url": "https://twitter.com/@support",
            "expected_risk": "LOW",
            "max_score": 0
        },
        {
            "name": "NPM Scoped Package with @ in Path",
            "url": "https://www.npmjs.com/package/@angular/core",
            "expected_risk": "LOW",
            "max_score": 0
        }
    ]

    passed_count = 0
    total_count = len(test_cases)

    for i, test in enumerate(test_cases, 1):
        name = test["name"]
        url = test["url"]
        exp_risk = test["expected_risk"]
        exp_sign = test.get("expected_sign")

        result = analyze_url_structure(url)
        risk = result.get("risk_category")
        score = result.get("structural_risk_score")
        signs = [s["id"] for s in result.get("warning_signs", [])]

        print(f"\n[TEST {i}/{total_count}] {name}")
        print(f"  Input:          {url}")
        print(f"  Risk Category:  {risk} (Expected: {exp_risk})")
        print(f"  Score:          {score}/100")
        print(f"  Warning Signs:  {signs}")

        # Assertions
        assert risk == exp_risk, f"FAILED: Expected risk {exp_risk}, got {risk}"
        if exp_sign:
            assert any(s.startswith(exp_sign) for s in signs), f"FAILED: Expected sign {exp_sign} in {signs}"
        if "max_score" in test:
            assert score <= test["max_score"], f"FAILED: Expected score <= {test['max_score']}, got {score}"

        # Verify disclaimer and safety recommendation exist
        assert "disclaimer" in result and len(result["disclaimer"]) > 0
        assert "recommendation" in result and len(result["recommendation"]) > 0
        assert "ML probability" not in json.dumps(result), "Failed: Found reference to ML probability"

        passed_count += 1
        print("  -> STATUS: PASS")

    print("\n" + "=" * 65)
    print(f"ALL {passed_count}/{total_count} URL SCANNER TESTS PASSED SUCCESSFULLY!")
    print("=" * 65)


if __name__ == "__main__":
    test_url_scanner()
