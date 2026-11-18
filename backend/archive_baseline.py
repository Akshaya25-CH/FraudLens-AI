import hashlib
import json
import os
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "models" / "sms_model.joblib"
ARCHIVE_PATH = BASE_DIR / "models" / "sms_model_baseline.joblib"
CHECKSUM_FILE = BASE_DIR / "models" / "model_checksums.json"

def calculate_sha256(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest().upper()

def main():
    print("=" * 60)
    print("Step 5A: Baseline Archival Verification")
    print("=" * 60)

    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Original model not found at {MODEL_PATH}")

    orig_hash = calculate_sha256(MODEL_PATH)
    orig_stat = MODEL_PATH.stat()
    print(f"Original model: {MODEL_PATH.name}")
    print(f"  Size: {orig_stat.st_size} bytes")
    print(f"  SHA-256: {orig_hash}")

    if ARCHIVE_PATH.exists():
        print(f"\nArchive already exists at {ARCHIVE_PATH}. Verifying integrity...")
        arch_hash = calculate_sha256(ARCHIVE_PATH)
        arch_stat = ARCHIVE_PATH.stat()
        print(f"  Existing archive size: {arch_stat.st_size} bytes")
        print(f"  Existing archive SHA-256: {arch_hash}")
        assert orig_hash == arch_hash, "CRITICAL: Existing archive hash does NOT match original model hash!"
        print("[VERIFIED] Archive hash matches original model.")
    else:
        print(f"\nCreating byte-for-byte archive at: {ARCHIVE_PATH.name}...")
        shutil.copy2(MODEL_PATH, ARCHIVE_PATH)
        arch_hash = calculate_sha256(ARCHIVE_PATH)
        arch_stat = ARCHIVE_PATH.stat()
        print(f"  Archived file size: {arch_stat.st_size} bytes")
        print(f"  Archived SHA-256:   {arch_hash}")
        assert orig_hash == arch_hash, "CRITICAL: Copied archive hash does not match original!"
        assert orig_stat.st_size == arch_stat.st_size, "CRITICAL: File size mismatch!"
        print("[SUCCESS] Byte-for-byte preservation verified.")

    # Record in model_checksums.json
    checksum_data = {
        "sms_model_original": {
            "path": "models/sms_model.joblib",
            "sha256": orig_hash,
            "size_bytes": orig_stat.st_size,
            "status": "active_baseline"
        },
        "sms_model_baseline_archive": {
            "path": "models/sms_model_baseline.joblib",
            "sha256": arch_hash,
            "size_bytes": arch_stat.st_size,
            "status": "archived_immutable_copy"
        },
        "verification": {
            "byte_for_byte_identical": (orig_hash == arch_hash),
            "timestamp": "2026-11-15T12:05:00"
        }
    }

    with open(CHECKSUM_FILE, "w", encoding="utf-8") as f:
        json.dump(checksum_data, f, indent=2)

    print(f"[SUCCESS] Recorded checksums in {CHECKSUM_FILE}")

if __name__ == "__main__":
    main()
