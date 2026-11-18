import re
from collections import Counter, defaultdict
import pandas as pd

def run_audit():
    df = pd.read_csv("datasets/training/indian_sms_train.csv")
    print(f"Loaded {len(df)} rows.")

    # ---------------------------------------------------------
    # 1. PHONE NUMBERS & PERSONAL DATA
    # ---------------------------------------------------------
    phone_pattern = re.compile(r'\b[6-9]\d{9}\b')
    tollfree_pattern = re.compile(r'\b1800\d{6,7}\b')
    account_pattern = re.compile(r'(?:A/C|A/c|account|खाता|खता)\s*(?:ending\s*)?(?:with\s*)?(?:XX|\*+)?\d+', re.IGNORECASE)
    card_pattern = re.compile(r'(?:Card|कार्ड)\s*(?:ending\s*)?(?:XX|\*+)?\d+', re.IGNORECASE)
    vehicle_pattern = re.compile(r'\b[A-Z]{2}\d{2}[A-Z]{1,2}\d{4}\b')
    person_names = ["Ramesh", "Priya", "Ananya", "Suresh", "Vijay", "Deepak", "Akash", "Imran", "Rajesh", "Rahul", "Santosh", "Sandeep", "Amit", "Sneha", "Pooja", "हरीश"]
    
    phone_matches = []
    tollfree_matches = []
    account_matches = []
    card_matches = []
    vehicle_matches = []
    name_matches = []

    for idx, row in df.iterrows():
        msg = row["message"]
        m_id = row["id"]
        
        # Phone
        phones = phone_pattern.findall(msg)
        if phones:
            phone_matches.append((m_id, row["label"], row["category"], phones, msg))
            
        # Toll-free
        tfs = tollfree_pattern.findall(msg)
        if tfs:
            tollfree_matches.append((m_id, row["label"], row["category"], tfs, msg))
            
        # Account
        accs = account_pattern.findall(msg)
        if accs:
            account_matches.append((m_id, row["label"], row["category"], accs))
            
        # Card
        cards = card_pattern.findall(msg)
        if cards:
            card_matches.append((m_id, row["label"], row["category"], cards))
            
        # Vehicle
        vehs = vehicle_pattern.findall(msg)
        if vehs:
            vehicle_matches.append((m_id, row["label"], row["category"], vehs))
            
        # Names
        found_names = [n for n in person_names if n in msg]
        if found_names:
            name_matches.append((m_id, row["label"], row["category"], found_names, msg))

    print(f"\n--- 1. Personal & Sensitive Identifiers ---")
    print(f"Messages with 10-digit phone numbers: {len(phone_matches)}")
    print(f"Messages with toll-free numbers: {len(tollfree_matches)}")
    print(f"Messages with Account numbers: {len(account_matches)}")
    print(f"Messages with Card references: {len(card_matches)}")
    print(f"Messages with Vehicle numbers: {len(vehicle_matches)}")
    print(f"Messages with Person names: {len(name_matches)}")

    # ---------------------------------------------------------
    # 2. TEMPLATE DIVERSITY
    # ---------------------------------------------------------
    banks = ["SBI", "HDFC", "ICICI", "Axis", "Kotak", "PNB", "Bank of Baroda", "Canara Bank", "Union Bank", 
             "IndusInd", "Federal Bank", "IDFC First Bank", "IDFC FIRST Bank", "Bank of India", "Central Bank", 
             "Yes Bank", "Paytm", "Standard Chartered", "PhonePe", "Google Pay", "BHIM", "Amazon", "Flipkart"]
    
    def abstract_template(text):
        t = text
        # Replace URLs
        t = re.sub(r'https?://\S+', '<URL>', t)
        # Replace 10-digit phones
        t = re.sub(r'\b[6-9]\d{9}\b', '<PHONE>', t)
        # Replace toll free
        t = re.sub(r'\b1800\d{6,7}\b', '<TOLLFREE>', t)
        # Replace vehicle numbers
        t = re.sub(r'\b[A-Z]{2}\d{2}[A-Z]{1,2}\d{4}\b', '<VEHICLE>', t)
        # Replace amounts
        t = re.sub(r'(?:Rs\.?|INR|रु|रुपये)\s*[\d,]+(?:\.\d{2})?', '<AMT>', t, flags=re.IGNORECASE)
        # Replace account/card numbers
        t = re.sub(r'(?:XX|\*+)?\d{4,}', '<NUM_ID>', t)
        # Replace isolated digits
        t = re.sub(r'\b\d+\b', '<NUM>', t)
        # Replace bank/brand names
        for b in sorted(banks, key=len, reverse=True):
            t = re.sub(re.escape(b), '<BRAND>', t, flags=re.IGNORECASE)
        # Clean whitespace and lowercase
        t = re.sub(r'\s+', ' ', t).strip().lower()
        return t

    scam_templates = Counter()
    legit_templates = Counter()
    scam_template_map = defaultdict(list)
    legit_template_map = defaultdict(list)

    for idx, row in df.iterrows():
        tpl = abstract_template(row["message"])
        if row["label"] == 1:
            scam_templates[tpl] += 1
            scam_template_map[tpl].append(row["id"])
        else:
            legit_templates[tpl] += 1
            legit_template_map[tpl].append(row["id"])

    print(f"\n--- 2. Template Diversity ---")
    print(f"Scam total: 220, Unique templates: {len(scam_templates)} ({len(scam_templates)/220*100:.1f}%)")
    print(f"Legit total: 220, Unique templates: {len(legit_templates)} ({len(legit_templates)/220*100:.1f}%)")
    
    repetitive_scam = {k: v for k, v in scam_templates.items() if v > 1}
    repetitive_legit = {k: v for k, v in legit_templates.items() if v > 1}
    print(f"Scam templates appearing >1 time: {len(repetitive_scam)}")
    print(f"Legit templates appearing >1 time: {len(repetitive_legit)}")

    # ---------------------------------------------------------
    # 3. CLASSIFICATION SHORTCUTS (Spurious Correlations)
    # ---------------------------------------------------------
    url_pattern = re.compile(r'https?://\S+')
    urgency_pattern = re.compile(r'\b(immediately|urgent|urgently|today|tonight|within 24|24 hours|blocked|suspended|deactivated|expire|expired|cutoff|disconnect|disconnected|hold|summons|warrant|turant|aaj|raat|band|freeze|rok|samapt|अति आवश्यक|तुरंत|आज|रात|बंद|काट|रोक|निलंबित|निष्क्रिय|चेतावनी)\b', re.IGNORECASE)
    disclaimer_pattern = re.compile(r'\b(never share|do not share|confidential|valid for|bank never asks|bank staff will never|do not disclose|kisi ko na|kisi ke sath share na|kisi ko na bataye|साझा न करें|किसी को न बताएं|गोपनीय|साझा न)\b', re.IGNORECASE)
    amount_pattern = re.compile(r'(?:Rs\.?|INR|रु|रुपये)\s*[\d,]+', re.IGNORECASE)
    
    scam_df = df[df["label"] == 1]
    legit_df = df[df["label"] == 0]

    scam_url_count = sum(bool(url_pattern.search(m)) for m in scam_df["message"])
    legit_url_count = sum(bool(url_pattern.search(m)) for m in legit_df["message"])

    scam_urgency_count = sum(bool(urgency_pattern.search(m)) for m in scam_df["message"])
    legit_urgency_count = sum(bool(urgency_pattern.search(m)) for m in legit_df["message"])

    scam_disclaimer_count = sum(bool(disclaimer_pattern.search(m)) for m in scam_df["message"])
    legit_disclaimer_count = sum(bool(disclaimer_pattern.search(m)) for m in legit_df["message"])

    scam_amount_count = sum(bool(amount_pattern.search(m)) for m in scam_df["message"])
    legit_amount_count = sum(bool(amount_pattern.search(m)) for m in legit_df["message"])

    print(f"\n--- 3. Shortcut / Feature Disproportion Analysis ---")
    print(f"URLs in Scam: {scam_url_count}/220 ({scam_url_count/220*100:.1f}%) | Legit: {legit_url_count}/220 ({legit_url_count/220*100:.1f}%)")
    print(f"Urgency in Scam: {scam_urgency_count}/220 ({scam_urgency_count/220*100:.1f}%) | Legit: {legit_urgency_count}/220 ({legit_urgency_count/220*100:.1f}%)")
    print(f"Disclaimers in Scam: {scam_disclaimer_count}/220 ({scam_disclaimer_count/220*100:.1f}%) | Legit: {legit_disclaimer_count}/220 ({legit_disclaimer_count/220*100:.1f}%)")
    print(f"Amounts in Scam: {scam_amount_count}/220 ({scam_amount_count/220*100:.1f}%) | Legit: {legit_amount_count}/220 ({legit_amount_count/220*100:.1f}%)")

    # ---------------------------------------------------------
    # 4. LANGUAGE AUTHENTICITY
    # ---------------------------------------------------------
    hinglish_words = ["aapka", "aapke", "aapki", "hai", "hain", "kare", "karna", "kiye", "hoga", "hogi", "liye", 
                      "se", "ko", "par", "me", "pe", "turant", "paisa", "paise", "khata", "khate", "bina", "raha", 
                      "rahi", "gaya", "gayi", "kisi", "kuch", "shuru", "aaj", "raat", "bachane", "sath", "bataye"]
    
    hinglish_df = df[df["language"] == "Hinglish"]
    weak_hinglish = []
    for idx, row in hinglish_df.iterrows():
        tokens = set(re.findall(r'[a-zA-Z]+', row["message"].lower()))
        matches = [w for w in hinglish_words if w in tokens]
        if len(matches) < 2:
            weak_hinglish.append((row["id"], row["label"], row["category"], len(matches), row["message"]))

    devanagari_df = df[df["language"] == "Hindi_Devanagari"]
    dev_regex = re.compile(r'[\u0900-\u097F]')
    weak_devanagari = []
    for idx, row in devanagari_df.iterrows():
        dev_chars = len(dev_regex.findall(row["message"]))
        total_chars = len(row["message"].replace(" ", ""))
        ratio = dev_chars / total_chars if total_chars > 0 else 0
        if ratio < 0.40:
            weak_devanagari.append((row["id"], row["label"], ratio, row["message"]))

    print(f"\n--- 4. Language Authenticity ---")
    print(f"Hinglish messages checked: {len(hinglish_df)}")
    print(f"Hinglish messages with <2 common Hindi marker words: {len(weak_hinglish)}")
    print(f"Devanagari messages checked: {len(devanagari_df)}")
    print(f"Devanagari messages with <40% Devanagari characters: {len(weak_devanagari)}")

    # ---------------------------------------------------------
    # 5. LABEL QUALITY & AMBIGUITY
    # ---------------------------------------------------------
    # Ambiguous legit: legit messages containing words that look like scam threats
    ambiguous_legit = []
    for idx, row in legit_df.iterrows():
        msg_l = row["message"].lower()
        if "block" in msg_l or "suspend" in msg_l or "deactivate" in msg_l or "dispute" in msg_l:
            ambiguous_legit.append((row["id"], row["category"], row["language"], row["message"]))
            
    # Weak scam: scam messages without clear call-to-action or suspicious hook
    scam_hooks = ["http", "call", "whatsapp", "telegram", "pin", "otp", "click", "pay", "fee", "summons", "warrant", "संपर्क", "क्लिक", "कॉल"]
    weak_scams = []
    for idx, row in scam_df.iterrows():
        msg_l = row["message"].lower()
        if not any(h in msg_l for h in scam_hooks):
            weak_scams.append((row["id"], row["category"], row["language"], row["message"]))

    print(f"\n--- 5. Label Quality & Edge Cases ---")
    print(f"Legitimate messages with security/blocking keywords (potential false alarm triggers): {len(ambiguous_legit)}")
    print(f"Scam messages without obvious hook/action: {len(weak_scams)}")

    return {
        "phone_matches": phone_matches,
        "tollfree_matches": tollfree_matches,
        "account_matches": account_matches,
        "card_matches": card_matches,
        "vehicle_matches": vehicle_matches,
        "name_matches": name_matches,
        "scam_templates": scam_templates,
        "legit_templates": legit_templates,
        "repetitive_scam": repetitive_scam,
        "repetitive_legit": repetitive_legit,
        "scam_url_count": scam_url_count,
        "legit_url_count": legit_url_count,
        "scam_urgency_count": scam_urgency_count,
        "legit_urgency_count": legit_urgency_count,
        "scam_disclaimer_count": scam_disclaimer_count,
        "legit_disclaimer_count": legit_disclaimer_count,
        "scam_amount_count": scam_amount_count,
        "legit_amount_count": legit_amount_count,
        "weak_hinglish": weak_hinglish,
        "weak_devanagari": weak_devanagari,
        "ambiguous_legit": ambiguous_legit,
        "weak_scams": weak_scams
    }

if __name__ == "__main__":
    run_audit()
