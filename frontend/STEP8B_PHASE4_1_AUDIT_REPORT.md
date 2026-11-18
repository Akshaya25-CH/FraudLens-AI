# FraudLens AI — Step 8B, Phase 4.1: History Accuracy Audit Report

**Audit Date:** 2026-11-18  
**Audit Type:** Read-Only Source Code & Data Flow Inspection  
**Status:** Complete — Zero Source Files Modified  

---

## Executive Summary

A comprehensive read-only audit of the **Advanced Scan History** implementation (`frontend/src/AdvancedScanHistory.jsx`) and its integration in `frontend/src/App.jsx` was conducted.

### Key Audit Findings:
1. **History Data Schema**: Verified. All three scanning engines (SMS, URL, UPI) emit a uniform schema containing `id`, `type`, `timestamp`, `date`, `message`, `prediction`, `risk_level`, `model_score`, `recommendation`, and `explanation`. `AdvancedScanHistory.jsx` correctly maps all fields.
2. **Date Filter Semantics**: Verified. `Today` operates as an inclusive hybrid matching records on the same calendar day (local timezone) or within the rolling last 24 hours. `Last 7 Days` and `Last 30 Days` enforce strict rolling windows (168h and 720h). If `item.id` is missing or non-numeric, it safely passes through (`true`) without throwing errors.
3. **CSV Export & Non-ASCII Encoding**: Verified with minor limitation. RFC 4180 cell escaping (doubled quotes `""`, comma wrapping, CRLF line endings) is compliant. Non-ASCII Hindi (Devanagari) content survives UTF-8 encoding cleanly. However, the CSV blob currently lacks a UTF-8 Byte Order Mark (`\uFEFF`), which may cause Microsoft Excel on Windows to default to ANSI decoding unless opened via the Text Import Wizard.
4. **Re-inspection Functionality**: Verified. Inspecting a scan restores the payload and navigates to the dedicated scanner tab without triggering an automated resubmission. SMS results are restored immediately; URL and UPI reset result state for manual re-scanning. A minor nuance exists where UPI entries scanned solely by VPA handle are loaded into the payment message input as `"UPI ID: <vpa>"`.
5. **Preservation**: Verified. No project source files, configurations, models, or datasets were modified during this audit.

---

## 1. History Data Schema Audit

### 1.1. Schema Construction by Engine (`frontend/src/App.jsx`)

Inspection of `frontend/src/App.jsx` verified the exact structure of `newEntry` across all three detection handlers:

| Field | SMS Scanner (`App.jsx#L348-L359`) | URL Scanner (`App.jsx#L404-L415`) | UPI Scanner (`App.jsx#L466-L477`) |
| :--- | :--- | :--- | :--- |
| **`id`** | `Date.now()` (epoch ms) | `Date.now()` (epoch ms) | `Date.now()` (epoch ms) |
| **`type`** | `'SMS'` | `'URL'` | `'UPI'` |
| **`timestamp`** | `new Date().toLocaleTimeString(...)` | `new Date().toLocaleTimeString(...)` | `new Date().toLocaleTimeString(...)` |
| **`date`** | `new Date().toLocaleDateString()` | `new Date().toLocaleDateString()` | `new Date().toLocaleDateString()` |
| **`message`** | Cleaned SMS text | Cleaned URL string | `trimmedMsg \|\| "UPI ID: <vpa>"` |
| **`prediction`** | `data.prediction` (0 or 1) | `data.risk_category === 'HIGH' ? 1 : 0` | `data.risk_category === 'HIGH' ? 1 : 0` |
| **`risk_level`** | `data.risk_level` (`POTENTIAL_FRAUD` / `NO_FRAUD_PATTERN_DETECTED`) | `data.risk_category === 'HIGH' ? 'HIGH_STRUCTURAL_RISK' : ...` | `data.risk_category === 'HIGH' ? 'HIGH_PAYMENT_RISK' : ...` |
| **`model_score`** | `data.model_score` (0–100%) | `data.structural_risk_score` (0–100) | `data.structural_risk_score` (0–100) |
| **`recommendation`**| `data.recommendation` | `data.recommendation` | `data.recommendation` |
| **`explanation`** | `data.explanation \|\| data.reasons[0]` | `${data.warning_count} structural warning sign(s) detected.` | `${data.warning_count} payment warning signal(s) detected.` |

### 1.2. Verification in `AdvancedScanHistory.jsx`
- **Render Mapping:**
  - Header: `scan.type`, `scan.date`, `scan.timestamp` ([`AdvancedScanHistory.jsx#L346-L352`](file:///c:/Users/admin/OneDrive/Desktop/FraudLens-AI/frontend/src/AdvancedScanHistory.jsx#L346-L352)).
  - Risk Tag: `isHigh ? 'HIGH RISK' : isMedium ? 'MEDIUM RISK' : 'LOW RISK'` ([`#L353-L357`](file:///c:/Users/admin/OneDrive/Desktop/FraudLens-AI/frontend/src/AdvancedScanHistory.jsx#L353-L357)).
  - Payload: `scan.message` ([`#L360`](file:///c:/Users/admin/OneDrive/Desktop/FraudLens-AI/frontend/src/AdvancedScanHistory.jsx#L360)).
  - Explanation: `scan.explanation` ([`#L364`](file:///c:/Users/admin/OneDrive/Desktop/FraudLens-AI/frontend/src/AdvancedScanHistory.jsx#L364)).
  - Score Formatting: `scan.type === 'SMS' ? `${scan.model_score}%` : `${scan.model_score} / 100`` ([`#L373`](file:///c:/Users/admin/OneDrive/Desktop/FraudLens-AI/frontend/src/AdvancedScanHistory.jsx#L373)).

**Conclusion:** All fields are mapped and formatted with 100% engine parity.

---

## 2. Date Filter Accuracy Audit

### 2.1. Logic Implementation (`AdvancedScanHistory.jsx#L26-L46`)
```javascript
function matchesDateFilter(item, filter, nowMs) {
  if (filter === 'ALL') return true
  const itemTime = typeof item.id === 'number' && item.id > 1000000000000 ? item.id : null
  if (!itemTime) return true

  const diffMs = nowMs - itemTime
  if (filter === 'TODAY') {
    const nowDate = new Date(nowMs).toDateString()
    const itemDate = new Date(itemTime).toDateString()
    return nowDate === itemDate || diffMs <= 24 * 60 * 60 * 1000
  }
  if (filter === 'WEEK') {
    return diffMs <= 7 * 24 * 60 * 60 * 1000
  }
  if (filter === 'MONTH') {
    return diffMs <= 30 * 24 * 60 * 60 * 1000
  }
  return true
}
```

### 2.2. Boundary & Semantic Analysis
1. **Meaning of `Today`:**
   - Evaluates: `nowDate === itemDate || diffMs <= 24 * 60 * 60 * 1000`.
   - UI Label: `"Today (Last 24h)"`.
   - Result: Implemented as an inclusive hybrid. Any scan conducted on the current calendar date (local timezone) OR within the trailing 24 hours (86,400,000 ms) matches.
2. **Boundaries for 7 Days and 30 Days:**
   - `WEEK`: Strict rolling window of `7 * 24 * 60 * 60 * 1000` ms (168 hours).
   - `MONTH`: Strict rolling window of `30 * 24 * 60 * 60 * 1000` ms (720 hours).
3. **Handling of Malformed/Missing Timestamps:**
   - Evaluates: `typeof item.id === 'number' && item.id > 1000000000000 ? item.id : null`.
   - If `item.id` is not an epoch millisecond integer (e.g. `null`, `"UUID-abc"`, or `42`), `itemTime` evaluates to `null`.
   - When `itemTime` is `null`, it returns `true` (pass-through).
   - *Limitation:* It does not attempt to parse `item.date` or `item.timestamp` when `item.id` is non-standard. However, because `App.jsx` strictly creates all records with `id: Date.now()`, every authentic session record is guaranteed to have a valid epoch integer.

---

## 3. CSV Export Audit

### 3.1. RFC 4180 Escaping Compliance
- **Cell Escaping:**
  [`AdvancedScanHistory.jsx#L77-L81`](file:///c:/Users/admin/OneDrive/Desktop/FraudLens-AI/frontend/src/AdvancedScanHistory.jsx#L77-L81):
  ```javascript
  function escapeCsvCell(val) {
    if (val === null || val === undefined) return '""'
    const str = String(val)
    return `"${str.replace(/"/g, '""')}"`
  }
  ```
  - Compliant with RFC 4180 §2.5, §2.6, and §2.7:
    - All fields are quoted.
    - Embedded double quotes are escaped by doubling (`""`).
    - Commas and line breaks are fully enclosed and preserved.
    - Rows are joined by CRLF (`\r\n`) in accordance with RFC 4180 §2.1.
- **Export Scope:** Strictly exports `filteredRecords` (`AdvancedScanHistory.jsx#L143-L170`). Any search query or dropdown filter active in the UI restricts the output rows accordingly.
- **Hindi / Hinglish Non-ASCII Support:**
  - Encoded with `{ type: 'text/csv;charset=utf-8;' }`.
  - Non-ASCII Devanagari Unicode characters (e.g. `प्रिय ग्राहक, आपका बैंक खाता...`) survive with byte fidelity in modern editors, Google Sheets, and LibreOffice.
  - *Identified Limitation:* The export blob currently does not prepend a UTF-8 Byte Order Mark (`\uFEFF`). On Windows, direct double-clicking of the CSV in certain versions of Microsoft Excel may open using the system default ANSI code page (Windows-1252), causing Devanagari text to appear garbled unless the user opens via `Data > From Text/CSV`.

---

## 4. Re-inspection Audit

### 4.1. Execution Trace (`frontend/src/App.jsx#L512-L536`)
```javascript
function handleInspectScan(item) {
  if (!item) return
  if (item.type === 'URL') {
    setUrlInput(item.message || '')
    setUrlError('')
    setUrlResult(null)
    setActiveTab('url')
  } else if (item.type === 'UPI') {
    setUpiMessage(item.message || '')
    setUpiError('')
    setUpiResult(null)
    setActiveTab('upi')
  } else {
    setMessage(item.message || '')
    setError('')
    setResult({
      prediction: item.prediction,
      risk_level: item.risk_level,
      model_score: item.model_score,
      explanation: item.explanation,
      recommendation: item.recommendation
    })
    setActiveTab('sms')
  }
}
```

### 4.2. Verification Findings
1. **Correct Routing:**
   - `type === 'URL'` -> navigates to `setActiveTab('url')` and populates `urlInput`.
   - `type === 'UPI'` -> navigates to `setActiveTab('upi')` and populates `upiMessage`.
   - `type === 'SMS'` -> navigates to `setActiveTab('sms')` and populates `message`.
2. **Accidental Resubmission:**
   - **Confirmed:** `handleInspectScan` does *not* invoke `handleScan()`, `handleUrlScan()`, or `handleUpiScan()`. No network requests are dispatched upon clicking Inspect.
3. **Payload Restoration Nuance:**
   - For **SMS**, the previous result card is fully populated via `setResult(...)`.
   - For **URL** and **UPI**, `urlResult` and `upiResult` are set to `null`, requiring the user to click the scan button to re-run.
   - For **UPI**, if a past scan was performed using *only* a VPA handle (without a message), the stored message was formatted as `"UPI ID: <vpa>"`. Inspecting loads this combined string into `upiMessage` rather than splitting it back into the separate `upiVpa` input field.

---

## 5. Preservation Check

- **Modified Files during Audit:** None (only this report was authored).
- **Source Code Alterations:** 0 lines modified in `frontend/src/*`, `backend/*`, `models/*`, or `datasets/*`.
- **Active Model Intact:** SHA-256 remains `F17D1222624071530CE770540894B1AA9F36FF16DCD3D894DE005A61F2FE701A`.

---

## 6. Audit Conclusion & Recommendations

| Investigation Area | Audit Finding | Status |
| :--- | :--- | :--- |
| **History Schema** | Uniform schema across SMS, URL, and UPI scanners. `AdvancedScanHistory.jsx` maps all fields correctly. | **Compliant** |
| **Date Filtering** | `Today (Last 24h)` operates as an inclusive calendar day + 24h rolling filter. `WEEK` and `MONTH` enforce strict 7-day and 30-day boundaries. Missing timestamps default to pass-through. | **Compliant** |
| **CSV Escaping** | RFC 4180 quotes, commas, and CRLF escaping verified. Scoped strictly to filtered records. Missing UTF-8 BOM (`\uFEFF`) for Excel auto-detection noted as a future enhancement. | **Compliant (Minor Excel BOM observation)** |
| **Re-inspection** | Correctly switches tabs and loads inputs without automated resubmission. SMS restores results card; URL/UPI require manual re-scan. UPI VPA string format noted. | **Compliant** |

*Audit complete. Strictly no files or configurations have been modified.*
