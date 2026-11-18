import { useState, useMemo } from 'react'
import {
  History, Search, Download, RotateCcw, X,
  Clock, AlertTriangle, CheckCircle2, ShieldAlert,
  ArrowUpDown, Filter, Eye, MessageSquareText,
  Link2, Smartphone
} from 'lucide-react'

// Risk Tier Helper
function getRiskTier(item) {
  const level = (item?.risk_level || '').toUpperCase()
  if (level.includes('HIGH') || level === 'POTENTIAL_FRAUD' || item?.prediction === 1) {
    return 'HIGH'
  }
  if (level.includes('MEDIUM')) {
    return 'MEDIUM'
  }
  return 'LOW'
}

// Extract and Validate Timestamp Helper
function extractValidTimestamp(item) {
  if (!item) return null

  const rawTs = item.timestamp
  if (rawTs === null || rawTs === undefined || rawTs === '') {
    return null
  }

  // 1. Date instance
  if (rawTs instanceof Date && !isNaN(rawTs.getTime())) {
    return rawTs.getTime()
  }

  // 2. Numeric epoch ms
  if (typeof rawTs === 'number' && Number.isFinite(rawTs) && rawTs > 1000000000000) {
    return rawTs
  }

  // 3. String timestamp
  if (typeof rawTs === 'string') {
    const trimmed = rawTs.trim()
    if (!trimmed) return null

    // Numeric string of epoch ms (e.g. "1731940000000")
    if (/^\d{13,}$/.test(trimmed)) {
      const num = Number(trimmed)
      if (Number.isFinite(num) && num > 1000000000000) return num
    }

    // ISO string or parseable RFC2822 datetime
    const parsed = Date.parse(trimmed)
    if (!isNaN(parsed) && parsed > 1000000000000) {
      return parsed
    }

    // Combined with item.date if present
    if (item.date && typeof item.date === 'string') {
      const combined = Date.parse(`${item.date.trim()} ${trimmed}`)
      if (!isNaN(combined) && combined > 1000000000000) {
        return combined
      }
    }

    // Standard session schema (App.jsx): verified time format + item.id epoch timestamp
    const timeCheck = Date.parse(`1970-01-01 ${trimmed}`)
    if (!isNaN(timeCheck)) {
      if (typeof item.id === 'number' && Number.isFinite(item.id) && item.id > 1000000000000) {
        return item.id
      }
    }

    return null
  }

  return null
}

// Date Match Helper (checks verified timestamp against active filter)
function matchesDateFilter(item, filter, nowMs) {
  // When All Time is selected, retain records even if their timestamps are missing or invalid
  if (filter === 'ALL') return true

  // When Today, Last 7 Days, or Last 30 Days is selected, exclude records with missing or invalid timestamps
  const itemTime = extractValidTimestamp(item)
  if (!itemTime) return false

  const diffMs = nowMs - itemTime
  if (filter === 'TODAY') {
    const nowDate = new Date(nowMs).toDateString()
    const itemDate = new Date(itemTime).toDateString()
    return nowDate === itemDate || (diffMs >= -60000 && diffMs <= 24 * 60 * 60 * 1000)
  }
  if (filter === 'WEEK') {
    return diffMs >= -60000 && diffMs <= 7 * 24 * 60 * 60 * 1000
  }
  if (filter === 'MONTH') {
    return diffMs >= -60000 && diffMs <= 30 * 24 * 60 * 60 * 1000
  }
  return true
}

// Real-Time Search Match Helper
function matchesSearch(item, query) {
  if (!query) return true
  const q = query.trim().toLowerCase()
  if (!q) return true

  const content = (item.message || '').toLowerCase()
  const type = (item.type || '').toLowerCase()
  const risk = (item.risk_level || '').toLowerCase()
  const tier = getRiskTier(item).toLowerCase()
  const explanation = (item.explanation || '').toLowerCase()
  const recommendation = (item.recommendation || '').toLowerCase()

  let synonyms = ''
  if (tier === 'high') synonyms = 'scam fraud threat critical danger high'
  else if (tier === 'medium') synonyms = 'warning suspicious moderate medium'
  else if (tier === 'low') synonyms = 'safe clean legitimate benign low'

  return (
    content.includes(q) ||
    type.includes(q) ||
    risk.includes(q) ||
    tier.includes(q) ||
    synonyms.includes(q) ||
    explanation.includes(q) ||
    recommendation.includes(q)
  )
}

// CSV Cell Escape Helper (Escapes quotes, handles commas and newlines)
function escapeCsvCell(val) {
  if (val === null || val === undefined) return '""'
  const str = String(val)
  return `"${str.replace(/"/g, '""')}"`
}

export default function AdvancedScanHistory({
  scanHistory = [],
  onClearHistory = () => {},
  onInspectScan = () => {},
  onNavigate = () => {},
  onToast = () => {}
}) {
  const [searchQuery, setSearchQuery] = useState('')
  const [scannerFilter, setScannerFilter] = useState('ALL') // 'ALL' | 'SMS' | 'URL' | 'UPI'
  const [riskFilter, setRiskFilter] = useState('ALL') // 'ALL' | 'HIGH' | 'MEDIUM' | 'LOW'
  const [dateFilter, setDateFilter] = useState('ALL') // 'ALL' | 'TODAY' | 'WEEK' | 'MONTH'
  const [sortBy, setSortBy] = useState('NEWEST') // 'NEWEST' | 'OLDEST' | 'SCORE_DESC' | 'SCORE_ASC'
  const [nowMs] = useState(() => Date.now())

  const hasActiveFilters = Boolean(
    searchQuery.trim() ||
    scannerFilter !== 'ALL' ||
    riskFilter !== 'ALL' ||
    dateFilter !== 'ALL' ||
    sortBy !== 'NEWEST'
  )

  function handleResetFilters() {
    setSearchQuery('')
    setScannerFilter('ALL')
    setRiskFilter('ALL')
    setDateFilter('ALL')
    setSortBy('NEWEST')
  }

  // Filtered and Sorted Records
  const filteredRecords = useMemo(() => {
    // 1. Filter
    const matched = scanHistory.filter((item) => {
      if (scannerFilter !== 'ALL' && (item.type || '').toUpperCase() !== scannerFilter) {
        return false
      }
      if (riskFilter !== 'ALL' && getRiskTier(item) !== riskFilter) {
        return false
      }
      if (!matchesDateFilter(item, dateFilter, nowMs)) {
        return false
      }
      if (!matchesSearch(item, searchQuery)) {
        return false
      }
      return true
    })

    // 2. Sort
    return matched.sort((a, b) => {
      const timeA = extractValidTimestamp(a) || (typeof a.id === 'number' ? a.id : 0)
      const timeB = extractValidTimestamp(b) || (typeof b.id === 'number' ? b.id : 0)
      const scoreA = Number(a.model_score) || 0
      const scoreB = Number(b.model_score) || 0

      if (sortBy === 'NEWEST') return timeB - timeA
      if (sortBy === 'OLDEST') return timeA - timeB
      if (sortBy === 'SCORE_DESC') return scoreB - scoreA
      if (sortBy === 'SCORE_ASC') return scoreA - scoreB
      return 0
    })
  }, [scanHistory, scannerFilter, riskFilter, dateFilter, searchQuery, sortBy, nowMs])

  // CSV Export Handler
  function handleExportCsv() {
    if (filteredRecords.length === 0) {
      if (onToast) onToast('No records available to export.', 'info')
      return
    }

    try {
      const headers = [
        'Timestamp',
        'Scanner Type',
        'Scanned Content',
        'Risk Score',
        'Risk Level',
        'Detection Explanation'
      ]

      const rows = filteredRecords.map((item) => {
        const timeStr = `${item.date || ''} ${item.timestamp || ''}`.trim()
        const typeStr = item.type || 'SMS'
        const contentStr = item.message || ''
        const scoreStr = item.type === 'SMS' ? `${item.model_score}%` : `${item.model_score}/100`
        const riskStr = item.risk_level || getRiskTier(item)
        const explStr = item.explanation || item.recommendation || ''

        return [
          escapeCsvCell(timeStr),
          escapeCsvCell(typeStr),
          escapeCsvCell(contentStr),
          escapeCsvCell(scoreStr),
          escapeCsvCell(riskStr),
          escapeCsvCell(explStr)
        ].join(',')
      })

      const csvContent = '\uFEFF' + [headers.map(escapeCsvCell).join(','), ...rows].join('\r\n')
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      const dateStr = new Date().toISOString().slice(0, 10)
      link.setAttribute('href', url)
      link.setAttribute('download', `fraudlens_scan_history_${dateStr}.csv`)
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
      if (onToast) onToast(`Exported ${filteredRecords.length} scan record(s) to CSV successfully.`, 'success')
    } catch (err) {
      if (onToast) onToast(`Failed to export CSV: ${err.message || 'Unknown error'}`, 'error')
    }
  }

  // Case A: Entire session history is empty
  if (scanHistory.length === 0) {
    return (
      <div className="history-container">
        <div className="scanner-header-section">
          <div className="scanner-eyebrow">
            <History size={14} /> SESSION SCAN LOGS & AUDIT TRAIL
          </div>
          <h2 className="scanner-main-title">Session Scan History</h2>
          <p className="scanner-main-desc">
            Complete audit trail of SMS messages, URLs, and UPI payment requests analyzed in this browser session.
          </p>
        </div>

        <div className="fintech-card empty-history-card">
          <div className="empty-icon-wrapper">
            <History size={48} className="empty-history-icon" />
          </div>
          <div className="empty-badge">SESSION LOGS EMPTY</div>
          <h3 className="empty-title">No Scan Records Found</h3>
          <p className="empty-description">
            Messages, URLs, and UPI alerts you scan with FraudLens AI will appear here in chronological order with risk classifications and model scores.
          </p>
          <div className="empty-actions">
            <button type="button" className="primary-btn" onClick={() => onNavigate('sms')}>
              <MessageSquareText size={16} /> Scan an SMS
            </button>
            <button type="button" className="secondary-btn" onClick={() => onNavigate('url')}>
              <Link2 size={16} /> Scan a URL
            </button>
            <button type="button" className="secondary-btn" onClick={() => onNavigate('upi')}>
              <Smartphone size={16} /> Scan a UPI Payment
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="history-container">
      {/* HEADER SECTION */}
      <div className="history-header">
        <div>
          <div className="scanner-eyebrow">
            <History size={14} /> SESSION SCAN LOGS & AUDIT TRAIL
          </div>
          <h2 className="scanner-main-title">Session Scan History</h2>
          <p className="scanner-main-desc">
            Search, filter, inspect, and export your session threat detections.
          </p>
        </div>
        <div className="history-header-actions">
          <button
            type="button"
            className="secondary-btn clear-btn"
            onClick={onClearHistory}
            title="Permanently erase all locally stored session scan history"
          >
            Clear Session History
          </button>
        </div>
      </div>

      {/* ADVANCED FILTER & SEARCH CONTROLS */}
      <div className="fintech-card history-controls-card">
        {/* Search Input Row */}
        <div className="history-search-row">
          <div className="history-search-input-wrapper">
            <Search size={16} className="history-search-icon" />
            <input
              type="text"
              className="history-search-input"
              placeholder="Search content, scanner type, risk level, or explanation..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            {searchQuery && (
              <button
                type="button"
                className="search-clear-btn"
                onClick={() => setSearchQuery('')}
                title="Clear search"
              >
                <X size={14} />
              </button>
            )}
          </div>

          <div className="history-quick-actions">
            <button
              type="button"
              className="export-csv-btn"
              onClick={handleExportCsv}
              disabled={filteredRecords.length === 0}
              title={filteredRecords.length === 0 ? 'No records to export' : `Export ${filteredRecords.length} filtered record(s) to CSV`}
            >
              <Download size={14} />
              <span>Export CSV ({filteredRecords.length})</span>
            </button>

            {hasActiveFilters && (
              <button
                type="button"
                className="history-reset-btn"
                onClick={handleResetFilters}
                title="Reset all search and filter parameters"
              >
                <RotateCcw size={13} />
                <span>Reset Filters</span>
              </button>
            )}
          </div>
        </div>

        {/* Filters Selection Row */}
        <div className="history-filters-row">
          {/* Scanner Engine Filter */}
          <div className="filter-field">
            <label htmlFor="filter-scanner" className="filter-label">
              <Filter size={12} /> SCANNER
            </label>
            <select
              id="filter-scanner"
              className="filter-select"
              value={scannerFilter}
              onChange={(e) => setScannerFilter(e.target.value)}
            >
              <option value="ALL">All Scanners</option>
              <option value="SMS">SMS Scanner</option>
              <option value="URL">URL Scanner</option>
              <option value="UPI">UPI Protection</option>
            </select>
          </div>

          {/* Risk Level Filter */}
          <div className="filter-field">
            <label htmlFor="filter-risk" className="filter-label">
              <ShieldAlert size={12} /> RISK LEVEL
            </label>
            <select
              id="filter-risk"
              className="filter-select"
              value={riskFilter}
              onChange={(e) => setRiskFilter(e.target.value)}
            >
              <option value="ALL">All Risk Levels</option>
              <option value="HIGH">High Risk Only</option>
              <option value="MEDIUM">Medium Risk Only</option>
              <option value="LOW">Low Risk / Safe Only</option>
            </select>
          </div>

          {/* Date Filter */}
          <div className="filter-field">
            <label htmlFor="filter-date" className="filter-label">
              <Clock size={12} /> DATE RANGE
            </label>
            <select
              id="filter-date"
              className="filter-select"
              value={dateFilter}
              onChange={(e) => setDateFilter(e.target.value)}
            >
              <option value="ALL">All Time</option>
              <option value="TODAY">Today (Last 24h)</option>
              <option value="WEEK">Last 7 Days</option>
              <option value="MONTH">Last 30 Days</option>
            </select>
          </div>

          {/* Sort By Filter */}
          <div className="filter-field">
            <label htmlFor="filter-sort" className="filter-label">
              <ArrowUpDown size={12} /> SORT BY
            </label>
            <select
              id="filter-sort"
              className="filter-select"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
            >
              <option value="NEWEST">Newest First</option>
              <option value="OLDEST">Oldest First</option>
              <option value="SCORE_DESC">Highest Risk Score</option>
              <option value="SCORE_ASC">Lowest Risk Score</option>
            </select>
          </div>
        </div>

        {/* Telemetry Count Meta Bar */}
        <div className="history-meta-bar">
          <div className="history-count-tag">
            Showing <strong>{filteredRecords.length}</strong> of <strong>{scanHistory.length}</strong> total session scan(s)
          </div>
          {searchQuery && (
            <div className="search-query-tag">
              Filter keyword: <em>&ldquo;{searchQuery}&rdquo;</em>
            </div>
          )}
        </div>
      </div>

      {/* RECORDS LIST OR FILTERED EMPTY STATE */}
      {filteredRecords.length === 0 ? (
        <div className="fintech-card history-empty-filtered-card">
          <div className="empty-filtered-icon-box">
            <Filter size={36} className="empty-filtered-icon" />
          </div>
          <h3 className="empty-filtered-title">No Matching Scan Records</h3>
          <p className="empty-filtered-desc">
            No session scan records matched your active query and filter combination.
          </p>
          <button
            type="button"
            className="primary-btn"
            onClick={handleResetFilters}
          >
            <RotateCcw size={14} /> Clear All Filters & Search
          </button>
        </div>
      ) : (
        <div className="history-list">
          {filteredRecords.map((scan) => {
            const tier = getRiskTier(scan)
            const isHigh = tier === 'HIGH'
            const isMedium = tier === 'MEDIUM'

            return (
              <div key={scan.id} className="fintech-card history-card">
                <div className="history-card-top">
                  <div className="history-meta">
                    <span className={`type-pill ${scan.type?.toLowerCase() || 'sms'}`}>
                      {scan.type === 'SMS' && <MessageSquareText size={12} />}
                      {scan.type === 'URL' && <Link2 size={12} />}
                      {scan.type === 'UPI' && <Smartphone size={12} />}
                      <span>{scan.type || 'SMS'}</span>
                    </span>
                    <Clock size={13} className="meta-clock-icon" />
                    <span className="history-time-text">{scan.date} at {scan.timestamp}</span>
                  </div>
                  <span className={`risk-badge ${isHigh ? 'danger' : isMedium ? 'warning' : 'safe'}`}>
                    {isHigh && <><AlertTriangle size={12} /> HIGH RISK</>}
                    {isMedium && <><AlertTriangle size={12} /> MEDIUM RISK</>}
                    {!isHigh && !isMedium && <><CheckCircle2 size={12} /> LOW RISK</>}
                  </span>
                </div>

                <div className="history-message-quote">
                  &ldquo;{scan.message}&rdquo;
                </div>

                {scan.explanation && (
                  <div className="history-explanation">
                    <strong>Analysis:</strong> {scan.explanation}
                  </div>
                )}

                <div className="history-card-footer">
                  <div className="history-score">
                    <span>Model Score:</span>
                    <strong className={`score-tag ${isHigh ? 'danger' : isMedium ? 'warning' : 'safe'}`}>
                      {scan.type === 'SMS' ? `${scan.model_score}%` : `${scan.model_score} / 100`}
                    </strong>
                  </div>
                  <button
                    type="button"
                    className="table-action-btn"
                    onClick={() => onInspectScan(scan)}
                    title="Load this payload back into its dedicated scanner"
                  >
                    <Eye size={13} />
                    <span>Inspect in Scanner</span>
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
