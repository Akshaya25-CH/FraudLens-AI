import ipaddress
import re
import urllib.parse
from typing import Any, Dict, List, Optional, Tuple

# Known URL shorteners that mask the true destination domain
KNOWN_SHORTENERS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd",
    "buff.ly", "adf.ly", "bit.do", "cutt.ly", "rebrand.ly", "shorturl.at",
    "tiny.cc", "rb.gy", "lnkd.in", "t2m.io", "qr.ae", "v.gd", "tr.im",
    "shorte.st", "clck.ru", "s.id", "soo.gd", "bc.vc", "bl.ink"
}

# High-risk / high-abuse TLDs frequently used for ephemeral phishing sites
HIGH_RISK_TLDS = {
    "xyz", "top", "club", "work", "click", "loan", "tk", "ml", "ga",
    "cf", "gq", "cam", "live", "support", "online", "vip", "buzz",
    "monster", "rest", "bar", "link", "gdn", "racing", "date", "icu"
}

# Brand and high-value target keywords frequently targeted by phishing campaigns
SENSITIVE_BRAND_KEYWORDS = {
    "paypal", "apple", "google", "microsoft", "netflix", "amazon",
    "facebook", "instagram", "whatsapp", "bankofamerica", "wellsfargo",
    "chase", "citibank", "sbi", "hdfc", "icici", "axis", "binance",
    "coinbase", "metamask", "steam", "discord", "dropbox", "outlook"
}

# Sensitive operational keywords that indicate security, credential, or payment flows
SECURITY_KEYWORDS = {
    "login", "signin", "sign-in", "log-in", "verify", "verification",
    "update", "account", "secure", "security", "wallet", "banking",
    "kyc", "authenticate", "confirm", "password", "credential", "otp",
    "invoice", "billing", "payment", "unlock", "suspended"
}


def is_ip_address(hostname: str) -> bool:
    """Checks whether the hostname is an IPv4 or IPv6 address."""
    clean_host = hostname.strip("[]")
    try:
        ipaddress.ip_address(clean_host)
        return True
    except ValueError:
        pass

    # Check for hex or decimal encoded IPv4 formats (e.g. 0x7f000001 or 2130706433)
    if re.fullmatch(r"0x[0-9a-fA-F]+", clean_host) or (clean_host.isdigit() and len(clean_host) >= 8):
        return True

    return False


def extract_domain_parts(hostname: str) -> Tuple[str, List[str], str]:
    """
    Extracts root domain, subdomains, and top-level domain from hostname.
    Returns (root_domain, subdomains, tld).
    """
    clean_host = hostname.lower().strip(".")
    if not clean_host or is_ip_address(clean_host):
        return clean_host, [], ""

    parts = clean_host.split(".")
    if len(parts) < 2:
        return clean_host, [], ""

    # Common two-part TLDs (e.g., co.uk, com.au, co.in)
    two_part_tlds = {"co.uk", "org.uk", "ac.uk", "gov.uk", "co.in", "net.in", "org.in", "com.au", "net.au"}
    potential_two_part = ".".join(parts[-2:])

    if len(parts) >= 3 and potential_two_part in two_part_tlds:
        tld = potential_two_part
        root_domain = f"{parts[-3]}.{tld}"
        subdomains = parts[:-3]
    else:
        tld = parts[-1]
        root_domain = f"{parts[-2]}.{tld}"
        subdomains = parts[:-2]

    return root_domain, subdomains, tld


def analyze_url_structure(raw_url: str) -> Dict[str, Any]:
    """
    Performs comprehensive, explainable structural analysis on a given URL
    WITHOUT making any outbound network requests or DNS resolutions.
    """
    url_str = raw_url.strip() if raw_url else ""

    if not url_str:
        return {
            "error": "URL cannot be empty.",
            "is_valid": False,
            "risk_category": "HIGH",
            "structural_risk_score": 100,
            "warning_signs": [{
                "id": "empty_url",
                "title": "Empty URL Input",
                "severity": "HIGH",
                "points": 100,
                "description": "No URL was provided for analysis."
            }],
            "recommendation": "Provide a valid URL to analyze.",
            "disclaimer": "Structural risk scoring relies strictly on lexical and syntactic analysis."
        }

    # Detect dangerous non-web schemes before normalization
    lower_raw = url_str.lower()
    dangerous_schemes = ("javascript:", "data:", "file:", "vbscript:")
    for d_scheme in dangerous_schemes:
        if lower_raw.startswith(d_scheme):
            return {
                "url": url_str,
                "is_valid": True,
                "risk_category": "HIGH",
                "structural_risk_score": 95,
                "is_suspicious": True,
                "warning_signs": [{
                    "id": "dangerous_scheme",
                    "title": f"Dangerous Pseudo-Protocol ({d_scheme})",
                    "severity": "HIGH",
                    "points": 95,
                    "description": f"The URL uses a dangerous URI scheme '{d_scheme}' frequently used in cross-site scripting (XSS) and client-side execution exploits."
                }],
                "structural_features": {
                    "scheme": d_scheme.rstrip(":"),
                    "hostname": "",
                    "port": None,
                    "path": url_str[len(d_scheme):],
                    "url_length": len(url_str)
                },
                "recommendation": "Do not execute or load this URL. Dangerous protocol schemes can execute unauthorized code directly in the browser.",
                "disclaimer": "Structural risk scoring evaluates static URL properties without making network requests."
            }

    # Normalize scheme for parsing
    if "://" not in url_str:
        # Prepend http:// for parsing if scheme is omitted
        normalized_url = "http://" + url_str
    else:
        normalized_url = url_str

    try:
        parsed = urllib.parse.urlsplit(normalized_url)
    except Exception as e:
        return {
            "error": f"Malformed URL syntax: {str(e)}",
            "is_valid": False,
            "risk_category": "HIGH",
            "structural_risk_score": 85,
            "warning_signs": [{
                "id": "malformed_syntax",
                "title": "Malformed URL Syntax",
                "severity": "HIGH",
                "points": 85,
                "description": "The URL cannot be parsed by standard URL specification RFC 3986."
            }],
            "recommendation": "Do not open this link. Malformed URLs often attempt parser confusion attacks.",
            "disclaimer": "Structural analysis is performed statically without network traffic."
        }

    scheme = parsed.scheme.lower()
    netloc = parsed.netloc
    hostname = (parsed.hostname or "").lower()
    port = parsed.port
    path = parsed.path or "/"
    query = parsed.query

    # Validate that we extracted a hostname
    if not hostname:
        return {
            "error": "Invalid URL: Missing hostname or domain authority.",
            "is_valid": False,
            "risk_category": "HIGH",
            "structural_risk_score": 80,
            "warning_signs": [{
                "id": "missing_hostname",
                "title": "Missing Hostname",
                "severity": "HIGH",
                "points": 80,
                "description": "The URL does not specify a valid domain name or network host."
            }],
            "recommendation": "Verify the URL. Incomplete or invalid URL formats cannot be safely resolved.",
            "disclaimer": "Analysis is conducted strictly through static lexical parsing."
        }

    root_domain, subdomains, tld = extract_domain_parts(hostname)

    warning_signs: List[Dict[str, Any]] = []
    score = 0

    # -----------------------------------------------------------------------
    # Rule 1: IP Address Instead of Registered Domain Name
    # -----------------------------------------------------------------------
    has_ip = is_ip_address(hostname)
    if has_ip:
        pts = 40
        score += pts
        warning_signs.append({
            "id": "ip_hostname",
            "title": "Direct IP Address Hostname",
            "severity": "HIGH",
            "points": pts,
            "description": f"The URL points directly to an IP address ({hostname}) rather than a registered domain name. Legitimate organizations rarely use bare IP addresses for client-facing links."
        })

    # -----------------------------------------------------------------------
    # Rule 2: Embedded Credentials / Userinfo (e.g. user:pass@domain or admin@)
    # -----------------------------------------------------------------------
    has_credentials = bool(parsed.username or parsed.password or ("@" in parsed.netloc))
    if has_credentials:
        pts = 35
        score += pts
        warning_signs.append({
            "id": "embedded_credentials",
            "title": "Embedded Credentials or Userinfo ('@' Symbol)",
            "severity": "HIGH",
            "points": pts,
            "description": "The URL contains an '@' delimiter in the authority component. Browsers ignore everything before '@' and route to the host that follows, a classic tactic to mislead users about the actual destination."
        })

    # -----------------------------------------------------------------------
    # Rule 3: Punycode / IDN Homograph Attack (xn--)
    # -----------------------------------------------------------------------
    is_punycode = "xn--" in hostname
    if is_punycode:
        pts = 35
        score += pts
        warning_signs.append({
            "id": "punycode_domain",
            "title": "Punycode Encoded Domain (IDN Homograph)",
            "severity": "HIGH",
            "points": pts,
            "description": f"The domain uses Punycode encoding ('{hostname}'). Attackers frequently use international characters that visually mimic standard Latin characters (e.g. Cyrillic 'а' for Latin 'a') to spoof trusted domains."
        })

    # -----------------------------------------------------------------------
    # Rule 4: Known URL Shorteners
    # -----------------------------------------------------------------------
    is_shortener = hostname in KNOWN_SHORTENERS or root_domain in KNOWN_SHORTENERS
    if is_shortener:
        pts = 25
        score += pts
        warning_signs.append({
            "id": "url_shortener",
            "title": "Known URL Shortening Service",
            "severity": "MEDIUM",
            "points": pts,
            "description": f"The domain '{hostname}' is a known URL shortener that conceals the true destination server. Phishing messages commonly use shorteners to evade automated link filters."
        })

    # -----------------------------------------------------------------------
    # Rule 5: Unusual Non-Standard Ports
    # -----------------------------------------------------------------------
    has_unusual_port = False
    if port is not None and port not in (80, 443):
        has_unusual_port = True
        pts = 25
        score += pts
        warning_signs.append({
            "id": "unusual_port",
            "title": f"Non-Standard Port (:{port})",
            "severity": "MEDIUM",
            "points": pts,
            "description": f"The URL targets a non-standard network port (:{port}) instead of standard web ports (80 for HTTP or 443 for HTTPS). Phishing campaigns often deploy rogue servers on arbitrary open ports."
        })

    # -----------------------------------------------------------------------
    # Rule 6: Brand Impersonation in Subdomains or Path
    # -----------------------------------------------------------------------
    full_subdomain_str = ".".join(subdomains).lower()
    for brand in SENSITIVE_BRAND_KEYWORDS:
        # If brand keyword is in subdomain, but root_domain is NOT that brand's official domain
        if brand in full_subdomain_str and brand not in root_domain:
            pts = 35
            score += pts
            warning_signs.append({
                "id": f"subdomain_brand_spoof_{brand}",
                "title": f"Target Brand Spoofing in Subdomain ({brand})",
                "severity": "HIGH",
                "points": pts,
                "description": f"The brand name '{brand}' appears inside the subdomain structure ('{full_subdomain_str}'), but the actual registered root domain is '{root_domain}'. This is a high-confidence indicator of brand impersonation."
            })
            break  # Flag once for brand impersonation

    # -----------------------------------------------------------------------
    # Rule 7: Excessive Subdomain Depth
    # -----------------------------------------------------------------------
    subdomain_count = len(subdomains)
    if subdomain_count >= 3:
        pts = 15
        score += pts
        warning_signs.append({
            "id": "excessive_subdomains",
            "title": f"Excessive Subdomain Depth ({subdomain_count} Subdomains)",
            "severity": "MEDIUM",
            "points": pts,
            "description": f"The hostname contains {subdomain_count} nested subdomain levels ('{full_subdomain_str}'). Phishing toolkits often stack subdomains to push the true root domain out of view on mobile screens."
        })

    # -----------------------------------------------------------------------
    # Rule 8: Hyphens and Obfuscation in Domain Name
    # -----------------------------------------------------------------------
    hyphen_count = hostname.count("-")
    if hyphen_count >= 2:
        pts = 20
        score += pts
        warning_signs.append({
            "id": "multiple_hyphens",
            "title": f"Multiple Hyphens in Hostname ({hyphen_count} Hyphens)",
            "severity": "MEDIUM",
            "points": pts,
            "description": f"The domain contains {hyphen_count} hyphens ('{hostname}'). Fraudulent lookalike domains often concatenate hyphenated security and service keywords (e.g. 'secure-login-account.com')."
        })
    elif hyphen_count == 1:
        # Check if the hyphen connects a brand or security keyword
        for kw in SENSITIVE_BRAND_KEYWORDS.union(SECURITY_KEYWORDS):
            if kw in hostname and kw != root_domain.split(".")[0]:
                pts = 10
                score += pts
                warning_signs.append({
                    "id": "hyphenated_keyword",
                    "title": f"Hyphenated Sensitive Keyword ('{kw}')",
                    "severity": "LOW",
                    "points": pts,
                    "description": f"The domain uses a hyphen combined with sensitive term '{kw}', a known pattern in domain squatting."
                })
                break

    # -----------------------------------------------------------------------
    # Rule 9: High-Risk / High-Abuse TLD Combined with Sensitive Keywords
    # -----------------------------------------------------------------------
    if tld in HIGH_RISK_TLDS:
        # Check if URL contains sensitive security or brand keywords
        has_sensitive_term = any(
            term in path.lower() or term in full_subdomain_str or term in query.lower()
            for term in SECURITY_KEYWORDS.union(SENSITIVE_BRAND_KEYWORDS)
        )
        if has_sensitive_term:
            pts = 25
            score += pts
            warning_signs.append({
                "id": "risky_tld_sensitive_keywords",
                "title": f"High-Abuse TLD (.{tld}) with Sensitive Credentials",
                "severity": "HIGH",
                "points": pts,
                "description": f"The domain uses a high-abuse top-level domain (.{tld}) combined with credential or financial keywords in the path/subdomain. Such TLDs are frequently provisioned for short-lived phishing sites."
            })
        else:
            pts = 10
            score += pts
            warning_signs.append({
                "id": "risky_tld",
                "title": f"Uncommon High-Abuse TLD (.{tld})",
                "severity": "LOW",
                "points": pts,
                "description": f"The domain uses the top-level domain '.{tld}', which is statistically associated with higher volumes of disposable spam and phishing domains."
            })

    # -----------------------------------------------------------------------
    # Rule 10: Suspicious Path Patterns (Double Slashes, Redirect Parameters)
    # -----------------------------------------------------------------------
    if "//" in path:
        pts = 15
        score += pts
        warning_signs.append({
            "id": "double_slash_path",
            "title": "Double Slashes in URL Path ('//')",
            "severity": "MEDIUM",
            "points": pts,
            "description": "The URL path contains multiple consecutive slashes ('//'). Attackers frequently use double slashes to cause URL parser confusion and bypass path-based security filters."
        })

    # Check for open redirect patterns in query parameters (e.g. ?url=http... or ?dest=...)
    redirect_match = re.search(r"[?&](?:redirect|url|dest|goto|next|target|link)=https?%3A%2F%2F|[?&](?:redirect|url|dest|goto|next|target|link)=https?://", url_str, re.IGNORECASE)
    if redirect_match:
        pts = 20
        score += pts
        warning_signs.append({
            "id": "open_redirect_parameter",
            "title": "Open Redirect Query Parameter",
            "severity": "MEDIUM",
            "points": pts,
            "description": "The URL query parameters contain an embedded destination address, typical of open-redirect vulnerabilities exploited to disguise malicious destinations."
        })

    # -----------------------------------------------------------------------
    # Rule 11: Insecure Plain HTTP with Sensitive Flow Keywords
    # -----------------------------------------------------------------------
    if scheme == "http" and not has_ip:
        sensitive_terms_found = [
            term for term in ("login", "signin", "bank", "password", "verify", "kyc", "otp", "checkout")
            if term in path.lower() or term in query.lower()
        ]
        if sensitive_terms_found:
            pts = 20
            score += pts
            warning_signs.append({
                "id": "insecure_http_sensitive",
                "title": "Unencrypted HTTP Scheme for Sensitive Action",
                "severity": "MEDIUM",
                "points": pts,
                "description": f"The URL uses unencrypted HTTP for an apparent sensitive workflow ({', '.join(sensitive_terms_found)}). Legitimate authentication and financial portals enforce HTTPS."
            })

    # -----------------------------------------------------------------------
    # Rule 12: Excessive URL Length
    # -----------------------------------------------------------------------
    url_len = len(url_str)
    if url_len > 120:
        pts = 15
        score += pts
        warning_signs.append({
            "id": "excessive_length",
            "title": f"Unusually Long URL ({url_len} Characters)",
            "severity": "LOW",
            "points": pts,
            "description": f"The URL contains {url_len} characters. Excessive length is often used to conceal malicious hostnames, tokens, or padding from mobile notification previews."
        })

    # Calculate final bounded score (0 to 100)
    final_score = min(100, max(0, score))

    # Determine explainable Risk Category
    has_high_severity_sign = any(w["severity"] == "HIGH" for w in warning_signs)
    if final_score >= 60 or (final_score >= 40 and has_high_severity_sign):
        risk_category = "HIGH"
        recommendation = (
            "DO NOT open this link or submit any credentials. This URL displays "
            "multiple high-confidence structural indicators of phishing, spoofing, or deceptive routing."
        )
    elif final_score >= 25 or warning_signs:
        risk_category = "MEDIUM"
        recommendation = (
            "Exercise caution before interacting with this link. Structural warning signals "
            "were detected. Verify the sender's identity through independent, official channels."
        )
    else:
        risk_category = "LOW"
        recommendation = (
            "No severe structural anomalies were detected in the URL syntax. However, structural "
            "inspection alone cannot verify server legitimacy or website content. Always confirm the domain before entering credentials."
        )

    return {
        "url": url_str,
        "is_valid": True,
        "risk_category": risk_category,
        "structural_risk_score": final_score,
        "is_suspicious": risk_category in ("HIGH", "MEDIUM"),
        "warning_signs": warning_signs,
        "warning_count": len(warning_signs),
        "structural_features": {
            "scheme": scheme,
            "hostname": hostname,
            "root_domain": root_domain,
            "subdomains": subdomains,
            "subdomain_count": subdomain_count,
            "tld": tld,
            "port": port,
            "path": path,
            "url_length": len(url_str),
            "has_ip_address": has_ip,
            "is_shortener": is_shortener,
            "is_punycode": is_punycode,
            "has_credentials": has_credentials,
            "has_unusual_port": has_unusual_port,
            "hyphen_count": hyphen_count
        },
        "recommendation": recommendation,
        "disclaimer": (
            "Structural risk scoring is an explainable heuristic analysis of URL syntax and lexical patterns. "
            "It does NOT make live network requests and does NOT claim the destination website is completely safe."
        )
    }
