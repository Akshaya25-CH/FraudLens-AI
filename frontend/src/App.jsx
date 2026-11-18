import { useState, useEffect, useCallback, lazy, Suspense } from 'react'
import {
  ShieldCheck, LayoutDashboard, MessageSquareText,
  Link2, Smartphone, Activity, History, Settings,
  AlertTriangle, CheckCircle2, ArrowRight,
  RefreshCw, Sparkles, FileText,
  AlertCircle, Code2, Lock, Globe,
  ShieldAlert, Info, Layers, CreditCard, QrCode, X
} from 'lucide-react'
import './App.css'

// Lazy-load heavier secondary views for optimal initial bundle footprint
const RiskAnalytics = lazy(() => import('./RiskAnalytics'))
const SettingsDiagnostics = lazy(() => import('./SettingsDiagnostics'))
const AdvancedScanHistory = lazy(() => import('./AdvancedScanHistory'))

// Valid hash-navigable tab identifiers
const VALID_TABS = new Set(['overview', 'sms', 'url', 'upi', 'analytics', 'history', 'settings'])

function getTabFromHash() {
  if (typeof window === 'undefined') return 'overview'
  const clean = window.location.hash.replace(/^#\/?/, '').trim().toLowerCase()
  return VALID_TABS.has(clean) ? clean : 'overview'
}

function TabLoadingFallback({ label = 'Loading section...' }) {
  return (
    <div className="tab-loading-container" role="status" aria-live="polite">
      <div className="tab-loading-spinner" />
      <span className="tab-loading-text">{label}</span>
    </div>
  )
}

const BACKEND_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

// Multilingual Sample SMS presets grouped by language (synthetic, privacy-safe)
const SAMPLE_SMS_BY_LANGUAGE = {
  English: [
    {
      id: 'en-scam-kyc',
      type: 'fraud',
      scenario: 'Fake KYC Update',
      label: 'Fake KYC PAN Suspension',
      text: 'Dear Customer, Your SBI bank account will be suspended today due to pending PAN KYC. Update immediately at https://sbi-kyc-update.test/verify'
    },
    {
      id: 'en-scam-elec',
      type: 'fraud',
      scenario: 'Electricity Disconnection Threat',
      label: 'Electricity Power Cut Threat',
      text: 'Urgent Notice: Your electricity power will be disconnected tonight at 9:30 PM because your previous bill was not updated. Call our power officer at 9876543210 immediately.'
    },
    {
      id: 'en-scam-cashback',
      type: 'fraud',
      scenario: 'Fake Cashback Reward',
      label: 'Fake Cashback Reward Phish',
      text: 'Congratulations! You have received a cashback reward of Rs 2,499 from PhonePe. Claim your direct bank refund now: https://cashback-reward-claim.test/pay'
    },
    {
      id: 'en-legit-bank',
      type: 'legit',
      scenario: 'Legitimate Bank Alert',
      label: 'Bank OTP Security Alert',
      text: 'Your OTP for transaction of Rs 1,450.00 at Amazon India is 492810. Valid for 5 mins. Do not share OTP with anyone including bank staff.'
    },
    {
      id: 'en-legit-salary',
      type: 'legit',
      scenario: 'Legitimate Salary Notification',
      label: 'Monthly Salary Credit',
      text: 'Dear Customer, Your salary of Rs 68,500.00 has been credited to A/C XX4921 on 30-Nov-2026 by Infosys Technologies Ltd. Available bal: Rs 82,140.00.'
    }
  ],
  Hinglish: [
    {
      id: 'hi-en-scam-upi',
      type: 'fraud',
      scenario: 'UPI Collect Request',
      label: 'UPI Collect Approval Fraud',
      text: 'Aapka Rs 50,000 ka cashback lottery approve ho gaya hai. Abhi approve request accept karein aur PIN dalein turant account me pane ke liye.'
    },
    {
      id: 'hi-en-scam-elec',
      type: 'fraud',
      scenario: 'Electricity Disconnection Threat',
      label: 'Bijli Bill Cut Threat',
      text: 'Priya Grahak, aapka bijli bill update nahi hua hai. Aaj raat 9:30 baje bijli ka connection kaat diya jayega. Turant is number 9876501234 par call karein.'
    },
    {
      id: 'hi-en-scam-kyc',
      type: 'fraud',
      scenario: 'Fake KYC Update',
      label: 'Bank Account Block KYC',
      text: 'Dear User, aapka bank khata block kar diya gaya hai KYC pending hone ke karan. Turant update karein link par: http://bank-kyc-verify.test/login'
    },
    {
      id: 'hi-en-legit-bank',
      type: 'legit',
      scenario: 'Legitimate Bank Alert',
      label: 'ATM Cash Withdrawal Notice',
      text: 'Aapke account XX7812 se Rs 2,000 ATM se withdraw hue hain 15-Nov ko. Agar yeh aapne nahi kiya toh turant customer care par sampark karein.'
    },
    {
      id: 'hi-en-legit-salary',
      type: 'legit',
      scenario: 'Legitimate Salary Notification',
      label: 'Monthly Salary Credit (Hinglish)',
      text: 'Aapka mahine ka vetan Rs 45,000 account XX8910 me safaltapoorvak credit ho gaya hai. Balance check karne ke liye mobile app kholein.'
    }
  ],
  'Hindi (Devanagari)': [
    {
      id: 'hi-scam-kyc',
      type: 'fraud',
      scenario: 'Fake KYC Update',
      label: 'केवाईसी खाता निलंबन (Fake KYC)',
      text: 'प्रिय ग्राहक, आपका बैंक खाता आज ब्लॉक कर दिया जाएगा क्योंकि आपका पैन कार्ड अपडेट नहीं है। तुरंत लिंक पर क्लिक करके केवाईसी पूरा करें: https://kyc-pan-update.test'
    },
    {
      id: 'hi-scam-elec',
      type: 'fraud',
      scenario: 'Electricity Disconnection Threat',
      label: 'बिजली कनेक्शन काटने की चेतावनी',
      text: 'सूचना: आपके पिछले महीने का बिजली बिल जमा नहीं हुआ है। आज रात 9:30 बजे बिजली कनेक्शन काट दिया जाएगा। तुरंत बिजली अधिकारी 9876543210 पर संपर्क करें।'
    },
    {
      id: 'hi-scam-cashback',
      type: 'fraud',
      scenario: 'UPI Collect / Fake Cashback',
      label: 'कैशबैक यूपीआई पिन स्कैम',
      text: 'बधाई हो! आपको मिला है रु 25,000 का सरकारी कैशबैक इनाम। अपने खाते में तुरंत राशि प्राप्त करने के लिए अपना यूपीआई पिन दर्ज करें।'
    },
    {
      id: 'hi-legit-bank',
      type: 'legit',
      scenario: 'Legitimate Bank Alert',
      label: 'बैंक खाता डेबिट सूचना',
      text: 'आपके बैंक खाते XX3456 से रु 1,500 की राशि यूपीआई द्वारा सफलतापूर्वक ट्रांसफर की गई है। आपका शेष बैलेंस रु 14,250 है।'
    },
    {
      id: 'hi-legit-salary',
      type: 'legit',
      scenario: 'Legitimate Salary Notification',
      label: 'मासिक वेतन क्रेडिट सूचना',
      text: 'प्रिय कर्मचारी, आपका नवंबर माह का वेतन रु 52,000 आपके खाते XX9012 में जमा कर दिया गया है। कंपनी एचआर विभाग।'
    }
  ]
}

// Flat sample list maintained for overview quick-action chip compatibility
const SAMPLE_MESSAGES = [
  SAMPLE_SMS_BY_LANGUAGE.English[0],
  SAMPLE_SMS_BY_LANGUAGE.English[1],
  SAMPLE_SMS_BY_LANGUAGE.English[3],
  SAMPLE_SMS_BY_LANGUAGE.English[4]
]

// Sample URLs for structural phishing testing
const SAMPLE_URLS = [
  {
    type: 'fraud',
    label: 'Subdomain Brand Spoof',
    url: 'https://paypal.com.verify-billing-update.xyz/login'
  },
  {
    type: 'fraud',
    label: 'Direct IP Hostname',
    url: 'http://192.168.1.100/admin/bank-login'
  },
  {
    type: 'fraud',
    label: 'Punycode IDN Homograph',
    url: 'http://xn--pple-43d.com/support/login'
  },
  {
    type: 'warning',
    label: 'URL Shortener Link',
    url: 'https://bit.ly/3xY7zQ'
  },
  {
    type: 'legit',
    label: 'Legitimate HTTPS Portal',
    url: 'https://www.google.com/search?q=financial+fraud+prevention'
  }
]

// Sample UPI & Indian payment fraud test cases
const SAMPLE_UPI_CASES = [
  {
    type: 'fraud',
    label: 'PIN to Receive Cashback',
    message: 'Congratulations! You have received cashback of Rs 2,500. Enter your 6-digit UPI PIN in Google Pay to claim money into your bank account.',
    vpa: 'rewards-dept@okhdfcbank'
  },
  {
    type: 'fraud',
    label: 'Scan QR Code to Receive Money',
    message: 'I am sending advance payment of Rs 15,000 for your furniture. Please scan this QR code with PhonePe to receive money directly into your account.',
    vpa: 'olx-buyer-pay@paytm'
  },
  {
    type: 'fraud',
    label: 'Collect Request Approval Trap',
    message: 'Dear customer, approve the collect request of Rs 4,999 in Paytm to accept payment from the buyer.',
    vpa: 'payment-accept@ybl'
  },
  {
    type: 'fraud',
    label: 'Fake Accidental Transfer Refund',
    message: 'Hello, I sent Rs 10,000 to your PhonePe by mistake instead of my brother. Please return and refund back to my UPI ID immediately.',
    vpa: 'rahul.kumar@okaxis'
  },
  {
    type: 'fraud',
    label: 'Suspicious VPA Keyword Spoofing',
    message: 'Pay your penalty fee to unblock your account before 6 PM.',
    vpa: 'sbi-customercare-refund@ybl'
  },
  {
    type: 'legit',
    label: 'Legitimate HDFC Debit Alert',
    message: 'A/C *1234 debited for Rs. 450.00 on 14-Nov-26 via UPI ref 123456789012. Bal: Rs. 12,450.50 - HDFC Bank',
    vpa: 'swiggy@icici'
  },
  {
    type: 'legit',
    label: 'Legitimate SBI Credit Notification',
    message: 'Your A/C *5678 credited with Rs. 5,000.00 on 14-Nov-26 by UPI ref 987654321098. - SBI',
    vpa: 'amit.verma@oksbi'
  }
]

function App() {
  const [activeTab, setActiveTab] = useState(() => getTabFromHash())
  const [toast, setToast] = useState(null)

  const showToast = useCallback((message, type = 'info') => {
    setToast({ id: Date.now(), message, type })
  }, [])

  // Auto-dismiss toast
  useEffect(() => {
    if (!toast) return
    const timer = setTimeout(() => {
      setToast(null)
    }, 4000)
    return () => clearTimeout(timer)
  }, [toast])

  // Synchronize URL hash with activeTab
  useEffect(() => {
    const currentClean = window.location.hash.replace(/^#\/?/, '').trim().toLowerCase()
    if (currentClean !== activeTab) {
      window.location.hash = `#${activeTab}`
    }
  }, [activeTab])

  // Handle browser back / forward navigation via popstate/hashchange
  useEffect(() => {
    function handleHashChange() {
      const nextTab = getTabFromHash()
      setActiveTab(nextTab)
    }
    window.addEventListener('hashchange', handleHashChange)
    return () => window.removeEventListener('hashchange', handleHashChange)
  }, [])

  // SMS Scanner State
  const [message, setMessage] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [showRawJson, setShowRawJson] = useState(false)
  const [selectedSmsLanguage, setSelectedSmsLanguage] = useState('All')

  // URL Scanner State
  const [urlInput, setUrlInput] = useState('')
  const [urlResult, setUrlResult] = useState(null)
  const [urlLoading, setUrlLoading] = useState(false)
  const [urlError, setUrlError] = useState('')
  const [showUrlRawJson, setShowUrlRawJson] = useState(false)

  // UPI Scanner State
  const [upiMessage, setUpiMessage] = useState('')
  const [upiVpa, setUpiVpa] = useState('')
  const [upiResult, setUpiResult] = useState(null)
  const [upiLoading, setUpiLoading] = useState(false)
  const [upiError, setUpiError] = useState('')
  const [showUpiRawJson, setShowUpiRawJson] = useState(false)

  // Shared System State
  const [backendStatus, setBackendStatus] = useState({ online: false, checking: true, data: null, lastChecked: null })
  const [scanHistory, setScanHistory] = useState(() => {
    try {
      const saved = localStorage.getItem('fraudlens_session_history')
      return saved ? JSON.parse(saved) : []
    } catch {
      return []
    }
  })

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

  // Check backend health on mount
  useEffect(() => {
    let active = true
    async function initCheck() {
      const nowTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
      try {
        const res = await fetch(`${BACKEND_BASE}/health`, { method: 'GET' })
        if (active) {
          if (res.ok) {
            const data = await res.json()
            setBackendStatus({ online: true, checking: false, data, lastChecked: nowTime })
          } else {
            setBackendStatus({ online: false, checking: false, data: null, lastChecked: nowTime })
          }
        }
      } catch {
        if (active) {
          setBackendStatus({ online: false, checking: false, data: null, lastChecked: nowTime })
        }
      }
    }
    initCheck()
    return () => {
      active = false
    }
  }, [])

  // Persist session history
  useEffect(() => {
    try {
      localStorage.setItem('fraudlens_session_history', JSON.stringify(scanHistory))
    } catch {
      // storage unavailable or full
    }
  }, [scanHistory])

  function extractErrorMessage(errData, fallback) {
    if (!errData || !errData.detail) return fallback
    if (typeof errData.detail === 'string') return errData.detail
    if (Array.isArray(errData.detail)) {
      return errData.detail.map((d) => d.msg || JSON.stringify(d)).join(', ')
    }
    return typeof errData.detail === 'object' ? JSON.stringify(errData.detail) : String(errData.detail)
  }

  // -------------------------------------------------------------------------
  // SMS Scan Handler
  // -------------------------------------------------------------------------
  async function handleScan(e) {
    if (e && e.preventDefault) e.preventDefault()
    const trimmed = message.trim()
    if (!trimmed) {
      setError('Please enter or paste an SMS text to analyze.')
      return
    }

    setLoading(true)
    setError('')
    setResult(null)

    try {
      const response = await fetch(`${BACKEND_BASE}/scan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: trimmed })
      })

      if (!response.ok) {
        let errMessage = 'Failed to analyze message.'
        try {
          const errData = await response.json()
          errMessage = extractErrorMessage(errData, errMessage)
        } catch {}
        throw new Error(errMessage)
      }

      const data = await response.json()
      setResult(data)
      showToast(`SMS scan complete: ${data.risk_level === 'POTENTIAL_FRAUD' ? 'Potential fraud pattern detected' : 'No fraud pattern detected'}.`, data.risk_level === 'POTENTIAL_FRAUD' ? 'info' : 'success')

      // Add to real session history
      const newEntry = {
        id: Date.now(),
        type: 'SMS',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        date: new Date().toLocaleDateString(),
        message: trimmed,
        prediction: data.prediction,
        risk_level: data.risk_level,
        model_score: data.model_score,
        recommendation: data.recommendation,
        explanation: data.explanation || (data.reasons && data.reasons[0])
      }

      setScanHistory((prev) => [newEntry, ...prev])
    } catch (err) {
      setError(`${err.message} Ensure the FastAPI backend is running on ${BACKEND_BASE}.`)
      showToast('SMS scan request failed. Backend may be offline.', 'error')
    } finally {
      setLoading(false)
    }
  }

  // -------------------------------------------------------------------------
  // URL Scan Handler
  // -------------------------------------------------------------------------
  async function handleUrlScan(e) {
    if (e && e.preventDefault) e.preventDefault()
    const trimmed = urlInput.trim()
    if (!trimmed) {
      setUrlError('Please enter or paste a URL to analyze.')
      return
    }

    setUrlLoading(true)
    setUrlError('')
    setUrlResult(null)

    try {
      const response = await fetch(`${BACKEND_BASE}/scan-url`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: trimmed })
      })

      if (!response.ok) {
        let errMessage = 'Failed to analyze URL structure.'
        try {
          const errData = await response.json()
          errMessage = extractErrorMessage(errData, errMessage)
        } catch {}
        throw new Error(errMessage)
      }

      const data = await response.json()
      setUrlResult(data)
      showToast(`URL scan complete: ${data.risk_category} structural risk.`, data.risk_category === 'HIGH' ? 'info' : 'success')

      // Add to real session history
      const newEntry = {
        id: Date.now(),
        type: 'URL',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        date: new Date().toLocaleDateString(),
        message: trimmed,
        prediction: data.risk_category === 'HIGH' ? 1 : 0,
        risk_level: data.risk_category === 'HIGH' ? 'HIGH_STRUCTURAL_RISK' : (data.risk_category === 'MEDIUM' ? 'MEDIUM_STRUCTURAL_RISK' : 'LOW_STRUCTURAL_RISK'),
        model_score: data.structural_risk_score,
        recommendation: data.recommendation,
        explanation: `${data.warning_count} structural warning sign(s) detected.`
      }

      setScanHistory((prev) => [newEntry, ...prev])
    } catch (err) {
      setUrlError(`${err.message} Ensure the FastAPI backend is running on ${BACKEND_BASE}.`)
      showToast('URL analysis request failed. Backend may be offline.', 'error')
    } finally {
      setUrlLoading(false)
    }
  }

  // -------------------------------------------------------------------------
  // UPI & Payment Scan Handler
  // -------------------------------------------------------------------------
  async function handleUpiScan(e) {
    if (e && e.preventDefault) e.preventDefault()
    const trimmedMsg = upiMessage.trim()
    const trimmedVpa = upiVpa.trim()

    if (!trimmedMsg && !trimmedVpa) {
      setUpiError('Please enter a payment message text or a UPI ID to analyze.')
      return
    }

    setUpiLoading(true)
    setUpiError('')
    setUpiResult(null)

    try {
      const response = await fetch(`${BACKEND_BASE}/scan-payment`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: trimmedMsg,
          upi_id: trimmedVpa || null
        })
      })

      if (!response.ok) {
        let errMessage = 'Failed to analyze UPI payment content.'
        try {
          const errData = await response.json()
          errMessage = extractErrorMessage(errData, errMessage)
        } catch {}
        throw new Error(errMessage)
      }

      const data = await response.json()
      setUpiResult(data)
      showToast(`UPI scan complete: ${data.risk_category} payment risk.`, data.risk_category === 'HIGH' ? 'info' : 'success')

      // Add to real session history
      const displayMsg = trimmedMsg || `UPI ID: ${trimmedVpa}`
      const newEntry = {
        id: Date.now(),
        type: 'UPI',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        date: new Date().toLocaleDateString(),
        message: displayMsg,
        prediction: data.risk_category === 'HIGH' ? 1 : 0,
        risk_level: data.risk_category === 'HIGH' ? 'HIGH_PAYMENT_RISK' : (data.risk_category === 'MEDIUM' ? 'MEDIUM_PAYMENT_RISK' : 'LOW_PAYMENT_RISK'),
        model_score: data.structural_risk_score,
        recommendation: data.recommendation,
        explanation: `${data.warning_count} payment warning signal(s) detected.`
      }

      setScanHistory((prev) => [newEntry, ...prev])
    } catch (err) {
      setUpiError(`${err.message} Ensure the FastAPI backend is running on ${BACKEND_BASE}.`)
      showToast('UPI verification request failed. Backend may be offline.', 'error')
    } finally {
      setUpiLoading(false)
    }
  }

  function handleSelectSample(sampleText) {
    setMessage(sampleText)
    setError('')
    setResult(null)
  }

  function handleSelectUrlSample(sampleUrl) {
    setUrlInput(sampleUrl)
    setUrlError('')
    setUrlResult(null)
  }

  function handleSelectUpiSample(sample) {
    setUpiMessage(sample.message || '')
    setUpiVpa(sample.vpa || '')
    setUpiError('')
    setUpiResult(null)
  }

  function clearHistory() {
    if (window.confirm('Clear all session scan history?')) {
      setScanHistory([])
      showToast('Session scan history successfully cleared.', 'success')
    }
  }

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

  // Calculate real analytics based purely on actual session scans (no fabricated numbers)
  const totalScans = scanHistory.length
  const fraudScans = scanHistory.filter((item) =>
    item.prediction === 1 ||
    item.risk_level === 'POTENTIAL_FRAUD' ||
    item.risk_level === 'HIGH_STRUCTURAL_RISK' ||
    item.risk_level === 'HIGH_PAYMENT_RISK'
  ).length
  const legitScans = scanHistory.filter((item) =>
    item.prediction === 0 ||
    item.risk_level === 'NO_FRAUD_PATTERN_DETECTED' ||
    item.risk_level === 'LOW_STRUCTURAL_RISK' ||
    item.risk_level === 'LOW_PAYMENT_RISK'
  ).length
  const avgScore = totalScans > 0
    ? (scanHistory.reduce((sum, item) => sum + (Number(item.model_score) || 0), 0) / totalScans).toFixed(1)
    : '0.0'

  const navItems = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'sms', label: 'SMS Scam Detection', icon: MessageSquareText },
    { id: 'url', label: 'URL Scanner', icon: Link2 },
    { id: 'upi', label: 'UPI Protection', icon: Smartphone },
    { id: 'analytics', label: 'Risk Analytics', icon: Activity },
    { id: 'history', label: 'Scan History', icon: History, count: scanHistory.length },
    { id: 'settings', label: 'Settings', icon: Settings }
  ]

  return (
    <div className="fintech-layout">
      {/* SIDEBAR NAVIGATION */}
      <aside className="fintech-sidebar">
        <div className="sidebar-brand">
          <div className="brand-badge">
            <ShieldCheck size={22} className="brand-shield" />
          </div>
          <div className="brand-text">
            <div className="brand-title">FraudLens <span className="brand-accent">AI</span></div>
            <div className="brand-subtitle">FINANCIAL SECURITY</div>
          </div>
        </div>

        <div className="sidebar-section-label">NAVIGATION</div>

        <nav className="sidebar-nav" aria-label="Main Navigation">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = activeTab === item.id
            return (
              <button
                key={item.id}
                type="button"
                className={`sidebar-nav-item ${isActive ? 'active' : ''}`}
                onClick={() => setActiveTab(item.id)}
                title={item.label}
                aria-label={item.label}
                aria-current={isActive ? 'page' : undefined}
              >
                <Icon size={18} className="nav-icon" />
                <span className="nav-label">{item.label}</span>
                {item.comingSoon && <span className="coming-soon-badge">Soon</span>}
                {item.count !== undefined && item.count > 0 && (
                  <span className="nav-count-pill">{item.count}</span>
                )}
                {isActive && <div className="active-indicator" />}
              </button>
            )
          })}
        </nav>

        {/* SIDEBAR FOOTER & SYSTEM HEALTH */}
        <div className="sidebar-footer">
          <div className={`health-card ${backendStatus.online ? 'online' : 'offline'}`}>
            <div className="health-card-header">
              <span className={`status-dot-pulse ${backendStatus.online ? 'pulse-green' : 'pulse-amber'}`} />
              <div className="health-card-title">
                {backendStatus.checking
                  ? 'Connecting...'
                  : backendStatus.online
                  ? 'Backend Connected'
                  : 'Backend Offline'}
              </div>
              <button
                type="button"
                className="health-refresh-btn"
                onClick={triggerManualHealthCheck}
                title="Refresh backend status"
              >
                <RefreshCw size={13} className={backendStatus.checking ? 'spin' : ''} />
              </button>
            </div>
            <div className="health-card-body">
              {backendStatus.online ? (
                <>
                  <div className="health-detail">
                    <span>SMS Model:</span>
                    <strong>TF-IDF + LogReg</strong>
                  </div>
                  <div className="health-detail">
                    <span>URL Analyzer:</span>
                    <strong>Lexical Parser</strong>
                  </div>
                  <div className="health-detail">
                    <span>UPI Engine:</span>
                    <strong>Rule-Based Heuristic</strong>
                  </div>
                  <div className="health-detail">
                    <span>Host:</span>
                    <code>{BACKEND_BASE.replace(/^https?:\/\//, '')}</code>
                  </div>
                </>
              ) : (
                <div className="health-hint">
                  Run <code>.\backend\venv\Scripts\python.exe backend\main.py</code>
                </div>
              )}
            </div>
          </div>

          <div className="sidebar-meta">
            <span>FraudLens AI · v2.2.0</span>
            <span>SMS + URL + UPI Fraud Engines</span>
          </div>
        </div>
      </aside>

      {/* MAIN CONTENT AREA */}
      <main className="fintech-main">
        {/* TOPBAR */}
        <header className="fintech-topbar">
          <div className="topbar-breadcrumb">
            <span className="breadcrumb-root">FraudLens</span>
            <span className="breadcrumb-separator">/</span>
            <span className="breadcrumb-active">
              {navItems.find((n) => n.id === activeTab)?.label || 'Overview'}
            </span>
          </div>

          <div className="topbar-actions">
            <div className="model-chip">
              <Sparkles size={14} className="chip-sparkle" />
              <span>
                {activeTab === 'url'
                  ? 'Engine: Structural Heuristics'
                  : activeTab === 'upi'
                  ? 'Engine: UPI Payment Heuristics'
                  : 'Model: Scikit-Learn TF-IDF'}
              </span>
            </div>

            <div className={`topbar-status-badge ${backendStatus.online ? 'online' : 'offline'}`}>
              <span className="status-dot-sm" />
              {backendStatus.online ? 'FastAPI 8000' : 'Backend Disconnected'}
            </div>
          </div>
        </header>

        {/* TAB 1: OVERVIEW DASHBOARD */}
        {activeTab === 'overview' && (
          <div className="dashboard-content">
            {/* HERO WELCOME BANNER */}
            <section className="fintech-hero">
              <div className="hero-text-block">
                <div className="hero-eyebrow">
                  <ShieldCheck size={14} /> AI & HEURISTIC FINANCIAL CRIME DEFENSE
                </div>
                <h1 className="hero-heading">
                  Intelligent detection against <span className="gradient-text">financial fraud & scams</span>.
                </h1>
                <p className="hero-description">
                  Real-time screening for phishing SMS, malicious URLs, collect-request traps, QR payment scams, and deceptive UPI handles.
                </p>
                <div className="hero-actions">
                  <button
                    className="primary-btn"
                    onClick={() => setActiveTab('sms')}
                  >
                    <MessageSquareText size={16} /> SMS Fraud Scanner
                  </button>
                  <button
                    className="secondary-btn"
                    onClick={() => setActiveTab('url')}
                  >
                    <Link2 size={16} /> URL Phishing Scanner
                  </button>
                  <button
                    className="secondary-btn"
                    onClick={() => setActiveTab('upi')}
                  >
                    <Smartphone size={16} /> UPI Protection
                  </button>
                  <button
                    className="secondary-btn"
                    onClick={() => setActiveTab('history')}
                  >
                    <History size={16} /> Scan Logs ({scanHistory.length})
                  </button>
                </div>
              </div>
              <div className="hero-graphic">
                <div className="shield-icon-halo">
                  <ShieldCheck size={52} className="shield-inner-icon" />
                </div>
              </div>
            </section>

            {/* REAL METRICS (BASED EXCLUSIVELY ON REAL SCAN HISTORY) */}
            <section className="metrics-grid">
              <div className="metric-card">
                <div className="metric-header">
                  <span className="metric-title">Session Scans</span>
                  <div className="metric-icon-box blue">
                    <Activity size={18} />
                  </div>
                </div>
                <div className="metric-value">{totalScans}</div>
                <div className="metric-caption">
                  {totalScans > 0 ? 'Verified via FastAPI endpoints' : 'No scans performed yet'}
                </div>
              </div>

              <div className="metric-card">
                <div className="metric-header">
                  <span className="metric-title">High Risk Flagged</span>
                  <div className="metric-icon-box red">
                    <AlertTriangle size={18} />
                  </div>
                </div>
                <div className="metric-value text-red">{fraudScans}</div>
                <div className="metric-caption">
                  {totalScans > 0
                    ? `${((fraudScans / totalScans) * 100).toFixed(0)}% of tested inputs`
                    : 'Awaiting inspection'}
                </div>
              </div>

              <div className="metric-card">
                <div className="metric-header">
                  <span className="metric-title">Clean / Low Risk</span>
                  <div className="metric-icon-box green">
                    <CheckCircle2 size={18} />
                  </div>
                </div>
                <div className="metric-value text-green">{legitScans}</div>
                <div className="metric-caption">
                  {totalScans > 0
                    ? `${((legitScans / totalScans) * 100).toFixed(0)}% of tested inputs`
                    : 'Awaiting inspection'}
                </div>
              </div>

              <div className="metric-card">
                <div className="metric-header">
                  <span className="metric-title">Avg. Risk Rating</span>
                  <div className="metric-icon-box purple">
                    <Sparkles size={18} />
                  </div>
                </div>
                <div className="metric-value">{avgScore}/100</div>
                <div className="metric-caption">
                  Derived directly from session scores
                </div>
              </div>
            </section>

            {/* DUAL COLUMN: QUICK SCANNER & CATEGORY INTEL */}
            <div className="dashboard-columns">
              {/* Quick Scan Card */}
              <div className="fintech-card flex-2">
                <div className="card-header">
                  <div>
                    <h3 className="card-title">Quick Security Scanner</h3>
                    <p className="card-subtitle">Test suspicious SMS, URLs, or payment notices in real-time</p>
                  </div>
                  <span className="card-badge-pill">Live Backend</span>
                </div>

                <div className="sample-chips-row">
                  <span className="chips-label">Try sample:</span>
                  <button
                    type="button"
                    className="sample-chip"
                    onClick={() => {
                      setMessage(SAMPLE_MESSAGES[0].text)
                      setActiveTab('sms')
                    }}
                  >
                    SMS: {SAMPLE_MESSAGES[0].label}
                  </button>
                  <button
                    type="button"
                    className="sample-chip"
                    onClick={() => {
                      setUrlInput(SAMPLE_URLS[0].url)
                      setActiveTab('url')
                    }}
                  >
                    URL: {SAMPLE_URLS[0].label}
                  </button>
                  <button
                    type="button"
                    className="sample-chip"
                    onClick={() => {
                      setUpiMessage(SAMPLE_UPI_CASES[0].message)
                      setUpiVpa(SAMPLE_UPI_CASES[0].vpa)
                      setActiveTab('upi')
                    }}
                  >
                    UPI: {SAMPLE_UPI_CASES[0].label}
                  </button>
                </div>

                <div className="quick-scan-box">
                  <textarea
                    rows={3}
                    className="fintech-textarea"
                    placeholder="Paste a suspicious SMS message, URL, or UPI collect notice here..."
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                  />
                  <div className="quick-scan-footer">
                    <span className="char-count">{message.length} chars</span>
                    <button
                      className="primary-btn"
                      disabled={loading || !message.trim()}
                      onClick={() => {
                        setActiveTab('sms')
                        handleScan()
                      }}
                    >
                      {loading ? 'Analyzing...' : 'Scan SMS'}
                      <ArrowRight size={16} />
                    </button>
                  </div>
                </div>
              </div>

              {/* Threat Categories Reference */}
              <div className="fintech-card flex-1">
                <div className="card-header">
                  <div>
                    <h3 className="card-title">Threat Coverage</h3>
                    <p className="card-subtitle">Active detection vectors</p>
                  </div>
                </div>

                <div className="threat-list">
                  <div className="threat-item">
                    <div className="threat-dot red" />
                    <div>
                      <strong>UPI PIN & Collect Request Traps</strong>
                      <p>Entering PIN to receive funds, QR code scams, reverse payment requests.</p>
                    </div>
                  </div>
                  <div className="threat-item">
                    <div className="threat-dot purple" />
                    <div>
                      <strong>URL Phishing & Spoofed Domains</strong>
                      <p>Punycode homographs, IP hosts, brand spoofing.</p>
                    </div>
                  </div>
                  <div className="threat-item">
                    <div className="threat-dot blue" />
                    <div>
                      <strong>KYC & Account Suspension Phishing</strong>
                      <p>Threats claiming bank or wallet deactivation.</p>
                    </div>
                  </div>
                  <div className="threat-item">
                    <div className="threat-dot amber" />
                    <div>
                      <strong>OTP Theft & Screen Sharing</strong>
                      <p>Demands for OTPs or installing remote desktop tools.</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* RECENT SESSION SCANS TABLE */}
            <div className="fintech-card">
              <div className="card-header">
                <div>
                  <h3 className="card-title">Recent Session Scan Activity</h3>
                  <p className="card-subtitle">Real scans performed during this active session</p>
                </div>
                {scanHistory.length > 0 && (
                  <button className="text-btn" onClick={clearHistory}>
                    Clear Logs
                  </button>
                )}
              </div>

              {scanHistory.length === 0 ? (
                <div className="empty-state-box">
                  <MessageSquareText size={36} className="empty-icon" />
                  <h4>No scans conducted yet in this session</h4>
                  <p>Run your first message, URL, or UPI payment scan above to view actual engine analysis.</p>
                  <div className="hero-actions" style={{ marginTop: '8px' }}>
                    <button
                      className="secondary-btn"
                      onClick={() => {
                        setMessage(SAMPLE_MESSAGES[0].text)
                        setActiveTab('sms')
                      }}
                    >
                      Test Sample SMS
                    </button>
                    <button
                      className="secondary-btn"
                      onClick={() => {
                        setUrlInput(SAMPLE_URLS[0].url)
                        setActiveTab('url')
                      }}
                    >
                      Test Sample URL
                    </button>
                    <button
                      className="secondary-btn"
                      onClick={() => {
                        setUpiMessage(SAMPLE_UPI_CASES[0].message)
                        setUpiVpa(SAMPLE_UPI_CASES[0].vpa)
                        setActiveTab('upi')
                      }}
                    >
                      Test Sample UPI
                    </button>
                  </div>
                </div>
              ) : (
                <div className="table-responsive">
                  <table className="fintech-table">
                    <thead>
                      <tr>
                        <th>Type</th>
                        <th>Time</th>
                        <th>Target Content</th>
                        <th>Risk Assessment</th>
                        <th>Score</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {scanHistory.slice(0, 6).map((item) => (
                        <tr key={item.id}>
                          <td>
                            <span className="type-pill">{item.type || 'SMS'}</span>
                          </td>
                          <td className="time-col">{item.timestamp}</td>
                          <td className="message-col">
                            <span className="message-snippet">{item.message}</span>
                          </td>
                          <td>
                            <span className={`risk-badge ${item.prediction === 1 ? 'danger' : 'safe'}`}>
                              {item.prediction === 1 ? (
                                <><AlertTriangle size={12} /> POTENTIAL RISK</>
                              ) : (
                                <><CheckCircle2 size={12} /> LOW RISK</>
                              )}
                            </span>
                          </td>
                          <td className="score-col">
                            <strong>{item.type === 'SMS' ? `${item.model_score}%` : `${item.model_score}/100`}</strong>
                          </td>
                          <td>
                            <button
                              className="table-action-btn"
                              onClick={() => handleInspectScan(item)}
                            >
                              Inspect
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 2: SMS SCAM DETECTION (FULL SCANNER) */}
        {activeTab === 'sms' && (
          <div className="scanner-container">
            <div className="scanner-header-section">
              <div className="scanner-eyebrow">
                <MessageSquareText size={14} /> SMS FRAUD SCREENING ENGINE
              </div>
              <h2 className="scanner-main-title">SMS Scam & Phishing Detection</h2>
              <p className="scanner-main-desc">
                Paste suspicious SMS messages, OTP requests, or bank alerts below. Our trained model extracts linguistic feature vectors using TF-IDF and classifies fraudulent intent across English, Hinglish, and Hindi (Devanagari).
              </p>
            </div>

            {/* SAMPLES SECTION */}
            <div className="samples-card">
              <div className="samples-header-row">
                <div className="samples-title">
                  <Sparkles size={15} /> Multilingual Test Presets:
                </div>
                <div className="language-filter-tabs">
                  {['All', 'English', 'Hinglish', 'Hindi (Devanagari)'].map((lang) => {
                    const count = lang === 'All'
                      ? Object.values(SAMPLE_SMS_BY_LANGUAGE).reduce((acc, list) => acc + list.length, 0)
                      : (SAMPLE_SMS_BY_LANGUAGE[lang] ? SAMPLE_SMS_BY_LANGUAGE[lang].length : 0)
                    return (
                      <button
                        key={lang}
                        type="button"
                        className={`lang-tab-btn ${selectedSmsLanguage === lang ? 'active' : ''}`}
                        onClick={() => setSelectedSmsLanguage(lang)}
                      >
                        <span>{lang}</span>
                        <span className="lang-tab-count">{count}</span>
                      </button>
                    )
                  })}
                </div>
              </div>

              <div className="samples-groups-container">
                {Object.entries(SAMPLE_SMS_BY_LANGUAGE)
                  .filter(([lang]) => selectedSmsLanguage === 'All' || selectedSmsLanguage === lang)
                  .map(([lang, samples]) => (
                    <div key={lang} className="samples-group-block">
                      <div className="samples-group-header">
                        <span className="group-lang-dot" />
                        <span>{lang}</span>
                        <span style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 500 }}>
                          ({samples.filter((s) => s.type === 'fraud').length} Scam, {samples.filter((s) => s.type === 'legit').length} Legitimate)
                        </span>
                      </div>
                      <div className="samples-grid">
                        {samples.map((sample) => (
                          <button
                            key={sample.id}
                            type="button"
                            className={`sample-pill ${sample.type}`}
                            onClick={() => handleSelectSample(sample.text)}
                            title={`Click to load into input (${sample.scenario}): "${sample.text}"`}
                          >
                            <span className={`pill-type-badge ${sample.type}`}>
                              {sample.type === 'fraud' ? 'Scam Example' : 'Legitimate Example'}
                            </span>
                            <span className="pill-indicator" />
                            <span className="pill-label">{sample.label}</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  ))}
              </div>
            </div>

            {/* SCAN FORM */}
            <div className="fintech-card scanner-form-card">
              <form onSubmit={handleScan}>
                <div className="input-group">
                  <div className="input-label-row">
                    <label htmlFor="sms-input">SUSPICIOUS MESSAGE TEXT</label>
                    <span className="input-help">Do not include your actual passwords or real PINs</span>
                  </div>

                  <textarea
                    id="sms-input"
                    rows={6}
                    className="fintech-textarea large"
                    placeholder="Paste the suspicious SMS, WhatsApp message, or email text here..."
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                  />

                  <div className="input-meta-bar">
                    <div className="meta-left">
                      <span>{message.length} characters</span>
                      <span>·</span>
                      <span>{message.trim() ? message.trim().split(/\s+/).length : 0} words</span>
                    </div>
                    {message && (
                      <button
                        type="button"
                        className="clear-link-btn"
                        onClick={() => {
                          setMessage('')
                          setResult(null)
                          setError('')
                        }}
                      >
                        Clear text
                      </button>
                    )}
                  </div>
                </div>

                <div className="form-submit-row">
                  <button
                    type="submit"
                    className="primary-btn submit-btn"
                    disabled={loading || !message.trim()}
                  >
                    {loading ? (
                      <>
                        <RefreshCw size={18} className="spin" />
                        Analyzing with ML Engine...
                      </>
                    ) : (
                      <>
                        <ShieldCheck size={18} />
                        Analyze for Fraud
                        <ArrowRight size={18} />
                      </>
                    )}
                  </button>
                </div>
              </form>

              {/* ERROR STATE */}
              {error && (
                <div className="fintech-alert danger">
                  <AlertCircle size={20} className="alert-icon" />
                  <div className="alert-body">
                    <strong>Scan Execution Error</strong>
                    <p>{error}</p>
                  </div>
                </div>
              )}

              {/* RESULT DISPLAY */}
              {result && (
                <div className={`analysis-result-panel ${result.risk_level === 'POTENTIAL_FRAUD' ? 'danger' : 'safe'}`}>
                  <div className="result-top-banner">
                    <div className="result-badge-col">
                      {result.risk_level === 'POTENTIAL_FRAUD' ? (
                        <div className="status-badge-lg danger">
                          <AlertTriangle size={22} />
                          <span>POTENTIAL FRAUD DETECTED</span>
                        </div>
                      ) : (
                        <div className="status-badge-lg safe">
                          <CheckCircle2 size={22} />
                          <span>NO FRAUD PATTERN DETECTED</span>
                        </div>
                      )}
                      <div className="result-subtext">
                        Analysis performed via TF-IDF + Logistic Regression classifier
                      </div>
                    </div>

                    <div className="result-score-box">
                      <span className="score-label">Model Fraud Score</span>
                      <div className="score-number-row">
                        <span className="score-val">{result.model_score}%</span>
                      </div>
                      <div className="score-bar-bg">
                        <div
                          className={`score-bar-fill ${result.risk_level === 'POTENTIAL_FRAUD' ? 'danger' : 'safe'}`}
                          style={{ width: `${Math.min(100, Math.max(5, result.model_score))}%` }}
                        />
                      </div>
                      <span className="score-disclaimer">
                        Estimated probability. Does not guarantee safety.
                      </span>
                    </div>
                  </div>

                  {/* DETAILS GRID */}
                  <div className="result-details-grid">
                    <div className="detail-panel">
                      <div className="detail-panel-header">
                        <FileText size={16} /> Model Explanation
                      </div>
                      <p className="detail-text">
                        {result.explanation || (result.reasons && result.reasons[0]) || 'Analysis completed by model.'}
                      </p>
                    </div>

                    <div className="detail-panel">
                      <div className="detail-panel-header">
                        <Lock size={16} /> Recommended Action
                      </div>
                      <p className="detail-text">{result.recommendation}</p>
                    </div>
                  </div>

                  {/* RAW API PAYLOAD TOGGLE */}
                  <div className="raw-payload-section">
                    <button
                      type="button"
                      className="raw-payload-toggle"
                      onClick={() => setShowRawJson(!showRawJson)}
                    >
                      <Code2 size={14} />
                      {showRawJson ? 'Hide Raw API Response' : 'Inspect Raw FastAPI JSON Response'}
                    </button>
                    {showRawJson && (
                      <pre className="raw-json-block">
                        {JSON.stringify(result, null, 2)}
                      </pre>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 3: URL PHISHING SCANNER */}
        {activeTab === 'url' && (
          <div className="scanner-container">
            <div className="scanner-header-section">
              <div className="scanner-eyebrow">
                <Link2 size={14} /> URL PHISHING & STRUCTURAL RISK ANALYZER
              </div>
              <h2 className="scanner-main-title">URL Phishing & Deception Scanner</h2>
              <p className="scanner-main-desc">
                Paste any suspicious hyperlink, SMS redirect, or payment URL below. Our offline rule-based analyzer evaluates syntactic anomalies, punycode lookalikes, IP hostnames, embedded userinfo, and deceptive subdomain structures without contacting external servers.
              </p>
            </div>

            {/* SAMPLES SECTION */}
            <div className="samples-card">
              <div className="samples-title">
                <Sparkles size={15} /> Quick Test URL Samples:
              </div>
              <div className="samples-grid">
                {SAMPLE_URLS.map((sample, idx) => (
                  <button
                    key={idx}
                    type="button"
                    className={`sample-pill ${sample.type === 'fraud' ? 'fraud' : (sample.type === 'warning' ? 'warning' : 'legit')}`}
                    onClick={() => handleSelectUrlSample(sample.url)}
                  >
                    <span className="pill-indicator" />
                    <span className="pill-label">{sample.label}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* URL SCAN FORM */}
            <div className="fintech-card scanner-form-card">
              <form onSubmit={handleUrlScan}>
                <div className="input-group">
                  <div className="input-label-row">
                    <label htmlFor="url-input">TARGET HYPERLINK OR DOMAIN</label>
                    <span className="input-help">Analyzed statically without initiating network connections</span>
                  </div>

                  <div className="url-input-wrapper">
                    <Globe size={18} className="url-input-icon" />
                    <input
                      id="url-input"
                      type="text"
                      className="fintech-input url-field"
                      placeholder="e.g. https://paypal.com.verify-billing-update.xyz/login or http://192.168.1.1/login"
                      value={urlInput}
                      onChange={(e) => setUrlInput(e.target.value)}
                    />
                    {urlInput && (
                      <button
                        type="button"
                        className="url-clear-btn"
                        onClick={() => {
                          setUrlInput('')
                          setUrlResult(null)
                          setUrlError('')
                        }}
                      >
                        Clear
                      </button>
                    )}
                  </div>
                </div>

                <div className="form-submit-row" style={{ marginTop: '16px' }}>
                  <button
                    type="submit"
                    className="primary-btn submit-btn"
                    disabled={urlLoading || !urlInput.trim()}
                  >
                    {urlLoading ? (
                      <>
                        <RefreshCw size={18} className="spin" />
                        Analyzing URL Structure...
                      </>
                    ) : (
                      <>
                        <Link2 size={18} />
                        Analyze URL for Phishing
                        <ArrowRight size={18} />
                      </>
                    )}
                  </button>
                </div>
              </form>

              {/* ERROR STATE */}
              {urlError && (
                <div className="fintech-alert danger">
                  <AlertCircle size={20} className="alert-icon" />
                  <div className="alert-body">
                    <strong>URL Analysis Error</strong>
                    <p>{urlError}</p>
                  </div>
                </div>
              )}

              {/* URL RESULT DISPLAY */}
              {urlResult && (
                <div className={`analysis-result-panel ${urlResult.risk_category === 'HIGH' ? 'danger' : (urlResult.risk_category === 'MEDIUM' ? 'warning' : 'safe')}`}>
                  <div className="result-top-banner">
                    <div className="result-badge-col">
                      {urlResult.risk_category === 'HIGH' ? (
                        <div className="status-badge-lg danger">
                          <ShieldAlert size={22} />
                          <span>HIGH STRUCTURAL RISK</span>
                        </div>
                      ) : urlResult.risk_category === 'MEDIUM' ? (
                        <div className="status-badge-lg warning">
                          <AlertTriangle size={22} />
                          <span>MEDIUM STRUCTURAL RISK</span>
                        </div>
                      ) : (
                        <div className="status-badge-lg safe">
                          <CheckCircle2 size={22} />
                          <span>LOW STRUCTURAL RISK</span>
                        </div>
                      )}
                      <div className="result-subtext">
                        Evaluated via explainable syntactic & lexical heuristic rules
                      </div>
                    </div>

                    <div className="result-score-box">
                      <span className="score-label">Structural Risk Score</span>
                      <div className="score-number-row">
                        <span className="score-val">{urlResult.structural_risk_score}/100</span>
                      </div>
                      <div className="score-bar-bg">
                        <div
                          className={`score-bar-fill ${urlResult.risk_category === 'HIGH' ? 'danger' : (urlResult.risk_category === 'MEDIUM' ? 'warning' : 'safe')}`}
                          style={{ width: `${Math.min(100, Math.max(5, urlResult.structural_risk_score))}%` }}
                        />
                      </div>
                      <span className="score-disclaimer">
                        Rule-based heuristic score (Not an ML probability).
                      </span>
                    </div>
                  </div>

                  {/* WARNING SIGNS LIST */}
                  <div className="url-warnings-section">
                    <div className="section-subtitle-bar">
                      <Layers size={16} />
                      <strong>Detected Warning Signs ({urlResult.warning_count || 0})</strong>
                    </div>

                    {(!urlResult.warning_signs || urlResult.warning_signs.length === 0) ? (
                      <div className="clean-signals-card">
                        <CheckCircle2 size={18} className="clean-icon" />
                        <span>No severe structural anomalies or deceptive patterns detected in the URL syntax.</span>
                      </div>
                    ) : (
                      <div className="warning-signs-grid">
                        {urlResult.warning_signs.map((sign, idx) => (
                          <div key={idx} className={`warning-sign-card ${sign.severity.toLowerCase()}`}>
                            <div className="warning-sign-top">
                              <span className={`severity-tag ${sign.severity.toLowerCase()}`}>
                                {sign.severity}
                              </span>
                              <strong className="warning-sign-title">{sign.title}</strong>
                              <span className="points-pill">+{sign.points} pts</span>
                            </div>
                            <p className="warning-sign-desc">{sign.description}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* EXTRACTED STRUCTURAL COMPONENTS */}
                  {urlResult.structural_features && (
                    <div className="features-section">
                      <div className="section-subtitle-bar">
                        <Globe size={16} />
                        <strong>Extracted Structural Components</strong>
                      </div>
                      <div className="features-pill-grid">
                        <div className="feature-pill">
                          <span className="feature-label">Scheme:</span>
                          <code>{urlResult.structural_features.scheme || 'none'}</code>
                        </div>
                        <div className="feature-pill">
                          <span className="feature-label">Hostname:</span>
                          <code>{urlResult.structural_features.hostname || 'none'}</code>
                        </div>
                        <div className="feature-pill">
                          <span className="feature-label">Root Domain:</span>
                          <code>{urlResult.structural_features.root_domain || 'none'}</code>
                        </div>
                        <div className="feature-pill">
                          <span className="feature-label">Subdomains:</span>
                          <code>{urlResult.structural_features.subdomains?.join('.') || 'none'}</code>
                        </div>
                        <div className="feature-pill">
                          <span className="feature-label">Port:</span>
                          <code>{urlResult.structural_features.port ? urlResult.structural_features.port : 'Default (80/443)'}</code>
                        </div>
                        <div className="feature-pill">
                          <span className="feature-label">IP Host:</span>
                          <strong>{urlResult.structural_features.has_ip_address ? 'Yes (Risky)' : 'No'}</strong>
                        </div>
                        <div className="feature-pill">
                          <span className="feature-label">Shortener:</span>
                          <strong>{urlResult.structural_features.is_shortener ? 'Yes' : 'No'}</strong>
                        </div>
                        <div className="feature-pill">
                          <span className="feature-label">Punycode:</span>
                          <strong>{urlResult.structural_features.is_punycode ? 'Yes (Homograph Risk)' : 'No'}</strong>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* RECOMMENDATION & DISCLAIMER */}
                  <div className="result-details-grid">
                    <div className="detail-panel">
                      <div className="detail-panel-header">
                        <Lock size={16} /> Security Recommendation
                      </div>
                      <p className="detail-text">{urlResult.recommendation}</p>
                    </div>

                    <div className="detail-panel">
                      <div className="detail-panel-header">
                        <Info size={16} /> Verification Disclaimer
                      </div>
                      <p className="detail-text">{urlResult.disclaimer}</p>
                    </div>
                  </div>

                  {/* RAW API PAYLOAD TOGGLE */}
                  <div className="raw-payload-section">
                    <button
                      type="button"
                      className="raw-payload-toggle"
                      onClick={() => setShowUrlRawJson(!showUrlRawJson)}
                    >
                      <Code2 size={14} />
                      {showUrlRawJson ? 'Hide Raw API Response' : 'Inspect Raw FastAPI JSON Response'}
                    </button>
                    {showUrlRawJson && (
                      <pre className="raw-json-block">
                        {JSON.stringify(urlResult, null, 2)}
                      </pre>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 4: UPI & PAYMENT FRAUD SCANNER (NEW MODULE) */}
        {activeTab === 'upi' && (
          <div className="scanner-container">
            <div className="scanner-header-section">
              <div className="scanner-eyebrow">
                <Smartphone size={14} /> UPI & DIGITAL PAYMENT FRAUD DEFENSE
              </div>
              <h2 className="scanner-main-title">UPI & Payment Scam Detection</h2>
              <p className="scanner-main-desc">
                Analyze payment requests, transaction alerts, QR payment instructions, and UPI IDs (VPAs). Detects reverse payment deception, collect-request traps, QR code scams, and deceptive customer care handles using explainable heuristic rules without contacting live banking gateways.
              </p>
            </div>

            {/* SAMPLES SECTION */}
            <div className="samples-card">
              <div className="samples-title">
                <Sparkles size={15} /> Quick Test Indian UPI Scenarios:
              </div>
              <div className="samples-grid">
                {SAMPLE_UPI_CASES.map((sample, idx) => (
                  <button
                    key={idx}
                    type="button"
                    className={`sample-pill ${sample.type === 'fraud' ? 'fraud' : 'legit'}`}
                    onClick={() => handleSelectUpiSample(sample)}
                  >
                    <span className="pill-indicator" />
                    <span className="pill-label">{sample.label}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* UPI SCAN FORM */}
            <div className="fintech-card scanner-form-card">
              <form onSubmit={handleUpiScan}>
                <div className="input-group">
                  <div className="input-label-row">
                    <label htmlFor="upi-message-input">PAYMENT NOTIFICATION / SMS / WHATSAPP TEXT</label>
                    <span className="input-help">Analyzed statically; never connects to live bank accounts</span>
                  </div>

                  <textarea
                    id="upi-message-input"
                    rows={4}
                    className="fintech-textarea"
                    placeholder="e.g. Enter your UPI PIN to claim cashback of Rs 2,500 in Google Pay..."
                    value={upiMessage}
                    onChange={(e) => setUpiMessage(e.target.value)}
                  />
                </div>

                <div className="input-group" style={{ marginTop: '14px' }}>
                  <div className="input-label-row">
                    <label htmlFor="upi-vpa-input">TARGET UPI ID / VPA (OPTIONAL)</label>
                    <span className="input-help">e.g. merchant-support-refund@ybl or user@okhdfcbank</span>
                  </div>

                  <div className="url-input-wrapper">
                    <CreditCard size={18} className="url-input-icon" />
                    <input
                      id="upi-vpa-input"
                      type="text"
                      className="fintech-input url-field"
                      placeholder="e.g. sbi-refund-care@ybl or buyer@paytm"
                      value={upiVpa}
                      onChange={(e) => setUpiVpa(e.target.value)}
                    />
                  </div>
                </div>

                <div className="input-meta-bar" style={{ marginTop: '6px' }}>
                  <div className="meta-left">
                    <span>{upiMessage.length} message chars</span>
                    <span>·</span>
                    <span>{upiVpa ? `VPA: ${upiVpa}` : 'No VPA specified'}</span>
                  </div>
                  {(upiMessage || upiVpa) && (
                    <button
                      type="button"
                      className="clear-link-btn"
                      onClick={() => {
                        setUpiMessage('')
                        setUpiVpa('')
                        setUpiResult(null)
                        setUpiError('')
                      }}
                    >
                      Clear all fields
                    </button>
                  )}
                </div>

                <div className="form-submit-row">
                  <button
                    type="submit"
                    className="primary-btn submit-btn"
                    disabled={upiLoading || (!upiMessage.trim() && !upiVpa.trim())}
                  >
                    {upiLoading ? (
                      <>
                        <RefreshCw size={18} className="spin" />
                        Analyzing UPI Patterns...
                      </>
                    ) : (
                      <>
                        <Smartphone size={18} />
                        Analyze Payment for Fraud
                        <ArrowRight size={18} />
                      </>
                    )}
                  </button>
                </div>
              </form>

              {/* ERROR STATE */}
              {upiError && (
                <div className="fintech-alert danger">
                  <AlertCircle size={20} className="alert-icon" />
                  <div className="alert-body">
                    <strong>Payment Analysis Error</strong>
                    <p>{upiError}</p>
                  </div>
                </div>
              )}

              {/* UPI RESULT DISPLAY */}
              {upiResult && (
                <div className={`analysis-result-panel ${upiResult.risk_category === 'HIGH' ? 'danger' : (upiResult.risk_category === 'MEDIUM' ? 'warning' : 'safe')}`}>
                  <div className="result-top-banner">
                    <div className="result-badge-col">
                      {upiResult.risk_category === 'HIGH' ? (
                        <div className="status-badge-lg danger">
                          <ShieldAlert size={22} />
                          <span>HIGH PAYMENT RISK DETECTED</span>
                        </div>
                      ) : upiResult.risk_category === 'MEDIUM' ? (
                        <div className="status-badge-lg warning">
                          <AlertTriangle size={22} />
                          <span>MEDIUM PAYMENT RISK DETECTED</span>
                        </div>
                      ) : (
                        <div className="status-badge-lg safe">
                          <CheckCircle2 size={22} />
                          <span>LOW PAYMENT RISK DETECTED</span>
                        </div>
                      )}
                      <div className="result-subtext">
                        Evaluated via explainable Indian UPI protocol & reverse payment rules
                      </div>
                    </div>

                    <div className="result-score-box">
                      <span className="score-label">Payment Risk Score</span>
                      <div className="score-number-row">
                        <span className="score-val">{upiResult.structural_risk_score}/100</span>
                      </div>
                      <div className="score-bar-bg">
                        <div
                          className={`score-bar-fill ${upiResult.risk_category === 'HIGH' ? 'danger' : (upiResult.risk_category === 'MEDIUM' ? 'warning' : 'safe')}`}
                          style={{ width: `${Math.min(100, Math.max(5, upiResult.structural_risk_score))}%` }}
                        />
                      </div>
                      <span className="score-disclaimer">
                        Rule-based heuristic score (Not an ML probability).
                      </span>
                    </div>
                  </div>

                  {/* UPI VPA EVALUATION CARDS */}
                  {upiResult.vpa_evaluations && upiResult.vpa_evaluations.length > 0 && (
                    <div className="features-section">
                      <div className="section-subtitle-bar">
                        <CreditCard size={16} />
                        <strong>UPI ID (VPA) Format Evaluation ({upiResult.vpa_evaluations.length})</strong>
                      </div>
                      <div className="vpa-eval-list">
                        {upiResult.vpa_evaluations.map((vpa, i) => (
                          <div key={i} className="vpa-eval-card">
                            <div className="vpa-eval-header">
                              <span className="vpa-text"><code>{vpa.vpa}</code></span>
                              <span className={`risk-badge ${vpa.has_suspicious_keywords ? 'danger' : (vpa.is_valid_format ? 'safe' : 'warning')}`}>
                                {vpa.has_suspicious_keywords ? 'Suspicious Keyword VPA' : (vpa.is_valid_format ? 'Valid Format' : 'Non-Standard Syntax')}
                              </span>
                            </div>
                            <ul className="vpa-observations">
                              {vpa.observations.map((obs, j) => (
                                <li key={j}>{obs}</li>
                              ))}
                            </ul>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* WARNING SIGNS LIST */}
                  <div className="url-warnings-section">
                    <div className="section-subtitle-bar">
                      <Layers size={16} />
                      <strong>Detected Payment Warning Signals ({upiResult.warning_count || 0})</strong>
                    </div>

                    {(!upiResult.warning_signs || upiResult.warning_signs.length === 0) ? (
                      <div className="clean-signals-card">
                        <CheckCircle2 size={18} className="clean-icon" />
                        <span>No deceptive reverse payment patterns, collect-request traps, or PIN requests detected.</span>
                      </div>
                    ) : (
                      <div className="warning-signs-grid">
                        {upiResult.warning_signs.map((sign, idx) => (
                          <div key={idx} className={`warning-sign-card ${sign.severity.toLowerCase()}`}>
                            <div className="warning-sign-top">
                              <span className={`severity-tag ${sign.severity.toLowerCase()}`}>
                                {sign.severity}
                              </span>
                              <strong className="warning-sign-title">{sign.title}</strong>
                              <span className="points-pill">+{sign.points} pts</span>
                            </div>
                            <p className="warning-sign-desc">{sign.description}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* UPI GOLDEN RULES CALLOUT */}
                  <div className="golden-rules-card">
                    <div className="golden-rules-header">
                      <QrCode size={18} className="golden-icon" />
                      <strong>UPI Safety Golden Rules (NPCI Guidelines)</strong>
                    </div>
                    <div className="golden-rules-grid">
                      <div className="golden-rule-item">
                        <div className="rule-num">1</div>
                        <div>
                          <strong>PIN is NEVER for Receiving</strong>
                          <p>Entering your UPI PIN always deducts money from your account. You NEVER enter a PIN to receive cashback or refunds.</p>
                        </div>
                      </div>
                      <div className="golden-rule-item">
                        <div className="rule-num">2</div>
                        <div>
                          <strong>QR Codes are for Sending Only</strong>
                          <p>Scanning a QR code creates an outgoing payment. Never scan QR codes sent by buyers on OLX/Marketplace to accept money.</p>
                        </div>
                      </div>
                      <div className="golden-rule-item">
                        <div className="rule-num">3</div>
                        <div>
                          <strong>Verify Balance Inside Bank App</strong>
                          <p>Never trust SMS credit notifications from unknown mobile numbers. Check your real passbook inside your official bank app.</p>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* RECOMMENDATION & DISCLAIMER */}
                  <div className="result-details-grid">
                    <div className="detail-panel">
                      <div className="detail-panel-header">
                        <Lock size={16} /> Security Recommendation
                      </div>
                      <p className="detail-text">{upiResult.recommendation}</p>
                    </div>

                    <div className="detail-panel">
                      <div className="detail-panel-header">
                        <Info size={16} /> Verification Disclaimer
                      </div>
                      <p className="detail-text">{upiResult.disclaimer}</p>
                    </div>
                  </div>

                  {/* RAW API PAYLOAD TOGGLE */}
                  <div className="raw-payload-section">
                    <button
                      type="button"
                      className="raw-payload-toggle"
                      onClick={() => setShowUpiRawJson(!showUpiRawJson)}
                    >
                      <Code2 size={14} />
                      {showUpiRawJson ? 'Hide Raw API Response' : 'Inspect Raw FastAPI JSON Response'}
                    </button>
                    {showUpiRawJson && (
                      <pre className="raw-json-block">
                        {JSON.stringify(upiResult, null, 2)}
                      </pre>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 5: RISK ANALYTICS */}
        {activeTab === 'analytics' && (
          <Suspense fallback={<TabLoadingFallback label="Loading Risk Analytics & Visualizations..." />}>
            <RiskAnalytics
              scanHistory={scanHistory}
              onNavigate={(tab) => setActiveTab(tab)}
            />
          </Suspense>
        )}

        {/* TAB 6: SCAN HISTORY */}
        {activeTab === 'history' && (
          <Suspense fallback={<TabLoadingFallback label="Loading Session Scan History..." />}>
            <AdvancedScanHistory
              scanHistory={scanHistory}
              onClearHistory={clearHistory}
              onInspectScan={handleInspectScan}
              onNavigate={(tab) => setActiveTab(tab)}
              onToast={showToast}
            />
          </Suspense>
        )}

        {/* TAB 7: SETTINGS & DIAGNOSTICS */}
        {activeTab === 'settings' && (
          <Suspense fallback={<TabLoadingFallback label="Loading System Settings & Diagnostics..." />}>
            <SettingsDiagnostics
              backendStatus={backendStatus}
              onRefreshHealth={async () => {
                await triggerManualHealthCheck()
                showToast('Backend health check refreshed.', 'info')
              }}
              backendBaseUrl={BACKEND_BASE}
              scanHistoryCount={scanHistory.length}
              onClearHistory={clearHistory}
              onNavigate={(tab) => setActiveTab(tab)}
              onToast={showToast}
            />
          </Suspense>
        )}

        {/* FOOTER */}
        <footer className="fintech-footer">
          <div className="footer-left">
            <span>© 2026 FraudLens AI</span>
            <span>·</span>
            <span>Intelligent Financial Crime Defense</span>
          </div>
          <div className="footer-right">
            <span>Connected: <code>{BACKEND_BASE}</code></span>
            <span>·</span>
            <span>Endpoints: <code>/scan</code>, <code>/scan-url</code> & <code>/scan-payment</code></span>
          </div>
        </footer>

        {/* TOAST NOTIFICATION BANNER */}
        {toast && (
          <div
            className={`fintech-toast toast-${toast.type}`}
            role="status"
            aria-live="polite"
          >
            <div className="toast-content">
              {toast.type === 'success' && <CheckCircle2 size={16} className="toast-icon success" />}
              {toast.type === 'error' && <AlertCircle size={16} className="toast-icon error" />}
              {toast.type === 'info' && <Info size={16} className="toast-icon info" />}
              <span className="toast-message">{toast.message}</span>
            </div>
            <button
              type="button"
              className="toast-close-btn"
              onClick={() => setToast(null)}
              title="Dismiss notification"
              aria-label="Dismiss notification"
            >
              <X size={14} />
            </button>
          </div>
        )}
      </main>
    </div>
  )
}

export default App
