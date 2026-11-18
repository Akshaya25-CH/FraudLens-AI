# FraudLens AI — Step 9.1: GitHub Publication Readiness Report

**Date:** 2026-11-18  
**Audit Type:** Read-Only Open-Source Publication Readiness & Security Audit  
**Status:** Audit Complete — Ready for Staging (Zero Git/Remote Changes Executed)  

---

## 1. Executive Summary & Git Repository Status

A comprehensive read-only audit was performed to assess FraudLens AI's readiness for public GitHub release.

### Current Git Repository State:
- **Git Initialized:** **No** (`fatal: not a git repository (or any of the parent directories): .git`).
- **Remotes Configured:** None (`origin` not set).
- **Current Branch:** None.
- **Tracked Files:** 0.
- **Total Local Files:** All files currently reside in local untracked file space.
- **Root `.gitignore`:** **Missing**. Only a local `frontend/.gitignore` exists.

> [!IMPORTANT]
> Because Git has not yet been initialized and no root `.gitignore` is present, running `git init` and `git add .` prematurely would accidentally stage:
> 1. `backend/venv/` (~350 MB of virtual environment binaries, libraries, and DLLs).
> 2. `frontend/node_modules/` (~170 MB of JavaScript packages).
> 3. `frontend/dist/` (compiled build artifacts).
> 4. Python bytecode (`__pycache__/` and `*.pyc`).
> 
> A comprehensive root `.gitignore` **must be created before running `git add .`**.

---

## 2. Security & Privacy Audit Findings

An automated scan of all source files, configurations, scripts, and documentation was conducted to identify exposed credentials, private personal information, and environment leaks.

### 2.1. Credentials & Secrets Audit
- **API Keys / Access Tokens:** **Zero found** (`0` occurrences of AWS keys, GitHub tokens, Google API keys, or private keys).
- **Hardcoded Passwords / Bearer Tokens:** **Zero found**.
- **Environment Files (`.env`, `.env.local`):** **Zero found**. The application currently relies on portable defaults (`http://127.0.0.1:8000`) and standard environment variable fallbacks (`import.meta.env.VITE_API_URL`).

### 2.2. Personally Identifiable Information (PII) Audit
- **Real Phone Numbers / Bank Accounts / VPAs:** **Zero real PII found**.
- **Sample Presets:** All SMS, URL, and UPI scenarios in `App.jsx`, `main.py`, and test suites are strictly synthetic test patterns (e.g. `sbi-kyc-update.test`, `XX4921`, `9876543210`).
- **Client Privacy Guarantees:** Scan history is stored purely in browser memory / `localStorage` (`fraudlens_session_history`), isolating all user scans to the client device.

### 2.3. Local File Path References
- **Source Code (`backend/*.py`, `frontend/src/*`, `tests/*.py`):** Clean. All imports and path resolutions use relative paths or portable `Path(__file__).resolve().parent`.
- **Launcher Scripts (`run_backend.bat`, `run_frontend.bat`):** Clean. Both scripts use `%~dp0` (portable directory resolution).
- **Markdown Audit Logs (`frontend/STEP8B_*.md`, `STEP6B_*.md`):** Contain conversational markdown file links formatted as `file:///c:/Users/admin/OneDrive/Desktop/FraudLens-AI/...`.
  - *Recommendation:* These historical development logs may either be retained as local audit trail or sanitized to relative GitHub links before public repository commit.

---

## 3. Dataset & Model Publication Review

### 3.1. Model Artifacts Inventory & File Sizes

| Artifact Path | SHA-256 Checksum | Size | Public Release Recommendation |
| :--- | :--- | :---: | :---: |
| `models/sms_model.joblib` | `F17D1222624071530CE770540894B1AA9F36FF16DCD3D894DE005A61F2FE701A` | 3.84 MB | **Include (Active Model)** |
| `models/sms_model_baseline.joblib` | `C47360251F4A7C89C21B02D448CBEA6192A1A72D76B06C40ED6497CDB0B91DDA` | 3.32 MB | **Include (Baseline Reference)** |
| `models/sms_model_pre_step7_backup.joblib` | `C47360251F4A7C89C21B02D448CBEA6192A1A72D76B06C40ED6497CDB0B91DDA` | 3.32 MB | *Optional (Redundant with baseline)* |
| `models/experiments/*.joblib` (10 files) | Multiple (Config A, B, C, D variants) | ~28.6 MB | **Include (Experiment Reproducibility)** |

*GitHub Compatibility:* Total models directory size is **39.11 MB** across 18 files. The largest individual artifact is 4.10 MB, well under GitHub's 50 MB recommendation threshold and 100 MB hard limit. Git LFS (Large File Storage) is **not required**.

### 3.2. Dataset Inventory & Provenance

| Dataset Path | Size | Description & Provenance | Licensing & Redistribution |
| :--- | :---: | :--- | :--- |
| `datasets/SMSSpamCollection` | 466.7 KB | UCI SMS Spam Collection benchmark (Almeida & Hidalgo, 2012). | Public academic dataset; standard attribution required. |
| `datasets/sms_dataset.csv` | 1.97 KB | Initial synthetic baseline seed dataset. | Project-authored; MIT/Apache compatible. |
| `datasets/training/indian_sms_train.csv` | 105.4 KB | Curated synthetic training corpus of Indian financial fraud patterns. | Project-authored; zero real PII; safe for release. |
| `datasets/evaluation/indian_sms_eval.csv` | 23.5 KB | Curated synthetic development evaluation dataset. | Project-authored; zero real PII; safe for release. |
| `datasets/evaluation/indian_sms_final_locked.csv` | 76.1 KB | Locked golden test split for Step 6B candidate benchmark. | Project-authored; locked SHA-256; safe for release. |
| `datasets/evaluation/step6b_predictions.csv` | 91.7 KB | Locked predictions matrix from Step 6B candidate evaluation. | Evaluation audit artifact; safe for release. |

### 3.3. Evaluation vs. Real-World Disclaimers
> [!CAUTION]
> **Mandatory Real-World Performance Disclaimer for README & Publications:**  
> The SMS evaluation metrics (F1, Precision, Recall) documented across FraudLens AI were measured against structured synthetic evaluation sets simulating prevalent Indian cyber-crime lures. While the model achieves high recall on these benchmark scenarios, real-world financial fraud constantly mutates with novel evasions, zero-day social engineering lures, and conversational obfuscations. Benchmark performance **must not** be represented as guaranteed real-world security or 100% scam interception.

---

## 4. Recommended `.gitignore` Configuration

A new `.gitignore` file should be created in the repository root directory (`FraudLens-AI/.gitignore`) with the following rules:

```gitignore
# ==============================================================================
# FraudLens AI - Public Repository .gitignore
# ==============================================================================

# Python Virtual Environments
venv/
.venv/
env/
.env/
backend/venv/
backend/env/
backend/.venv/

# Python Bytecode & Optimization Caches
__pycache__/
*.py[cod]
*$py.class
*.so
.pytest_cache/
.coverage
htmlcov/

# Node.js & Frontend Package Dependencies
node_modules/
frontend/node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*
lerna-debug.log*

# Frontend Production Build Outputs
dist/
frontend/dist/
dist-ssr/
frontend/dist-ssr/
*.local

# Environment Variables & Sensitive Local Configurations
.env
.env.*
!.env.example
*.pem
*.key

# Temporary Workspace & Scratch Files
scratch/
*.tmp
*.temp
logs/
*.log

# Operating System & IDE Metadata
.DS_Store
Thumbs.db
desktop.ini
.vscode/
!.vscode/extensions.json
.idea/
*.suo
*.ntvs*
*.njsproj
*.sln
*.sw?
```

---

## 5. Proposed Project `README.md` Draft

Below is the complete, production-ready markdown content proposed for the root `README.md`:

```markdown
# FraudLens AI 🛡️
### Intelligent Multi-Engine Financial Fraud & Scam Defense

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%200.115+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React%2019%20%2B%20Vite%208-61DAFB.svg?logo=react&logoColor=black)](https://react.dev)
[![Scikit-Learn](https://img.shields.io/badge/ML-Scikit--Learn-F7931E.svg?logo=scikitlearn&logoColor=white)](https://scikit-learn.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

FraudLens AI is an open-source, client-first financial cybercrime defense platform designed to protect users against prevalent digital fraud vectors: **multilingual phishing SMS**, **malicious URL redirects**, and **deceptive UPI payment requests**.

---

## 📌 Problem Statement

Digital payments in India through the Unified Payments Interface (UPI) process billions of transactions monthly. Concurrently, cybercriminals deploy sophisticated social engineering schemes targeting retail users:
- **Phishing SMS:** Fake KYC panics, electricity disconnection threats, and unauthorized prize notifications.
- **Deceptive URLs:** Punycode lookalikes, subdomain brand spoofing, open redirect chains, and raw IP hostnames.
- **UPI Collect Traps:** Reverse payment traps where victims are tricked into entering their UPI PIN to "receive" funds, violating the golden rule of UPI.

FraudLens AI provides real-time, explainable, and privacy-preserving detection engines to counter these threats without exposing sensitive user financial data to third-party trackers.

---

## 🚀 Key Features

### 1. Multilingual SMS Fraud Detection
- Trained Scikit-Learn classification pipeline incorporating Indic-aware preprocessing, token normalization, and sublinear word/character n-gram TF-IDF representations.
- Supports **English**, **Hinglish** (Romanized Hindi), and **Hindi (Devanagari Unicode)**.
- Classifies incoming messages into `POTENTIAL_FRAUD` or `NO_FRAUD_PATTERN_DETECTED` with probabilistic risk scores (0–100%) and actionable security advice.

### 2. URL Phishing & Structural Analyzer
- 100% offline rule-based heuristic syntax parser.
- Inspects lexical features, brand spoofing in subdomains, excessive hyphenation, embedded userinfo credentials (`admin:pass@`), Punycode homographs (`xn--...`), IP hostnames, and suspicious top-level domains.
- Evaluates URLs without contacting remote target servers, preserving client anonymity.

### 3. UPI & Digital Payment Fraud Defense
- Rule-based heuristic engine analyzing transaction alerts, WhatsApp payment demands, and UPI IDs (VPAs).
- Detects the **UPI Golden Rule Violation**: Prompting users to enter a UPI PIN or scan a QR code to *receive* money.
- Inspects Virtual Payment Address handles (`@okhdfcbank`, `@ybl`) and flags suspicious keywords (`refund`, `care`, `support`, `cashback`) mimicking official banking desks.

### 4. Interactive Threat Intelligence & History
- **Risk Analytics:** Dynamic KPI cards and Recharts visualizations (threat distribution, score histograms, timeline activity) calculated strictly from active session scans.
- **Advanced Scan History:** Real-time search, multi-factor filtering (engine, risk level, date range), sorting, and RFC 4180 CSV export with UTF-8 BOM for Microsoft Excel.
- **Settings & System Diagnostics:** Live backend connectivity monitoring, model architecture disclosure, and local storage data management.

---

## 🏗️ Architecture & Technology Stack

```
FraudLens-AI/
├── backend/                  # FastAPI REST Service
│   ├── main.py               # API Endpoints (/health, /scan, /scan-url, /scan-payment)
│   ├── sms_preprocessor.py   # Indic Transliteration & Cleaning Pipeline
│   ├── url_scanner.py        # Structural URL Heuristic Engine
│   └── upi_scanner.py        # UPI Protocol & Payment Rule Engine
├── frontend/                 # React 19 + Vite 8 SPA
│   ├── src/
│   │   ├── App.jsx           # Core Layout, Navigation & Scanners
│   │   ├── RiskAnalytics.jsx # Threat Intelligence & Recharts Visualizations
│   │   ├── AdvancedScanHistory.jsx # Session Logs, Search & CSV Export
│   │   └── SettingsDiagnostics.jsx # Telemetry, Specs & Storage Management
├── models/                   # Serialized ML Pipeline Artifacts
└── datasets/                 # Training & Locked Evaluation Corpora
```

- **Backend:** Python 3.12, FastAPI, Uvicorn, Scikit-Learn, NumPy, Joblib.
- **Frontend:** React 19, Vite 8, Recharts 3, Lucide React, Oxlint.
- **Client Routing:** Zero-dependency URL hash navigation (`#overview`, `#sms`, `#url`, `#upi`, `#analytics`, `#history`, `#settings`).

---

## 💻 Local Setup & Installation (Windows)

### Prerequisites
- Python 3.10+ (Python 3.12 recommended)
- Node.js 18+ (Node.js 20+ recommended)
- Git

### 1. Clone the Repository
```powershell
git clone https://github.com/your-username/FraudLens-AI.git
cd FraudLens-AI
```

### 2. Backend Setup
```powershell
# Create and activate Python virtual environment
python -m venv backend\venv
.\backend\venv\Scripts\Activate.ps1

# Install backend dependencies
pip install -r backend\requirements.txt

# Run backend unit tests
python -m unittest discover tests
```

### 3. Frontend Setup
```powershell
cd frontend
npm install
npm run build
cd ..
```

---

## 🚦 Starting the Application

### Option A: Using One-Click Batch Launchers (Windows)
1. Double-click `run_backend.bat` to launch the FastAPI server at `http://127.0.0.1:8000`.
2. Double-click `run_frontend.bat` to launch the Vite development server at `http://localhost:5173`.

### Option B: Using PowerShell / Terminal
```powershell
# Terminal 1: Backend
.\backend\venv\Scripts\python.exe backend\main.py

# Terminal 2: Frontend
cd frontend
npm run dev
```

Open your browser and navigate to `http://localhost:5173`.

---

## 🔌 API Endpoints Reference

| Method | Endpoint | Description | Sample Request |
| :---: | :--- | :--- | :--- |
| `GET` | `/health` | Service health & model status | *None* |
| `POST` | `/scan` | SMS scam & phishing detection | `{"message": "Your bank account is blocked. Update KYC now."}` |
| `POST` | `/scan-url` | URL phishing & syntax analysis | `{"url": "https://paypal.com.verify-billing.xyz/login"}` |
| `POST` | `/scan-payment` | UPI payment & VPA verification | `{"message": "Enter UPI PIN to receive Rs 2500", "upi_id": null}` |

---

## 🔒 Privacy & Security Considerations

- **Client-Side Storage:** All scan history resides strictly in the browser's local storage (`fraudlens_session_history`). No user messages or URLs are persisted into server-side databases.
- **Zero Real-World Execution:** The URL analyzer and UPI scanner operate 100% statically. They do not initiate HTTP outbound connections to suspect URLs and never interact with live NPCI banking switches.
- **No Data Fabrication:** All analytics charts, counts, and history entries are calculated dynamically from actual session events.

---

## ⚠️ Limitations & Honest Disclaimer

- **Synthetic Evaluation Benchmark:** The model was tuned and evaluated against curated synthetic benchmarks simulating real-world scam categories. While it scores high recall on these structured cases, cybercriminals rapidly invent novel obfuscations, Unicode homoglyphs, and polymorphic phrasings. Benchmark scores do not guarantee 100% scam interception.
- **Offline Heuristics:** The URL scanner evaluates syntax, structure, and lexical indicators. It cannot determine if a legitimate domain has suffered a server-side compromise.
- **Advisory Only:** FraudLens AI provides supplementary threat intelligence and should never replace official bank apps or two-factor authentication practices.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
```

---

## 6. Exact Files Recommended for Public Release

### ✅ Recommended for Inclusion (Staged for Git):
1. **Root Configuration & Launchers:**
   - `.gitignore` (Newly created based on Section 4 recommendations).
   - `README.md` (Newly created based on Section 5 draft).
   - `run_backend.bat`
   - `run_frontend.bat`
2. **Backend Directory (`backend/`):**
   - `main.py`
   - `sms_preprocessor.py`
   - `url_scanner.py`
   - `upi_scanner.py`
   - `requirements.txt`
   - `train_model.py`, `evaluate_indian_sms.py`, `build_and_audit_dataset.py`, `run_experiments_step5b.py`
   - `__init__.py`
3. **Frontend Directory (`frontend/`):**
   - `package.json`, `package-lock.json`
   - `vite.config.js`, `index.html`, `.oxlintrc.json`
   - `src/App.jsx`, `src/App.css`, `src/main.jsx`, `src/index.css`
   - `src/RiskAnalytics.jsx`, `src/AdvancedScanHistory.jsx`, `src/SettingsDiagnostics.jsx`
   - `src/assets/*`
   - `public/*`
4. **Test Suite (`tests/`):**
   - `test_backend.py`, `test_sms_comprehensive.py`, `test_sms_preprocessor.py`
   - `test_url_comprehensive.py`, `test_url_scanner.py`, `test_upi_comprehensive.py`, `test_upi_scanner.py`
   - `test_cors.py`, `test_audit.py`
5. **Models (`models/`):**
   - `models/sms_model.joblib` (Active frozen candidate)
   - `models/sms_model_baseline.joblib`
   - `models/experiments/*.joblib` (Full experimental record)
   - `models/model_checksums.manifest` (if present)
6. **Datasets (`datasets/`):**
   - `datasets/training/indian_sms_train.csv`
   - `datasets/evaluation/indian_sms_eval.csv`
   - `datasets/evaluation/indian_sms_final_locked.csv`
   - `datasets/evaluation/step6b_predictions.csv`
   - `datasets/SMSSpamCollection`
   - `datasets/sms_dataset.csv`
7. **Documentation (`docs/` & reports):**
   - Milestone markdown reports (`datasets/training/*.md`, `datasets/evaluation/*.md`, `frontend/*.md`).

### ❌ Strictly Excluded (Ignored via `.gitignore`):
- `backend/venv/`
- `frontend/node_modules/`
- `frontend/dist/`
- `scratch/`
- `__pycache__/` and `*.pyc`
- Any local OS artifacts (`Thumbs.db`, `.DS_Store`).

---

## 7. Blockers & Pre-Publication Checklist

| Checklist Item | Status | Action Required |
| :--- | :---: | :--- |
| **Root `.gitignore`** | ⚠️ Pending | Create `FraudLens-AI/.gitignore` before initializing Git. |
| **Root `README.md`** | ⚠️ Pending | Write root `README.md` using the proposed draft. |
| **LICENSE File** | ⚠️ Pending | Add `LICENSE` (e.g. MIT License) to root directory. |
| **Clean `scratch/` Directory** | ✅ Verified | Scratch folder is currently empty. |
| **No Hardcoded Secrets** | ✅ Verified | Zero credentials or tokens detected. |
| **Model File Sizes** | ✅ Verified | All `.joblib` files are < 5 MB (Git LFS not needed). |
| **Test Suites Passing** | ✅ Verified | 100% unit tests, comprehensive tests, and lint pass. |

---

*Report authored. Strictly zero Git commands, repository creations, commits, or pushes were initiated.*
