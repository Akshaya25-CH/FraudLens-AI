import re
from typing import Any, Dict, List, Optional, Tuple

# Known NPCI / PSP Bank UPI Handles frequently used in India
COMMON_UPI_HANDLES = {
    # Major PSPs & Tech Handles
    "okhdfcbank", "oksbi", "okaxis", "okicici", "ybl", "ibl", "axl",
    "paytm", "upi", "apl", "rapl", "waaxis", "wahdfcbank", "wasbi", "waicici",
    "gpay", "freecharge", "airtel", "amazonpay", "fbl", "jupiteraxis",
    # Public & Private Banks
    "barodampay", "idfcbank", "federal", "postbank", "pnb", "cnrb",
    "unionbank", "uboi", "mahb", "indus", "kotak", "kbl", "sib",
    "yesbank", "rbl", "equitas", "aufin", "dbs", "bandhan", "sc"
}

# Suspicious keywords in the username part of a UPI ID (spoofing support or banking services)
SUSPICIOUS_VPA_KEYWORDS = {
    "refund", "cashback", "support", "helpdesk", "care", "customercare",
    "kyc", "verification", "bonus", "winner", "prize", "lottery",
    "claim", "security", "official", "merchant-verify", "helpline"
}


def validate_upi_id_format(upi_id: str) -> Dict[str, Any]:
    """
    Validates the lexical structure of an Indian UPI VPA (Virtual Payment Address).
    Does NOT connect to live NPCI databases or bank APIs. Explains formatting anomalies neutrally.
    """
    clean_vpa = (upi_id or "").strip().lower()

    if not clean_vpa:
        return {
            "vpa": "",
            "is_valid_format": False,
            "handle": None,
            "username": None,
            "is_known_handle": False,
            "has_suspicious_keywords": False,
            "observations": ["No UPI ID provided."]
        }

    # Standard format: username@handle (e.g., user@okhdfcbank or 9876543210@paytm)
    if "@" not in clean_vpa:
        return {
            "vpa": clean_vpa,
            "is_valid_format": False,
            "handle": None,
            "username": clean_vpa,
            "is_known_handle": False,
            "has_suspicious_keywords": False,
            "observations": [
                "Invalid UPI ID format: Missing '@' delimiter. A standard UPI VPA must contain exactly one '@' (e.g. username@handle)."
            ]
        }

    parts = clean_vpa.split("@")
    if len(parts) != 2:
        return {
            "vpa": clean_vpa,
            "is_valid_format": False,
            "handle": None,
            "username": None,
            "is_known_handle": False,
            "has_suspicious_keywords": False,
            "observations": ["Invalid UPI ID format: Multiple '@' symbols detected in address."]
        }

    username, handle = parts[0], parts[1]
    observations: List[str] = []

    syntax_valid = True
    # Check username syntax (alphanumeric, dot, hyphen, underscore)
    valid_username_regex = r"^[a-zA-Z0-9.\-_]{2,64}$"
    if not re.match(valid_username_regex, username):
        syntax_valid = False
        observations.append(
            f"Non-standard username syntax: '{username}' contains invalid characters or does not meet standard length (2-64 chars)."
        )

    # Check handle syntax (letters only, usually 2-30 chars)
    valid_handle_regex = r"^[a-zA-Z0-9]{2,32}$"
    if not re.match(valid_handle_regex, handle):
        syntax_valid = False
        observations.append(
            f"Non-standard handle syntax: '@{handle}' contains non-alphanumeric characters."
        )

    is_known_handle = handle in COMMON_UPI_HANDLES
    if is_known_handle:
        observations.append(f"Standard PSP / Bank Handle recognized: '@{handle}'.")
    else:
        observations.append(
            f"Uncommon / Private PSP Handle: '@{handle}' is not in the common list of consumer UPI handles. It may belong to a cooperative bank or custom merchant PSP."
        )

    # Check for keyword stuffing in username (e.g., sbi-helpdesk-refund@...)
    matched_suspicious_kws = [kw for kw in SUSPICIOUS_VPA_KEYWORDS if kw in username]
    has_suspicious_keywords = len(matched_suspicious_kws) > 0
    if has_suspicious_keywords:
        observations.append(
            f"Sensitive Service Keywords in Username: Username contains terms {matched_suspicious_kws}. Scammers frequently create VPAs mimicking official support desks (e.g. 'sbi-care-refund@ybl'). Legitimate banking support never receives payments via peer VPAs."
        )

    return {
        "vpa": clean_vpa,
        "is_valid_format": syntax_valid,
        "username": username,
        "handle": handle,
        "is_known_handle": is_known_handle,
        "has_suspicious_keywords": has_suspicious_keywords,
        "suspicious_keywords": matched_suspicious_kws,
        "observations": observations
    }


def extract_upi_ids(text: str) -> List[str]:
    """Extracts potential UPI VPAs from free-form text using regex."""
    vpa_pattern = r"\b[a-zA-Z0-9.\-_]{2,64}@[a-zA-Z0-9]{2,32}\b"
    matches = re.findall(vpa_pattern, text)
    # Deduplicate while preserving order
    seen = set()
    unique = []
    for m in matches:
        low = m.lower()
        if low not in seen and not low.endswith((".com", ".org", ".net", ".in", ".co")):
            seen.add(low)
            unique.append(m)
    return unique


def analyze_payment_fraud(text: str, specified_vpa: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyzes payment messages, transaction alerts, and UPI VPAs for fraudulent patterns
    using explainable rules. Does not initiate transactions or contact live payment gateways.
    """
    clean_text = (text or "").strip()
    lower_text = clean_text.lower()

    # Extract any UPI VPAs mentioned in the text or explicitly passed
    extracted_vpas = extract_upi_ids(clean_text)
    if specified_vpa and specified_vpa.strip():
        if specified_vpa.strip() not in extracted_vpas:
            extracted_vpas.insert(0, specified_vpa.strip())

    vpa_evaluations = [validate_upi_id_format(v) for v in extracted_vpas]

    warning_signs: List[Dict[str, Any]] = []
    score = 0

    if not clean_text and not specified_vpa:
        return {
            "error": "Input text or UPI ID cannot be empty.",
            "is_valid": False,
            "risk_category": "HIGH",
            "structural_risk_score": 100,
            "detected_patterns": ["empty_input"],
            "warning_signs": [{
                "id": "empty_input",
                "title": "Empty Input",
                "severity": "HIGH",
                "points": 100,
                "description": "No message content or UPI ID was supplied for analysis."
            }],
            "recommendation": "Provide message text or a UPI ID to analyze.",
            "disclaimer": "Analysis is performed offline via heuristic pattern rules."
        }

    # -----------------------------------------------------------------------
    # Pattern 1: Entering UPI PIN to Receive Money (CRITICAL GOLDEN RULE SCAM)
    # -----------------------------------------------------------------------
    pin_keywords = ["pin", "upi pin", "mpin", "security pin", "enter pin", "put pin"]
    receive_keywords = ["receive", "received", "credit", "credited", "accept", "claim", "collect", "deposit", "get money", "take payment"]

    has_pin = any(pk in lower_text for pk in pin_keywords)
    has_receive = any(rk in lower_text for rk in receive_keywords)

    # Explicit phrases matching the scam
    pin_receive_regex = r"(?:enter|put|type|share|provide|input).{0,25}(?:pin|mpin).{0,35}(?:receive|credit|claim|get|collect|accept)"
    receive_pin_regex = r"(?:receive|credit|claim|get|accept|collect).{0,35}(?:enter|put|type|provide|input).{0,25}(?:pin|mpin)"

    if re.search(pin_receive_regex, lower_text) or re.search(receive_pin_regex, lower_text) or (has_pin and has_receive and ("enter" in lower_text or "put" in lower_text or "type" in lower_text)):
        pts = 45
        score += pts
        warning_signs.append({
            "id": "pin_to_receive_scam",
            "title": "UPI Golden Rule Violation: PIN Prompted to Receive Money",
            "severity": "HIGH",
            "points": pts,
            "description": "The message instructs you to enter a UPI PIN to receive or claim funds. UNDER THE UPI PROTOCOL, YOU NEVER NEED TO ENTER A UPI PIN TO RECEIVE MONEY. Entering your UPI PIN will immediately DEBIT (deduct) money from your bank account."
        })

    # -----------------------------------------------------------------------
    # Pattern 2: Scanning a QR Code to Receive Money
    # -----------------------------------------------------------------------
    qr_keywords = ["qr", "qr code", "scanner", "barcode", "scan"]
    if any(qk in lower_text for qk in qr_keywords) and has_receive:
        qr_scam_regex = r"(?:scan|open).{0,25}(?:qr|code).{0,35}(?:receive|get|claim|credit|accept)"
        if re.search(qr_scam_regex, lower_text) or ("scan" in lower_text and ("receive" in lower_text or "get" in lower_text or "credit" in lower_text)):
            pts = 40
            score += pts
            warning_signs.append({
                "id": "qr_receive_scam",
                "title": "QR Code Scam: Request to Scan QR to Receive Funds",
                "severity": "HIGH",
                "points": pts,
                "description": "The message asks you to scan a QR code to receive, claim, or accept money. QR codes in UPI are strictly used to SEND money. Scanning a QR code generated by someone else will open a payment checkout screen to transfer your funds to them."
            })

    # -----------------------------------------------------------------------
    # Pattern 3: Collect Request / Reverse Payment Trap
    # -----------------------------------------------------------------------
    collect_keywords = [
        "collect request", "approve request", "accept request", "click pay to receive",
        "press pay to receive", "request money", "mandate approve", "autopay request"
    ]
    for ck in collect_keywords:
        if ck in lower_text:
            pts = 35
            score += pts
            warning_signs.append({
                "id": "collect_request_trap",
                "title": f"UPI Collect-Request Deception ('{ck}')",
                "severity": "HIGH",
                "points": pts,
                "description": f"The message refers to approving a collect request or clicking 'Pay' ({ck}). Fraudsters send payment collect requests disguised as credit approvals. Approving the request authorizes an outgoing debit from your account."
            })
            break

    # -----------------------------------------------------------------------
    # Pattern 4: Fake Cashback, Scratch Card, or Lottery Reward
    # -----------------------------------------------------------------------
    reward_keywords = [
        "cashback", "scratch card", "reward won", "bonus credited", "lottery",
        "prize money", "gift card won", "lucky draw", "gpay reward", "phonepe reward"
    ]
    matched_rewards = [rk for rk in reward_keywords if rk in lower_text]
    if matched_rewards:
        # Check if paired with urgency or claim instruction
        has_claim_action = any(a in lower_text for a in ["claim", "click", "open", "approve", "redeem", "won", "expire"])
        pts = 30 if has_claim_action else 15
        score += pts
        warning_signs.append({
            "id": "fake_cashback_reward",
            "title": f"Unsolicited Cashback or Reward Offer ({', '.join(matched_rewards)})",
            "severity": "HIGH" if has_claim_action else "MEDIUM",
            "points": pts,
            "description": f"The message promises unexpected rewards or cashback ({', '.join(matched_rewards)}). Official payment apps (PhonePe, Google Pay, Paytm) automatically credit legitimate rewards directly into your linked bank account without requiring approval links."
        })

    # -----------------------------------------------------------------------
    # Pattern 5: OTP, PIN, or Remote Access Screen-Sharing Harvesting
    # -----------------------------------------------------------------------
    otp_terms = ["otp", "one time password", "share code", "verification code", "card pin"]
    remote_access_apps = ["anydesk", "teamviewer", "quicksupport", "rustdesk", "airmirror", "screenshare"]

    has_otp_demand = any(ot in lower_text for ot in otp_terms) and any(v in lower_text for v in ["share", "send", "tell", "forward", "enter", "submit"])
    matched_remote = [ra for ra in remote_access_apps if ra in lower_text]

    if has_otp_demand:
        pts = 40
        score += pts
        warning_signs.append({
            "id": "otp_harvesting",
            "title": "Credential / OTP Harvesting Prompt",
            "severity": "HIGH",
            "points": pts,
            "description": "The message demands an OTP or verification code. Banking and UPI protocols strictly forbid sharing OTPs or PINs. Legitimate bank representatives will never request your OTP."
        })

    if matched_remote:
        pts = 45
        score += pts
        warning_signs.append({
            "id": "remote_access_tool",
            "title": f"Remote Screen-Sharing App Demanded ({', '.join(matched_remote)})",
            "severity": "HIGH",
            "points": pts,
            "description": f"The message instructs you to install or grant access to remote desktop software ({', '.join(matched_remote)}). Scammers use these tools to remotely view your phone screen, capture your UPI PIN, and drain bank accounts."
        })

    # -----------------------------------------------------------------------
    # Pattern 6: Urgent KYC / Account / UPI Deactivation Threat
    # -----------------------------------------------------------------------
    threat_terms = ["account blocked", "upi blocked", "kyc expired", "pan not linked", "sim blocked", "deactivation within", "suspended today", "bank blocked"]
    matched_threats = [tt for tt in threat_terms if tt in lower_text]
    if matched_threats:
        pts = 30
        score += pts
        warning_signs.append({
            "id": "account_suspension_threat",
            "title": f"Urgent Account Suspension Threat ({', '.join(matched_threats)})",
            "severity": "HIGH",
            "points": pts,
            "description": f"The message uses coercive urgency threatening imminent account termination ({', '.join(matched_threats)}). Banks and UPI operators never suspend accounts through SMS demand notices with third-party contact numbers."
        })

    # -----------------------------------------------------------------------
    # Pattern 7: Fake Payment Confirmation or "Accidental Transfer" Refund Scam
    # -----------------------------------------------------------------------
    accidental_refund_terms = ["by mistake", "sent mistakenly", "wrongly sent", "please return", "refund back", "send it back"]
    has_accidental_claim = any(at in lower_text for at in accidental_refund_terms)

    fake_credit_terms = ["credited successfully", "received rs", "payment received", "sent you rs", "has sent you"]
    has_fake_credit = any(fc in lower_text for fc in fake_credit_terms)

    if has_accidental_claim:
        pts = 30
        score += pts
        warning_signs.append({
            "id": "accidental_transfer_refund_scam",
            "title": "Fake Accidental Transfer Refund Scam",
            "severity": "HIGH",
            "points": pts,
            "description": "The sender claims to have sent money 'by mistake' and urgently asks you to send it back via UPI. Often, no money was ever sent (or a spoofed confirmation was forged). Always verify your actual bank balance in your official banking app first."
        })
    elif has_fake_credit and ("link" in lower_text or "click" in lower_text or "verify" in lower_text or "call" in lower_text):
        pts = 20
        score += pts
        warning_signs.append({
            "id": "suspicious_credit_confirmation",
            "title": "Suspicious Payment Confirmation with External Action Link",
            "severity": "MEDIUM",
            "points": pts,
            "description": "The message claims a payment was credited but instructs you to click a link or call an unverified phone number. Genuine bank credit SMS notifications are informational and do not require external verification clicks."
        })

    # -----------------------------------------------------------------------
    # Pattern 8: Suspicious VPA Heuristics
    # -----------------------------------------------------------------------
    for vpa_eval in vpa_evaluations:
        if vpa_eval.get("has_suspicious_keywords"):
            pts = 25
            score += pts
            warning_signs.append({
                "id": f"suspicious_vpa_{vpa_eval.get('username')}",
                "title": f"Deceptive Support Keyword in UPI VPA ('{vpa_eval.get('vpa')}')",
                "severity": "HIGH",
                "points": pts,
                "description": f"The UPI ID '{vpa_eval.get('vpa')}' uses service keywords ({vpa_eval.get('suspicious_keywords')}) in its username. Fraudsters configure VPAs mimicking official refund desks to make unauthorized payment requests appear legitimate."
            })

    # -----------------------------------------------------------------------
    # Pattern 9: High-Risk Phishing Hyperlink Inside Payment Message
    # -----------------------------------------------------------------------
    url_regex = r"https?://[^\s]+"
    urls_found = re.findall(url_regex, clean_text)
    if urls_found and (has_receive or has_pin or matched_threats or matched_rewards):
        pts = 20
        score += pts
        warning_signs.append({
            "id": "embedded_payment_link",
            "title": "Embedded Hyperlink in Payment Alert",
            "severity": "MEDIUM",
            "points": pts,
            "description": f"The payment alert contains embedded web links ({len(urls_found)} link(s)). Official bank transaction notifications do not direct users to third-party web forms to claim incoming funds."
        })

    # Bound final score between 0 and 100
    final_score = min(100, max(0, score))

    # Determine Risk Category
    has_high_severity = any(w["severity"] == "HIGH" for w in warning_signs)
    if final_score >= 50 or has_high_severity:
        risk_category = "HIGH"
        recommendation = (
            "CRITICAL WARNING: DO NOT proceed with this payment or enter your UPI PIN. "
            "Under UPI protocol, you NEVER enter a PIN to receive funds. Do not scan any QR codes or approve collect requests."
        )
    elif final_score >= 20 or warning_signs:
        risk_category = "MEDIUM"
        recommendation = (
            "EXERCISE CAUTION: This transaction notice contains suspicious patterns. "
            "Verify your bank statement directly inside your official bank app before taking any action. Never share OTPs."
        )
    else:
        risk_category = "LOW"
        recommendation = (
            "No prominent UPI fraud patterns were identified in the message text. "
            "However, rule-based heuristics cannot guarantee sender authenticity. Always verify the recipient VPA and amount before authorizing any outgoing payment."
        )

    return {
        "text": clean_text,
        "is_valid": True,
        "risk_category": risk_category,
        "structural_risk_score": final_score,
        "is_suspicious": risk_category in ("HIGH", "MEDIUM"),
        "warning_signs": warning_signs,
        "warning_count": len(warning_signs),
        "extracted_vpas": extracted_vpas,
        "vpa_evaluations": vpa_evaluations,
        "detected_patterns": [w["id"] for w in warning_signs],
        "recommendation": recommendation,
        "disclaimer": (
            "UPI fraud risk scoring is an explainable heuristic analysis of message syntax, payment semantics, and VPA formatting. "
            "It does NOT connect to live NPCI databases, does NOT verify bank account ownership, and NEVER initiates real financial transactions."
        )
    }
