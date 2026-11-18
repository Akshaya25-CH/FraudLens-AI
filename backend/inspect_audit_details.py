import re
import pandas as pd

df = pd.read_csv("datasets/training/indian_sms_train.csv")

# 1. Inspect the 4 Hinglish messages with <2 common marker words
hinglish_words = ["aapka", "aapke", "aapki", "hai", "hain", "kare", "karna", "kiye", "hoga", "hogi", "liye", 
                  "se", "ko", "par", "me", "pe", "turant", "paisa", "paise", "khata", "khate", "bina", "raha", 
                  "rahi", "gaya", "gayi", "kisi", "kuch", "shuru", "aaj", "raat", "bachane", "sath", "bataye"]

hinglish_df = df[df["language"] == "Hinglish"]
print("--- 4 Hinglish messages with <2 marker words ---")
for idx, row in hinglish_df.iterrows():
    tokens = set(re.findall(r'[a-zA-Z]+', row["message"].lower()))
    matches = [w for w in hinglish_words if w in tokens]
    if len(matches) < 2:
        print(f"ID {row['id']} [{row['category']}]: matches={matches}")
        print(f"  {row['message']}")

# 2. Inspect URLs and domains in Legit vs Scam
domain_pattern = re.compile(r'(?:https?://\S+|\b[\w-]+\.(?:com|org|net|gov\.in|nic\.in|test)\b)', re.IGNORECASE)
scam_domains = [row['id'] for _, row in df[df['label']==1].iterrows() if domain_pattern.search(row['message'])]
legit_domains = [row['id'] for _, row in df[df['label']==0].iterrows() if domain_pattern.search(row['message'])]
print(f"\nDomain / URL presence:")
print(f"Scam with domain/URL: {len(scam_domains)}/220 ({len(scam_domains)/220*100:.1f}%)")
print(f"Legit with domain/URL: {len(legit_domains)}/220 ({len(legit_domains)/220*100:.1f}%)")
print("Legit domain message examples:")
for lid in legit_domains[:5]:
    print(f"  ID {lid}: {df.loc[df['id']==lid, 'message'].values[0]}")

# 3. Inspect Ambiguous Legit messages
print("\n--- Ambiguous Legit messages ---")
for idx, row in df[df['label']==0].iterrows():
    msg_l = row["message"].lower()
    if any(k in msg_l for k in ["block", "suspend", "deactivate", "dispute"]):
        print(f"ID {row['id']} [{row['category']}, {row['language']}]: {row['message']}")

# 4. Inspect Scam messages without URLs
scam_no_url = df[(df['label']==1) & (~df['message'].str.contains('http'))]
print(f"\nScam messages without URLs: {len(scam_no_url)}")
for idx, row in scam_no_url.head(6).iterrows():
    print(f"ID {row['id']} [{row['category']}, {row['language']}]: {row['message']}")

# 5. Check phone numbers distribution (Scam vs Legit)
phone_pattern = re.compile(r'\b[6-9]\d{9}\b')
scam_phones = df[(df['label']==1) & (df['message'].str.contains(phone_pattern))]
legit_phones = df[(df['label']==0) & (df['message'].str.contains(phone_pattern))]
print(f"\n10-digit mobile numbers: Scam={len(scam_phones)}/220, Legit={len(legit_phones)}/220")
