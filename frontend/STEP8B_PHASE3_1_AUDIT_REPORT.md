# FraudLens AI — Step 8B, Phase 3.1: Settings Accuracy Audit Report

**Audit Date:** 2026-11-18  
**Audit Type:** Read-Only Source Code & Model Inspection  
**Status:** Audit Complete — Zero Source Files Modified  

---

## Executive Summary

A comprehensive read-only audit of the newly implemented **Settings & Diagnostics** page (`frontend/src/SettingsDiagnostics.jsx`) was executed against the active backend, model artifacts, and client source code.

### Summary of Audit Findings:
1. **SMS Model Architecture**: **Mismatch Detected**. The active model artifact (`models/sms_model.joblib`) is Config D (C=10.0, unweighted). It features a `FeatureUnion` combining word n-grams `(1, 2)` and character boundary n-grams `(3, 5)` with `sublinear_tf=True`. `SettingsDiagnostics.jsx` inaccurately displays `"TF-IDF Vectorizer (ngram range 1-3) + Logistic Regression (C=10.0, unweighted)"`, completely omitting the character n-gram extractor, misstating the word n-gram range as `1-3` instead of `1-2`, and omitting `sublinear_tf=True`.
2. **Local Storage Key**: **Exact Match Verified**. The key `fraudlens_session_history` is used identically in `App.jsx` and displayed in `SettingsDiagnostics.jsx`. The `clearHistory` handler resets both `localStorage` and client state, synchronizing Overview, History, Risk Analytics, and Settings.
3. **Version Information**: **Hardcoded Scaffold Constant**. The frontend version `0.0.0` is hardcoded in `SettingsDiagnostics.jsx:373`. It corresponds to the default scaffold version in `frontend/package.json`, rather than a dynamically imported version or dedicated release version.
4. **Backend Diagnostics Telemetry**: **Verified with Semantic Distinction**. Engine status and model-loaded flags genuinely reflect the backend `/health` response. However, `lastChecked` records the timestamp of the **last probe attempt** (including failed connections), rather than exclusively the last *successful* probe.
5. **Preservation**: Verified. No project source files, configurations, models, or datasets were modified during this audit.

---

## 1. Active SMS Model Architecture Audit

### 1.1. Inspection of `models/sms_model.joblib`
Direct inspection of `models/sms_model.joblib` (SHA-256: `F17D1222624071530CE770540894B1AA9F36FF16DCD3D894DE005A61F2FE701A`, installed in Step 7) revealed the following concrete pipeline architecture:

```
Pipeline(steps=[
    ('preprocessor', MultilingualSMSPreprocessor()),
    ('features', FeatureUnion(transformer_list=[
        ('word', TfidfVectorizer(
            analyzer='word',
            ngram_range=(1, 2),
            min_df=1,
            max_features=None,
            norm='l2',
            sublinear_tf=True
        )),
        ('char', TfidfVectorizer(
            analyzer='char_wb',
            ngram_range=(3, 5),
            min_df=1,
            max_features=None,
            norm='l2',
            sublinear_tf=True
        ))
    ])),
    ('classifier', LogisticRegression(
        C=10.0,
        class_weight=None,
        solver='lbfgs',
        max_iter=1000,
        random_state=42
    ))
])
```

### 1.2. Architecture Displayed in `SettingsDiagnostics.jsx`
- **Location:** [`frontend/src/SettingsDiagnostics.jsx#L190-L193`](file:///c:/Users/admin/OneDrive/Desktop/FraudLens-AI/frontend/src/SettingsDiagnostics.jsx#L190-L193)
- **Displayed String:**
  ```jsx
  <div className="spec-row">
    <span className="spec-key">Model Architecture</span>
    <span className="spec-val">TF-IDF Vectorizer (ngram range 1-3) + Logistic Regression (C=10.0, unweighted)</span>
  </div>
  ```
- **Backend `/health` Payload Module String:**
  [`backend/main.py#L88`](file:///c:/Users/admin/OneDrive/Desktop/FraudLens-AI/backend/main.py#L88):
  `"sms_scanner": "TF-IDF + Logistic Regression"`

### 1.3. Discrepancy Breakdown
| Dimension | Real Active Model Artifact (`models/sms_model.joblib`) | Displayed in `SettingsDiagnostics.jsx` | Discrepancy Status |
| :--- | :--- | :--- | :--- |
| **Pipeline Container** | `sklearn.pipeline.Pipeline` with 3 steps (`preprocessor`, `features`, `classifier`) | Flat description | Omits pipeline structure |
| **Feature Extraction** | `sklearn.pipeline.FeatureUnion` (Dual vectorizer) | Single `TF-IDF Vectorizer` | **MISMATCH**: Omits `FeatureUnion` |
| **Word N-grams** | `ngram_range=(1, 2)` (Unigrams + Bigrams) | `ngram range 1-3` (Unigrams, Bigrams, Trigrams) | **MISMATCH**: Inaccurate n-gram upper bound |
| **Character N-grams** | `analyzer='char_wb'`, `ngram_range=(3, 5)` | Not mentioned | **MISMATCH**: Completely omitted |
| **TF Scaling** | `sublinear_tf=True` (on both word & char vectorizers) | Not mentioned | Omitted |
| **Classifier & C** | `LogisticRegression(C=10.0, class_weight=None)` | `LogisticRegression (C=10.0, unweighted)` | **MATCH** |
| **Preprocessor** | `MultilingualSMSPreprocessor` (First pipeline step) | Listed separately in table | **MATCH** (Semantically described) |

---

## 2. Local Storage Audit

### 2.1. LocalStorage Key Tracing
- **Initialization & Retrieval:**
  [`frontend/src/App.jsx#L244`](file:///c:/Users/admin/OneDrive/Desktop/FraudLens-AI/frontend/src/App.jsx#L244):
  ```javascript
  const saved = localStorage.getItem('fraudlens_session_history')
  ```
- **Persistence Sync:**
  [`frontend/src/App.jsx#L297`](file:///c:/Users/admin/OneDrive/Desktop/FraudLens-AI/frontend/src/App.jsx#L297):
  ```javascript
  localStorage.setItem('fraudlens_session_history', JSON.stringify(scanHistory))
  ```
- **Display in Settings:**
  [`frontend/src/SettingsDiagnostics.jsx#L312`](file:///c:/Users/admin/OneDrive/Desktop/FraudLens-AI/frontend/src/SettingsDiagnostics.jsx#L312):
  `...<code>window.localStorage</code> under the key <code>fraudlens_session_history</code>...`  
  [`frontend/src/SettingsDiagnostics.jsx#L325`](file:///c:/Users/admin/OneDrive/Desktop/FraudLens-AI/frontend/src/SettingsDiagnostics.jsx#L325):
  `Storage key: <code>fraudlens_session_history</code>`

**Result:** Exact key match verified (`fraudlens_session_history`).

### 2.2. Clear-History Handler & Synchronization Trace
1. **Trigger:** User clicks `"Clear Session History"` in Settings ([`SettingsDiagnostics.jsx#L330`](file:///c:/Users/admin/OneDrive/Desktop/FraudLens-AI/frontend/src/SettingsDiagnostics.jsx#L330)).
2. **Confirmation:** Invokes `onClearHistory()` -> `clearHistory()` in [`App.jsx#L504`](file:///c:/Users/admin/OneDrive/Desktop/FraudLens-AI/frontend/src/App.jsx#L504):
   ```javascript
   function clearHistory() {
     if (window.confirm('Clear all session scan history?')) {
       setScanHistory([])
     }
   }
   ```
3. **Storage Synchronization:** `setScanHistory([])` updates `scanHistory` state to `[]`. The `useEffect` hook in [`App.jsx#L295-L300`](file:///c:/Users/admin/OneDrive/Desktop/FraudLens-AI/frontend/src/App.jsx#L295-L300) runs and executes:
   ```javascript
   localStorage.setItem('fraudlens_session_history', '[]')
   ```
4. **Multi-View Synchronization:**
   - **Overview Tab:** Recalculates `totalScans`, `fraudScans`, `legitScans`, and `avgScore` to `0` / `'0.0'`. Recent scans table renders the empty state.
   - **Scan History Tab:** Displays `0` in sidebar count badge. Renders `"No session scan history recorded."`.
   - **Risk Analytics Tab:** Receives `scanHistory={[]}`. Line 174 of `RiskAnalytics.jsx` triggers the global empty state card `"No Scan History Recorded"`.
   - **Settings Tab:** Receives `scanHistoryCount={0}`, updates count to `0 recorded scan(s)`, and disables the clear button.

**Result:** Verified. The clear-history handler fully synchronizes all application modules.

---

## 3. Version Information Audit

### 3.1. Source of Displayed Frontend Version `0.0.0`
- **Location:** [`frontend/src/SettingsDiagnostics.jsx#L373`](file:///c:/Users/admin/OneDrive/Desktop/FraudLens-AI/frontend/src/SettingsDiagnostics.jsx#L373):
  ```jsx
  <div className="app-info-tile">
    <span className="info-tile-label">FRONTEND CLIENT VERSION</span>
    <strong className="info-tile-val">0.0.0</strong>
    <span className="info-tile-sub">Vite React Production Client</span>
  </div>
  ```
- **Origin in Project Files:**
  [`frontend/package.json#L4`](file:///c:/Users/admin/OneDrive/Desktop/FraudLens-AI/frontend/package.json#L4):
  ```json
  "version": "0.0.0",
  ```

### 3.2. Evaluation of Authenticity
- The value `0.0.0` is a **hardcoded literal** in `SettingsDiagnostics.jsx`.
- It is **not** imported dynamically from `package.json` (e.g. via bundler define or JSON import).
- It is the standard default placeholder version created by `npm create vite`. There is **no** separately defined application release version for the frontend client.
- In contrast, the backend declares an explicit release version in [`backend/main.py#L92`](file:///c:/Users/admin/OneDrive/Desktop/FraudLens-AI/backend/main.py#L92) (`"version": "2.2.0"`), which is fetched dynamically via `/health`.

---

## 4. Backend Diagnostics Audit

### 4.1. Verification of Backend Health Response Mapping
In [`backend/main.py#L82-L94`](file:///c:/Users/admin/OneDrive/Desktop/FraudLens-AI/backend/main.py#L82-L94):
```python
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "modules": {
            "sms_scanner": "TF-IDF + Logistic Regression",
            "url_scanner": "Structural Heuristic Rule-Based Engine",
            "payment_scanner": "UPI & Payment Fraud Heuristic Engine"
        },
        "version": "2.2.0"
    }
```

In [`frontend/src/SettingsDiagnostics.jsx`](file:///c:/Users/admin/OneDrive/Desktop/FraudLens-AI/frontend/src/SettingsDiagnostics.jsx):
- `model_loaded` -> `isModelLoaded = Boolean(backendStatus.data?.model_loaded)` (line 38) -> determines `"Active & Loaded"` vs `"Model not loaded"` vs `"Offline"`.
- `modules.sms_scanner` -> rendered in line 148.
- `modules.url_scanner` -> rendered in line 171.
- `modules.payment_scanner` -> rendered in line 194.
- `version` -> rendered as `v2.2.0` in line 40.

**Result:** Verified. Engine and model-loaded statuses are directly derived from actual `/health` payload fields.

### 4.2. Semantic Meaning of `lastChecked`
In [`frontend/src/App.jsx#L251-L288`](file:///c:/Users/admin/OneDrive/Desktop/FraudLens-AI/frontend/src/App.jsx#L251-L288):
```javascript
const triggerManualHealthCheck = useCallback(async () => {
  setBackendStatus((prev) => ({ ...prev, checking: true }))
  const nowTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  try {
    const res = await fetch(`${BACKEND_BASE}/health`, { method: 'GET' })
    if (res.ok) {
      const data = await res.json()
      setBackendStatus({ online: true, checking: false, data, lastChecked: nowTime })
    } else {
      setBackendStatus({ online: false, checking: false, data: null, lastChecked: nowTime })
    }
  } catch {
    setBackendStatus({ online: false, checking: false, data: null, lastChecked: nowTime })
  }
}, [])
```

**Result & Distinction:**
- `lastChecked: nowTime` is executed in the `res.ok` branch, the `!res.ok` branch, **and** the `catch` block.
- Therefore, `lastChecked` represents the timestamp of the **last probe attempt**, regardless of whether the probe succeeded or failed.
- In `SettingsDiagnostics.jsx:105`, the UI label is titled `LAST HEALTH CHECK`. When the backend is offline, `lastChecked` shows the timestamp of the failed probe alongside an `Offline` indicator.

---

## 5. Preservation Check

- **Modified Files during Audit:** None (only this report was authored).
- **Source Code Alterations:** 0 lines modified in `frontend/src/*`, `backend/*`, `models/*`, or `datasets/*`.
- **Active Model Intact:** SHA-256 remains `F17D1222624071530CE770540894B1AA9F36FF16DCD3D894DE005A61F2FE701A`.

---

## 6. Audit Conclusion & Recommendations

| Item | Finding | Action Needed in Future Maintenance |
| :--- | :--- | :--- |
| **1. Model Architecture** | `SettingsDiagnostics.jsx` states `"TF-IDF Vectorizer (ngram range 1-3) + Logistic Regression (C=10.0, unweighted)"`. Real model has a `FeatureUnion` with word `(1, 2)` + char `(3, 5)` with `sublinear_tf=True`. | When authorized, update the description in `SettingsDiagnostics.jsx` and `main.py` to accurately reflect the Config D `FeatureUnion`. |
| **2. Local Storage Key** | Exact match verified (`fraudlens_session_history`). Full multi-view synchronization confirmed. | None. Implemented correctly. |
| **3. Frontend Version** | Hardcoded `0.0.0` drawn from scaffold `package.json`. | None required unless the project implements dynamic package version injection via Vite define. |
| **4. Backend Diagnostics** | Health fields mapped cleanly. `lastChecked` reflects the last probe attempt timestamp. | Note the semantic distinction: probe attempt vs successful probe. |

*Audit complete. Strictly no files or configurations have been modified.*
