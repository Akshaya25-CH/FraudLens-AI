import { useState } from 'react'
import {
  Settings, Server, Cpu, Lock, Info, RefreshCw,
  CheckCircle2, AlertCircle, Trash2,
  Smartphone, Link2, MessageSquareText,
  Database
} from 'lucide-react'

export default function SettingsDiagnostics({
  backendStatus = { online: false, checking: false, data: null, lastChecked: null },
  onRefreshHealth = () => {},
  backendBaseUrl = 'http://127.0.0.1:8000',
  scanHistoryCount = 0,
  onClearHistory = () => {},
  onNavigate = () => {},
  onToast = () => {}
}) {
  const [clearNotice, setClearNotice] = useState('')

  // Sanitize base URL to ensure no credentials or secrets are inadvertently displayed
  let sanitizedBaseUrl = backendBaseUrl
  try {
    const parsed = new URL(backendBaseUrl)
    sanitizedBaseUrl = `${parsed.protocol}//${parsed.host}`
  } catch {
    sanitizedBaseUrl = backendBaseUrl
  }

  function handleClearWithNotice() {
    const countBefore = scanHistoryCount
    onClearHistory()
    if (countBefore > 0) {
      setClearNotice('Local session scan history has been cleared successfully.')
      if (onToast) onToast('Local session scan history cleared.', 'success')
      setTimeout(() => setClearNotice(''), 4000)
    }
  }

  const isModelLoaded = Boolean(backendStatus.data?.model_loaded)
  const backendVersion = backendStatus.data?.version
    ? `v${backendStatus.data.version}`
    : backendStatus.online
    ? 'Not exposed by backend'
    : 'Unavailable'

  const smsScannerStatus = isModelLoaded
    ? 'Active & Loaded'
    : backendStatus.online
    ? 'Model not loaded'
    : 'Offline'

  const urlScannerStatus = backendStatus.online ? 'Active' : 'Offline'
  const upiScannerStatus = backendStatus.online ? 'Active' : 'Offline'

  return (
    <div className="settings-container">
      {/* HEADER SECTION */}
      <div className="scanner-header-section">
        <div className="scanner-eyebrow">
          <Settings size={14} /> SYSTEM CONFIGURATION & DIAGNOSTICS
        </div>
        <h2 className="scanner-main-title">Settings & System Diagnostics</h2>
        <p className="scanner-main-desc">
          Monitor real-time backend health, inspect verified ML model specifications, review data transmission privacy policies, and manage browser storage.
        </p>
      </div>

      {/* SECTION 1: SYSTEM STATUS & DIAGNOSTICS */}
      <div className="fintech-card settings-card">
        <div className="settings-card-header">
          <div className="settings-title-group">
            <div className="settings-title-row">
              <Server size={18} className="settings-icon blue" />
              <h3 className="settings-card-title">System Status & API Diagnostics</h3>
            </div>
            <p className="settings-card-desc">
              Real-time connectivity and health telemetry from the FraudLens AI FastAPI service.
            </p>
          </div>
          <button
            type="button"
            className="secondary-btn refresh-btn"
            onClick={onRefreshHealth}
            disabled={backendStatus.checking}
            title="Perform live GET /health probe"
          >
            <RefreshCw size={14} className={backendStatus.checking ? 'spin' : ''} />
            <span>{backendStatus.checking ? 'Checking...' : 'Refresh Diagnostics'}</span>
          </button>
        </div>

        {/* Status Banner */}
        <div className={`diagnostics-status-banner ${backendStatus.checking ? 'checking' : backendStatus.online ? 'online' : 'offline'}`}>
          <div className="banner-icon-col">
            {backendStatus.checking ? (
              <RefreshCw size={18} className="spin" />
            ) : backendStatus.online ? (
              <CheckCircle2 size={18} />
            ) : (
              <AlertCircle size={18} />
            )}
          </div>
          <div className="banner-text-col">
            <div className="banner-headline">
              {backendStatus.checking
                ? 'Connecting to backend diagnostics endpoint...'
                : backendStatus.online
                ? 'All Security Services Operational · Backend Connected'
                : 'Backend Server Unreachable · Diagnostics Offline'}
            </div>
            <div className="banner-subtext">
              {backendStatus.online
                ? `FastAPI server listening at ${sanitizedBaseUrl} · Model loaded in memory.`
                : `Cannot establish connection with ${sanitizedBaseUrl}. Ensure uvicorn server is running.`}
            </div>
          </div>
        </div>

        {/* Diagnostics Tiles Grid */}
        <div className="diagnostics-tiles-grid">
          <div className="diagnostic-tile">
            <span className="tile-label">BACKEND CONNECTION</span>
            <div className="tile-value-row">
              <span className={`status-dot ${backendStatus.online ? 'online' : 'offline'}`} />
              <strong className="tile-value">{backendStatus.online ? 'Online' : 'Offline'}</strong>
            </div>
            <span className="tile-subtext">{sanitizedBaseUrl}</span>
          </div>

          <div className="diagnostic-tile">
            <span className="tile-label">BACKEND API VERSION</span>
            <div className="tile-value-row">
              <strong className="tile-value">{backendVersion}</strong>
            </div>
            <span className="tile-subtext">FastAPI Engine Gateway</span>
          </div>

          <div className="diagnostic-tile">
            <span className="tile-label">LAST HEALTH-CHECK ATTEMPT</span>
            <div className="tile-value-row">
              <strong className="tile-value">{backendStatus.lastChecked || 'Initial probe pending'}</strong>
            </div>
            <span className="tile-subtext">GET /health endpoint</span>
          </div>

          <div className="diagnostic-tile">
            <span className="tile-label">ACTIVE SMS CLASSIFIER</span>
            <div className="tile-value-row">
              <span className={`status-dot ${isModelLoaded ? 'online' : 'offline'}`} />
              <strong className="tile-value">{smsScannerStatus}</strong>
            </div>
            <span className="tile-subtext">Memory Pipeline</span>
          </div>
        </div>

        {/* Individual Engine Module Cards */}
        <div className="engine-modules-section">
          <h4 className="sub-section-title">Detection Engine Diagnostics</h4>
          <div className="modules-grid">
            {/* SMS Module */}
            <div className="engine-module-card">
              <div className="module-card-top">
                <div className="module-title-col">
                  <div className="module-icon-box blue"><MessageSquareText size={16} /></div>
                  <div>
                    <div className="module-name">SMS Fraud Scanner</div>
                    <div className="module-arch">
                      {backendStatus.data?.modules?.sms_scanner || (backendStatus.online ? 'TF-IDF + Logistic Regression' : 'Unavailable')}
                    </div>
                  </div>
                </div>
                <span className={`engine-status-badge ${isModelLoaded ? 'active' : 'offline'}`}>
                  {smsScannerStatus}
                </span>
              </div>
              <p className="module-desc">
                Multilingual text normalizer, Devanagari Unicode token extraction, and vocabulary feature classification across English, Hinglish, and Hindi.
              </p>
            </div>

            {/* URL Module */}
            <div className="engine-module-card">
              <div className="module-card-top">
                <div className="module-title-col">
                  <div className="module-icon-box purple"><Link2 size={16} /></div>
                  <div>
                    <div className="module-name">URL Phishing Scanner</div>
                    <div className="module-arch">
                      {backendStatus.data?.modules?.url_scanner || (backendStatus.online ? 'Structural Heuristic Rule-Based Engine' : 'Unavailable')}
                    </div>
                  </div>
                </div>
                <span className={`engine-status-badge ${backendStatus.online ? 'active' : 'offline'}`}>
                  {urlScannerStatus}
                </span>
              </div>
              <p className="module-desc">
                Multi-factor structural heuristic scanner analyzing subdomain brand spoofing, IP hostnames, Punycode homographs, and entropy.
              </p>
            </div>

            {/* UPI Module */}
            <div className="engine-module-card">
              <div className="module-card-top">
                <div className="module-title-col">
                  <div className="module-icon-box cyan"><Smartphone size={16} /></div>
                  <div>
                    <div className="module-name">UPI & Payment Protection</div>
                    <div className="module-arch">
                      {backendStatus.data?.modules?.payment_scanner || (backendStatus.online ? 'UPI & Payment Fraud Heuristic Engine' : 'Unavailable')}
                    </div>
                  </div>
                </div>
                <span className={`engine-status-badge ${backendStatus.online ? 'active' : 'offline'}`}>
                  {upiScannerStatus}
                </span>
              </div>
              <p className="module-desc">
                Indian digital payments engine checking VPA syntax, keyword spoofing, collect-request approval traps, and PIN-loss vectors.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* SECTION 2: MODEL INFORMATION & VERIFIED PIPELINE */}
      <div className="fintech-card settings-card">
        <div className="settings-card-header">
          <div className="settings-title-group">
            <div className="settings-title-row">
              <Cpu size={18} className="settings-icon purple" />
              <h3 className="settings-card-title">Model Specifications & Verified Pipeline</h3>
            </div>
            <p className="settings-card-desc">
              Architectural properties and verified runtime parameters of the active SMS classification model.
            </p>
          </div>
        </div>

        <div className="model-spec-table">
          <div className="spec-row">
            <span className="spec-key">Official Model Name</span>
            <span className="spec-val highlight">FraudLens AI Multilingual SMS Classifier</span>
          </div>
          <div className="spec-row align-top">
            <span className="spec-key">Model Architecture</span>
            <div className="spec-val pipeline-breakdown">
              <div><strong>Preprocessor:</strong> Multilingual SMS Preprocessor</div>
              <div><strong>FeatureUnion:</strong> Word TF-IDF [ngram_range=(1,2), sublinear_tf=True] + Character TF-IDF [analyzer=&apos;char_wb&apos;, ngram_range=(3,5), sublinear_tf=True]</div>
              <div><strong>Classifier:</strong> Logistic Regression [C=10.0, class_weight=None (unweighted), max_iter=1000]</div>
            </div>
          </div>
          <div className="spec-row">
            <span className="spec-key">Active Model Status</span>
            <span className="spec-val">
              {isModelLoaded ? (
                <span className="status-pill-text green"><CheckCircle2 size={13} /> Loaded & Operational in Backend RAM</span>
              ) : backendStatus.online ? (
                <span className="status-pill-text amber">Connected, but model not loaded</span>
              ) : (
                <span className="status-pill-text red">Unavailable (Backend Offline)</span>
              )}
            </span>
          </div>
          <div className="spec-row">
            <span className="spec-key">Supported Languages</span>
            <span className="spec-val">English, Hinglish (Romanized Hindi), Hindi (Devanagari Unicode U+0900–U+097F)</span>
          </div>
          <div className="spec-row">
            <span className="spec-key">Preprocessor Pipeline</span>
            <span className="spec-val">Multilingual Indic-aware cleaner, transliteration normalizer, URL/UPI token preservation</span>
          </div>
          <div className="spec-row">
            <span className="spec-key">Model Artifact SHA-256</span>
            <span className="spec-val muted">Not exposed by backend (Preserved in server checksum manifest)</span>
          </div>
          <div className="spec-row">
            <span className="spec-key">Internal Hyperparameters</span>
            <span className="spec-val muted">Not exposed by backend</span>
          </div>
          <div className="spec-row">
            <span className="spec-key">Offline Benchmark Metric</span>
            <span className="spec-val muted">Not exposed by backend (Documented in locked evaluation report)</span>
          </div>
        </div>
      </div>

      {/* SECTION 3: PRIVACY & DATA MANAGEMENT */}
      <div className="fintech-card settings-card">
        <div className="settings-card-header">
          <div className="settings-title-group">
            <div className="settings-title-row">
              <Lock size={18} className="settings-icon green" />
              <h3 className="settings-card-title">Privacy Policy & Local Data Management</h3>
            </div>
            <p className="settings-card-desc">
              Complete transparency regarding payload transmission, local storage, and history destruction.
            </p>
          </div>
        </div>

        <div className="privacy-disclosure-box">
          <div className="privacy-item">
            <div className="privacy-item-icon"><Server size={18} /></div>
            <div className="privacy-item-content">
              <strong>Data Transmission Notice</strong>
              <p>
                When you initiate an SMS, URL, or UPI payment scan, the entered message text, link, or VPA handle is transmitted via HTTP POST to the configured backend service (<code>/scan</code>, <code>/scan-url</code>, <code>/scan-payment</code>) for linguistic vectorization and heuristic evaluation. <em>We do not claim that no data leaves your browser.</em>
              </p>
            </div>
          </div>

          <div className="privacy-item">
            <div className="privacy-item-icon"><Database size={18} /></div>
            <div className="privacy-item-content">
              <strong>Browser Storage Policy</strong>
              <p>
                Your session scan history, threat predictions, risk scores, and timestamps are persisted locally in your browser&apos;s Web Storage (<code>window.localStorage</code> under the key <code>fraudlens_session_history</code>). This data is kept solely on your local device to power your session history and Risk Analytics.
              </p>
            </div>
          </div>
        </div>

        {/* Current Storage Summary & Clear History */}
        <div className="storage-management-row">
          <div className="storage-stat-block">
            <span className="storage-stat-label">LOCAL SESSION STORAGE</span>
            <div className="storage-stat-val">
              <strong>{scanHistoryCount}</strong> <span>recorded scan(s) in browser memory</span>
            </div>
            <span className="storage-stat-sub">Storage key: <code>fraudlens_session_history</code></span>
          </div>

          <div className="storage-actions-block">
            <button
              type="button"
              className="danger-btn"
              onClick={handleClearWithNotice}
              disabled={scanHistoryCount === 0}
              title={scanHistoryCount === 0 ? 'No history to clear' : 'Clear all local scan history'}
            >
              <Trash2 size={15} />
              <span>Clear Session History</span>
            </button>
          </div>
        </div>

        {clearNotice && (
          <div className="clear-notice-alert">
            <CheckCircle2 size={15} />
            <span>{clearNotice}</span>
          </div>
        )}
      </div>

      {/* SECTION 4: APPLICATION INFORMATION */}
      <div className="fintech-card settings-card">
        <div className="settings-card-header">
          <div className="settings-title-group">
            <div className="settings-title-row">
              <Info size={18} className="settings-icon amber" />
              <h3 className="settings-card-title">Application Information & Environment</h3>
            </div>
            <p className="settings-card-desc">
              Client build metadata, deployment environment, and gateway configuration.
            </p>
          </div>
        </div>

        <div className="app-info-grid">
          <div className="app-info-tile">
            <span className="info-tile-label">APPLICATION NAME</span>
            <strong className="info-tile-val">FraudLens AI</strong>
            <span className="info-tile-sub">Financial Security & Threat Screening</span>
          </div>

          <div className="app-info-tile">
            <span className="info-tile-label">FRONTEND PACKAGE VERSION</span>
            <strong className="info-tile-val">0.0.0</strong>
            <span className="info-tile-sub">Vite package.json metadata</span>
          </div>

          <div className="app-info-tile">
            <span className="info-tile-label">BACKEND API BASE URL</span>
            <strong className="info-tile-val monospace">{sanitizedBaseUrl}</strong>
            <span className="info-tile-sub">Configured FastAPI Endpoint</span>
          </div>

          <div className="app-info-tile">
            <span className="info-tile-label">CLIENT ARCHITECTURE</span>
            <strong className="info-tile-val">React 19 · Vite 8</strong>
            <span className="info-tile-sub">Recharts 3 · Lucide Icons</span>
          </div>
        </div>

        <div className="app-quick-links">
          <span className="quick-links-label">Quick Navigation:</span>
          <button type="button" className="quick-link-btn" onClick={() => onNavigate('overview')}>Overview</button>
          <button type="button" className="quick-link-btn" onClick={() => onNavigate('sms')}>SMS Scanner</button>
          <button type="button" className="quick-link-btn" onClick={() => onNavigate('url')}>URL Scanner</button>
          <button type="button" className="quick-link-btn" onClick={() => onNavigate('upi')}>UPI Protection</button>
          <button type="button" className="quick-link-btn" onClick={() => onNavigate('analytics')}>Risk Analytics</button>
          <button type="button" className="quick-link-btn" onClick={() => onNavigate('history')}>Scan History</button>
        </div>
      </div>
    </div>
  )
}
