import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from starlette.middleware.cors import CORSMiddleware
from backend.main import app

def test_cors_middleware():
    print("=" * 65)
    print("FRAUDLENS AI - CORS ORIGIN & SECURITY VERIFICATION")
    print("=" * 65)

    # Find the CORSMiddleware in app.user_middleware
    cors_mw = None
    for mw in app.user_middleware:
        if mw.cls == CORSMiddleware:
            cors_mw = mw
            break

    assert cors_mw is not None, "CORSMiddleware is not registered on app!"
    print("\nFound CORSMiddleware registration:")
    print("  allow_origins:", cors_mw.kwargs.get("allow_origins"))
    print("  allow_origin_regex:", cors_mw.kwargs.get("allow_origin_regex"))
    print("  allow_credentials:", cors_mw.kwargs.get("allow_credentials"))

    # Instantiate the middleware with dummy ASGI app to test is_allowed_origin
    dummy_app = lambda scope, receive, send: None
    middleware_instance = CORSMiddleware(
        dummy_app,
        allow_origins=cors_mw.kwargs.get("allow_origins", ()),
        allow_origin_regex=cors_mw.kwargs.get("allow_origin_regex"),
        allow_credentials=cors_mw.kwargs.get("allow_credentials", False),
        allow_methods=cors_mw.kwargs.get("allow_methods", ("GET",)),
        allow_headers=cors_mw.kwargs.get("allow_headers", ()),
    )

    test_origins = [
        ("http://localhost:5173", True, "Default Vite dev port (localhost)"),
        ("http://127.0.0.1:5173", True, "Default Vite dev port (127.0.0.1)"),
        ("http://localhost:5174", True, "Fallback Vite dev port 5174 (localhost)"),
        ("http://127.0.0.1:5174", True, "Fallback Vite dev port 5174 (127.0.0.1)"),
        ("http://localhost:5175", True, "Fallback Vite dev port 5175 (localhost)"),
        ("http://127.0.0.1:5175", True, "Fallback Vite dev port 5175 (127.0.0.1)"),
        ("http://localhost:4173", True, "Vite production preview port (localhost)"),
        ("http://127.0.0.1:4173", True, "Vite production preview port (127.0.0.1)"),
        ("http://localhost:3000", True, "Standard dev port 3000 (localhost)"),
        ("http://127.0.0.1:3000", True, "Standard dev port 3000 (127.0.0.1)"),
        ("http://malicious-site.com", False, "External unauthorized domain"),
        ("http://evil-hacker.xyz:5174", False, "External domain using port 5174"),
        ("https://phishing-fraudlens.org", False, "External HTTPS phishing domain"),
    ]

    all_passed = True
    for origin, expected_allowed, desc in test_origins:
        is_allowed = middleware_instance.is_allowed_origin(origin)
        status = "PASS" if is_allowed == expected_allowed else "FAIL"
        if status == "FAIL":
            all_passed = False
        print(f"[{status}] Origin: {origin:<35} Allowed: {is_allowed!s:<5} (Expected: {expected_allowed!s:<5}) -> {desc}")

    print("\n" + "=" * 65)
    assert all_passed, "Some CORS origin verification tests failed!"
    print("ALL CORS ORIGIN VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 65)

if __name__ == "__main__":
    test_cors_middleware()
