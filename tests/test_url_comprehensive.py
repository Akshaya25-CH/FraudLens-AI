import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.main import scan_url, UrlScanRequest
from backend.url_scanner import analyze_url_structure
from fastapi import HTTPException

def test_url_comprehensive():
    print("=" * 70)
    print("FRAUDLENS AI - URL SCANNER COMPREHENSIVE REGRESSION AUDIT")
    print("=" * 70)

    test_urls = [
        ("Legitimate Google", "https://www.google.com", "LOW"),
        ("Legitimate GitHub", "https://github.com/fastapi/fastapi", "LOW"),
        ("Legitimate Apple", "https://www.apple.com/iphone", "LOW"),
        ("Legitimate PayPal", "https://www.paypal.com/signin", "LOW"),
        ("Legitimate Profile with @ in Path", "https://medium.com/@johndoe", "LOW"),
        ("Subdomain Brand Impersonation", "https://paypal.com.verify-billing-update.xyz/login", "HIGH"),
        ("Direct IP Address", "http://192.168.1.100/admin/bank-login", "HIGH"),
        ("Known URL Shortener", "https://bit.ly/3xY7zQ", "MEDIUM"),
        ("Punycode Homograph", "http://xn--pple-43d.com/support/login", "HIGH"),
        ("Embedded Userinfo Credentials", "http://admin:secret@chase-portal.com/login", "HIGH"),
        ("Open Redirect Parameter", "http://192.168.1.1/admin/login?dest=http://evil.com", "HIGH"),
        ("Non-standard Port", "http://secure-banking-portal.com:8443/auth", "MEDIUM"),
        ("Extremely Long URL (2,000 chars)", "https://legitimate-looking-site.com/portal/login?" + "padding=" * 200, "MEDIUM"),
        ("Malformed Missing Scheme & Host", "https://", "HIGH"),
        ("Whitespace only", "    \n\t  ", "HTTPException_400"),
        ("Empty string", "", "HTTPException_400"),
    ]

    all_passed = True
    for cat, url_str, expected in test_urls:
        print(f"\n--- Testing [{cat}] ---")
        preview = (url_str[:65] + "...") if len(url_str) > 65 else url_str
        print(f"URL: {preview!r}")

        if expected == "HTTPException_400":
            try:
                req = UrlScanRequest(url=url_str)
                scan_url(req)
                print("  [FAIL] Expected HTTPException 400, but succeeded!")
                all_passed = False
            except HTTPException as e:
                print(f"  [PASS] Correctly raised HTTPException: {e.status_code} - {e.detail}")
        else:
            try:
                req = UrlScanRequest(url=url_str)
                res = scan_url(req)
                risk = res["risk_category"]
                score = res["structural_risk_score"]
                signs = [s["id"] for s in res.get("warning_signs", [])]
                print(f"  Result -> Risk: {risk}, Score: {score}/100, Signs: {signs}")
                print(f"  Recommendation: {res['recommendation'][:65]}...")
                if risk == expected:
                    print(f"  [PASS] Risk {risk} matches expected {expected}")
                else:
                    print(f"  [FAIL] Risk {risk} DOES NOT match expected {expected}!")
                    all_passed = False
            except Exception as e:
                print(f"  [FAIL] Crashed with exception: {e}")
                all_passed = False

    print("\n" + "=" * 70)
    assert all_passed, "Some URL comprehensive tests failed!"
    print("ALL URL COMPREHENSIVE TESTS EXECUTED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    test_url_comprehensive()
