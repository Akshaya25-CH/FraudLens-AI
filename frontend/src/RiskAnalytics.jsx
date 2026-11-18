import { useState, useMemo } from 'react'
import {
  Activity, ShieldAlert, AlertTriangle, CheckCircle2,
  Layers, Smartphone, Link2, MessageSquareText,
  TrendingUp, BarChart3, PieChart as PieIcon, ArrowRight, RotateCcw
} from 'lucide-react'
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid
} from 'recharts'

/**
 * Classifies an individual scan history item into High, Medium, or Low risk.
 * - High: POTENTIAL_FRAUD, HIGH_STRUCTURAL_RISK, HIGH_PAYMENT_RISK, or prediction === 1
 * - Medium: MEDIUM_STRUCTURAL_RISK, MEDIUM_PAYMENT_RISK
 * - Low: NO_FRAUD_PATTERN_DETECTED, LOW_STRUCTURAL_RISK, LOW_PAYMENT_RISK, or prediction === 0
 */
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

// ---------------------------------------------------------------------------
// Custom Chart Tooltips (High contrast, clean typography)
// ---------------------------------------------------------------------------
function CustomBarTooltip({ active, payload, label }) {
  if (active && payload && payload.length) {
    const data = payload[0]
    return (
      <div className="analytics-custom-tooltip">
        <div className="tooltip-title">{label || data.name}</div>
        <div className="tooltip-item" style={{ color: data.payload?.fill || '#3b82f6' }}>
          <span>Total Scans:</span>
          <strong>{data.value}</strong>
        </div>
      </div>
    )
  }
  return null
}

function CustomPieTooltip({ active, payload }) {
  if (active && payload && payload.length) {
    const data = payload[0]
    return (
      <div className="analytics-custom-tooltip">
        <div className="tooltip-title">{data.name}</div>
        <div className="tooltip-item" style={{ color: data.payload?.fill || '#ef4444' }}>
          <span>Detections:</span>
          <strong>{data.value}</strong>
        </div>
      </div>
    )
  }
  return null
}

function CustomBucketTooltip({ active, payload }) {
  if (active && payload && payload.length) {
    const data = payload[0]
    return (
      <div className="analytics-custom-tooltip">
        <div className="tooltip-title">{data.payload?.label || data.name}</div>
        <div className="tooltip-item" style={{ color: data.payload?.fill || '#10b981' }}>
          <span>Scans in range:</span>
          <strong>{data.value}</strong>
        </div>
      </div>
    )
  }
  return null
}

function CustomTimelineTooltip({ active, payload }) {
  if (active && payload && payload.length) {
    const data = payload[0]?.payload
    if (!data) return null
    return (
      <div className="analytics-custom-tooltip">
        <div className="tooltip-title">{data.name} ({data.engine})</div>
        <div className="tooltip-time">{data.date ? `${data.date} · ` : ''}{data.time}</div>
        <div className="tooltip-item" style={{ color: '#2563eb' }}>
          <span>Risk Score:</span>
          <strong>{data.score} / 100</strong>
        </div>
        <div className="tooltip-sub">
          <span>Tier:</span>
          <strong className={`tier-badge-text ${data.tier.toLowerCase()}`}>{data.tier}</strong>
        </div>
      </div>
    )
  }
  return null
}

// ---------------------------------------------------------------------------
// Main Risk Analytics Component
// ---------------------------------------------------------------------------
export default function RiskAnalytics({ scanHistory = [], onNavigate = () => {} }) {
  const [selectedFilter, setSelectedFilter] = useState('ALL') // 'ALL' | 'SMS' | 'URL' | 'UPI'

  // Per-filter counts across all stored history
  const filterCounts = useMemo(() => {
    return {
      ALL: scanHistory.length,
      SMS: scanHistory.filter((i) => (i.type || '').toUpperCase() === 'SMS').length,
      URL: scanHistory.filter((i) => (i.type || '').toUpperCase() === 'URL').length,
      UPI: scanHistory.filter((i) => (i.type || '').toUpperCase() === 'UPI').length
    }
  }, [scanHistory])

  // Filtered dataset responding strictly to user selection
  const filteredHistory = useMemo(() => {
    if (selectedFilter === 'ALL') return scanHistory
    return scanHistory.filter((item) => (item.type || '').toUpperCase() === selectedFilter)
  }, [scanHistory, selectedFilter])

  // Aggregated KPI metrics computed purely from filtered data
  const metrics = useMemo(() => {
    const total = filteredHistory.length
    const high = filteredHistory.filter((i) => getRiskTier(i) === 'HIGH').length
    const medium = filteredHistory.filter((i) => getRiskTier(i) === 'MEDIUM').length
    const low = filteredHistory.filter((i) => getRiskTier(i) === 'LOW').length

    const highRate = total > 0 ? ((high / total) * 100).toFixed(1) : '0.0'
    const mediumRate = total > 0 ? ((medium / total) * 100).toFixed(1) : '0.0'
    const lowRate = total > 0 ? ((low / total) * 100).toFixed(1) : '0.0'
    const scamDetectionRate = total > 0 ? (((high + medium) / total) * 100).toFixed(1) : '0.0'

    const avgScore = total > 0
      ? (filteredHistory.reduce((sum, i) => sum + (Number(i.model_score) || 0), 0) / total).toFixed(1)
      : '0.0'

    // Determine primary/most frequently used engine within session history
    const engineCounts = { SMS: 0, URL: 0, UPI: 0 }
    scanHistory.forEach((i) => {
      const t = (i.type || '').toUpperCase()
      if (engineCounts[t] !== undefined) engineCounts[t]++
    })

    let topEngine = 'N/A'
    let topCount = 0
    Object.entries(engineCounts).forEach(([eng, count]) => {
      if (count > topCount) {
        topCount = count
        topEngine = eng
      }
    })

    const topEngineLabel = topEngine === 'N/A'
      ? 'None'
      : `${topEngine} Scanner (${topCount})`

    return {
      total,
      high,
      medium,
      low,
      highRate,
      mediumRate,
      lowRate,
      scamDetectionRate,
      avgScore,
      topEngineLabel
    }
  }, [filteredHistory, scanHistory])

  // Chart 1: Engine volume
  const engineChartData = useMemo(() => {
    const sms = filteredHistory.filter((i) => (i.type || '').toUpperCase() === 'SMS').length
    const url = filteredHistory.filter((i) => (i.type || '').toUpperCase() === 'URL').length
    const upi = filteredHistory.filter((i) => (i.type || '').toUpperCase() === 'UPI').length
    return [
      { name: 'SMS Scanner', count: sms, fill: '#3b82f6' },
      { name: 'URL Scanner', count: url, fill: '#8b5cf6' },
      { name: 'UPI Protection', count: upi, fill: '#06b6d4' }
    ]
  }, [filteredHistory])

  // Chart 2: Threat severity distribution
  const threatChartData = useMemo(() => {
    const list = [
      { name: 'High Risk (Scam/Threat)', value: metrics.high, fill: '#ef4444' },
      { name: 'Medium Risk (Warning)', value: metrics.medium, fill: '#f59e0b' },
      { name: 'Low Risk (Legitimate)', value: metrics.low, fill: '#10b981' }
    ]
    return list.filter((item) => item.value > 0)
  }, [metrics])

  // Chart 3: Risk score frequency buckets
  const scoreBucketsData = useMemo(() => {
    const buckets = [
      { range: '0–20%', label: '0–20% (Safe)', count: 0, fill: '#10b981' },
      { range: '21–40%', label: '21–40% (Mild)', count: 0, fill: '#84cc16' },
      { range: '41–60%', label: '41–60% (Moderate)', count: 0, fill: '#f59e0b' },
      { range: '61–80%', label: '61–80% (Elevated)', count: 0, fill: '#f97316' },
      { range: '81–100%', label: '81–100% (Critical)', count: 0, fill: '#ef4444' }
    ]
    filteredHistory.forEach((item) => {
      const s = Math.max(0, Math.min(100, Number(item.model_score) || 0))
      if (s <= 20) buckets[0].count++
      else if (s <= 40) buckets[1].count++
      else if (s <= 60) buckets[2].count++
      else if (s <= 80) buckets[3].count++
      else buckets[4].count++
    })
    return buckets
  }, [filteredHistory])

  // Chart 4: Chronological timeline of scans (oldest to newest)
  const timelineData = useMemo(() => {
    return [...filteredHistory].reverse().map((item, idx) => {
      const timeLabel = item.timestamp || `Scan #${idx + 1}`
      return {
        order: idx + 1,
        name: `Scan #${idx + 1}`,
        time: timeLabel,
        score: Math.round(Number(item.model_score) || 0),
        engine: item.type || 'Scan',
        tier: getRiskTier(item),
        date: item.date || ''
      }
    })
  }, [filteredHistory])

  // -------------------------------------------------------------------------
  // Case A: Entire session history is empty
  // -------------------------------------------------------------------------
  if (scanHistory.length === 0) {
    return (
      <div className="analytics-container">
        <div className="scanner-header-section">
          <div className="scanner-eyebrow">
            <Activity size={14} /> THREAT INTELLIGENCE & TELEMETRY
          </div>
          <h2 className="scanner-main-title">Risk Analytics & Threat Distribution</h2>
          <p className="scanner-main-desc">
            Live telemetry and security metrics computed dynamically from your active scan sessions.
          </p>
        </div>

        <div className="analytics-empty-card fintech-card">
          <div className="empty-icon-wrapper">
            <Activity size={48} className="empty-activity-icon" />
          </div>
          <div className="empty-badge">TELEMETRY ENGINE READY</div>
          <h3 className="empty-title">No Scan History Recorded</h3>
          <p className="empty-description">
            FraudLens AI calculates real-time threat intelligence dynamically from actual scan events.
            Execute scans in the SMS, URL, or UPI modules to populate threat distribution charts,
            risk histograms, and timeline activity.
          </p>
          <div className="empty-actions">
            <button
              type="button"
              className="primary-btn"
              onClick={() => onNavigate('sms')}
            >
              <MessageSquareText size={16} /> Open SMS Scanner
            </button>
            <button
              type="button"
              className="secondary-btn"
              onClick={() => onNavigate('url')}
            >
              <Link2 size={16} /> Open URL Scanner
            </button>
            <button
              type="button"
              className="secondary-btn"
              onClick={() => onNavigate('upi')}
            >
              <Smartphone size={16} /> Open UPI Protection
            </button>
          </div>
        </div>
      </div>
    )
  }

  // -------------------------------------------------------------------------
  // Case B: Filter has no matches, but session history has scans
  // -------------------------------------------------------------------------
  const isFilterEmpty = filteredHistory.length === 0

  return (
    <div className="analytics-container">
      {/* HEADER SECTION */}
      <div className="scanner-header-section">
        <div className="scanner-eyebrow">
          <Activity size={14} /> LIVE THREAT INTELLIGENCE & TELEMETRY
        </div>
        <h2 className="scanner-main-title">Enterprise Risk Analytics</h2>
        <p className="scanner-main-desc">
          Dynamic security metrics, threat distributions, and multi-engine telemetry computed directly from your active session scans.
        </p>
      </div>

      {/* FILTER CONTROL BAR */}
      <div className="analytics-filter-bar fintech-card">
        <div className="filter-bar-label">
          <Layers size={15} /> Scope Filter:
        </div>
        <div className="filter-pill-group">
          {[
            { id: 'ALL', label: 'All Scanners', count: filterCounts.ALL },
            { id: 'SMS', label: 'SMS Only', count: filterCounts.SMS },
            { id: 'URL', label: 'URL Only', count: filterCounts.URL },
            { id: 'UPI', label: 'UPI Only', count: filterCounts.UPI }
          ].map((tab) => (
            <button
              key={tab.id}
              type="button"
              className={`filter-pill-btn ${selectedFilter === tab.id ? 'active' : ''}`}
              onClick={() => setSelectedFilter(tab.id)}
            >
              <span>{tab.label}</span>
              <span className="filter-count-badge">{tab.count}</span>
            </button>
          ))}
        </div>
      </div>

      {isFilterEmpty ? (
        <div className="analytics-empty-card fintech-card" style={{ marginTop: '16px' }}>
          <div className="empty-icon-wrapper warning">
            <ShieldAlert size={44} className="empty-warning-icon" />
          </div>
          <h3 className="empty-title">No {selectedFilter} Scans Recorded</h3>
          <p className="empty-description">
            You have {scanHistory.length} total scan(s) recorded in your session, but none under the <strong>{selectedFilter}</strong> module.
          </p>
          <div className="empty-actions">
            <button
              type="button"
              className="primary-btn"
              onClick={() => setSelectedFilter('ALL')}
            >
              <RotateCcw size={15} /> Reset Filter to All Scanners ({scanHistory.length})
            </button>
            <button
              type="button"
              className="secondary-btn"
              onClick={() => onNavigate(selectedFilter.toLowerCase())}
            >
              <ArrowRight size={15} /> Run a {selectedFilter} Scan Now
            </button>
          </div>
        </div>
      ) : (
        <>
          {/* SUMMARY KPI CARDS */}
          <div className="analytics-kpi-grid">
            {/* Total Scans */}
            <div className="fintech-card analytics-kpi-card">
              <div className="kpi-header">
                <span className="kpi-label">TOTAL SCANS</span>
                <span className="kpi-icon-badge blue"><Layers size={16} /></span>
              </div>
              <div className="kpi-value">{metrics.total}</div>
              <div className="kpi-subtext">
                {selectedFilter === 'ALL' ? 'Across all engines' : `Filtered: ${selectedFilter} only`}
              </div>
            </div>

            {/* High-Risk Detections */}
            <div className="fintech-card analytics-kpi-card">
              <div className="kpi-header">
                <span className="kpi-label">HIGH-RISK DETECTIONS</span>
                <span className="kpi-icon-badge red"><ShieldAlert size={16} /></span>
              </div>
              <div className="kpi-value red-text">{metrics.high}</div>
              <div className="kpi-subtext">
                <strong>{metrics.highRate}%</strong> of evaluated scans
              </div>
            </div>

            {/* Medium-Risk Detections */}
            <div className="fintech-card analytics-kpi-card">
              <div className="kpi-header">
                <span className="kpi-label">MEDIUM-RISK WARNINGS</span>
                <span className="kpi-icon-badge amber"><AlertTriangle size={16} /></span>
              </div>
              <div className="kpi-value amber-text">{metrics.medium}</div>
              <div className="kpi-subtext">
                <strong>{metrics.mediumRate}%</strong> suspicious signals
              </div>
            </div>

            {/* Low-Risk / Legitimate */}
            <div className="fintech-card analytics-kpi-card">
              <div className="kpi-header">
                <span className="kpi-label">LOW-RISK / VERIFIED SAFE</span>
                <span className="kpi-icon-badge green"><CheckCircle2 size={16} /></span>
              </div>
              <div className="kpi-value green-text">{metrics.low}</div>
              <div className="kpi-subtext">
                <strong>{metrics.lowRate}%</strong> benign / safe scans
              </div>
            </div>

            {/* Most Frequently Used Scanner */}
            <div className="fintech-card analytics-kpi-card">
              <div className="kpi-header">
                <span className="kpi-label">PRIMARY SECURITY ENGINE</span>
                <span className="kpi-icon-badge purple"><TrendingUp size={16} /></span>
              </div>
              <div className="kpi-value text-small">{metrics.topEngineLabel}</div>
              <div className="kpi-subtext">
                Avg Risk Score: <strong>{metrics.avgScore}/100</strong>
              </div>
            </div>
          </div>

          {/* DETECTION RATE & HEALTH PROGRESS BAR BANNER */}
          <div className="fintech-card detection-ratio-banner">
            <div className="ratio-header-row">
              <div className="ratio-title-col">
                <div className="ratio-title">Scam Detection & Threat Ratio</div>
                <div className="ratio-desc">
                  Combined threat mitigation posture across high-risk scams and medium warnings.
                </div>
              </div>
              <div className="ratio-stats-col">
                <div className="ratio-stat-pill threat">
                  Threat Rate: <strong>{metrics.scamDetectionRate}%</strong>
                </div>
                <div className="ratio-stat-pill clean">
                  Safe / Benign: <strong>{metrics.lowRate}%</strong>
                </div>
              </div>
            </div>

            {/* Stacked bar visualization */}
            <div className="ratio-progress-track">
              {metrics.high > 0 && (
                <div
                  className="ratio-progress-segment high"
                  style={{ width: `${metrics.highRate}%` }}
                  title={`High Risk: ${metrics.high} (${metrics.highRate}%)`}
                />
              )}
              {metrics.medium > 0 && (
                <div
                  className="ratio-progress-segment medium"
                  style={{ width: `${metrics.mediumRate}%` }}
                  title={`Medium Risk: ${metrics.medium} (${metrics.mediumRate}%)`}
                />
              )}
              {metrics.low > 0 && (
                <div
                  className="ratio-progress-segment low"
                  style={{ width: `${metrics.lowRate}%` }}
                  title={`Low Risk: ${metrics.low} (${metrics.lowRate}%)`}
                />
              )}
            </div>
            <div className="ratio-legend-row">
              <span className="legend-item"><span className="legend-dot red" /> High Risk ({metrics.high})</span>
              <span className="legend-item"><span className="legend-dot amber" /> Medium Risk ({metrics.medium})</span>
              <span className="legend-item"><span className="legend-dot green" /> Low Risk / Safe ({metrics.low})</span>
            </div>
          </div>

          {/* CHARTS GRID */}
          <div className="analytics-charts-grid">
            {/* Chart 1: Total Scans by Engine */}
            <div className="fintech-card analytics-chart-card">
              <div className="chart-header">
                <div className="chart-title-row">
                  <BarChart3 size={17} className="chart-title-icon blue" />
                  <h4 className="chart-title">Scans by Security Engine</h4>
                </div>
                <p className="chart-desc">Volume of evaluated payloads per detection engine</p>
              </div>
              <div className="chart-body">
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={engineChartData} margin={{ top: 10, right: 15, left: -15, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                    <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={{ stroke: '#e2e8f0' }} />
                    <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: '#64748b' }} axisLine={{ stroke: '#e2e8f0' }} />
                    <Tooltip content={<CustomBarTooltip />} />
                    <Bar dataKey="count" radius={[6, 6, 0, 0]} maxBarSize={48}>
                      {engineChartData.map((entry, index) => (
                        <Cell key={`cell-eng-${index}`} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Chart 2: Threat Distribution (Donut) */}
            <div className="fintech-card analytics-chart-card">
              <div className="chart-header">
                <div className="chart-title-row">
                  <PieIcon size={17} className="chart-title-icon red" />
                  <h4 className="chart-title">Threat Severity Distribution</h4>
                </div>
                <p className="chart-desc">Proportion of high, medium, and low risk outcomes</p>
              </div>
              <div className="chart-body">
                {threatChartData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={260}>
                    <PieChart>
                      <Pie
                        data={threatChartData}
                        dataKey="value"
                        nameKey="name"
                        cx="50%"
                        cy="45%"
                        outerRadius={80}
                        innerRadius={46}
                        paddingAngle={3}
                      >
                        {threatChartData.map((entry, index) => (
                          <Cell key={`cell-threat-${index}`} fill={entry.fill} />
                        ))}
                      </Pie>
                      <Tooltip content={<CustomPieTooltip />} />
                      <Legend
                        verticalAlign="bottom"
                        iconType="circle"
                        wrapperStyle={{ fontSize: '11.5px', paddingTop: '10px' }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="chart-placeholder">No threat records in current view</div>
                )}
              </div>
            </div>

            {/* Chart 3: Risk Score Distribution (Histogram) */}
            <div className="fintech-card analytics-chart-card">
              <div className="chart-header">
                <div className="chart-title-row">
                  <Activity size={17} className="chart-title-icon amber" />
                  <h4 className="chart-title">Risk Score Frequency (0–100%)</h4>
                </div>
                <p className="chart-desc">Frequency of model and structural risk probability intervals</p>
              </div>
              <div className="chart-body">
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={scoreBucketsData} margin={{ top: 10, right: 15, left: -15, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                    <XAxis dataKey="range" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={{ stroke: '#e2e8f0' }} />
                    <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: '#64748b' }} axisLine={{ stroke: '#e2e8f0' }} />
                    <Tooltip content={<CustomBucketTooltip />} />
                    <Bar dataKey="count" radius={[6, 6, 0, 0]} maxBarSize={42}>
                      {scoreBucketsData.map((entry, index) => (
                        <Cell key={`cell-bucket-${index}`} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Chart 4: Recent Scan Activity Timeline */}
            <div className="fintech-card analytics-chart-card">
              <div className="chart-header">
                <div className="chart-title-row">
                  <TrendingUp size={17} className="chart-title-icon green" />
                  <h4 className="chart-title">Chronological Scan Activity</h4>
                </div>
                <p className="chart-desc">Risk score progression over recorded scan sequence</p>
              </div>
              <div className="chart-body">
                {timelineData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={260}>
                    <AreaChart data={timelineData} margin={{ top: 10, right: 15, left: -15, bottom: 0 }}>
                      <defs>
                        <linearGradient id="scoreAreaGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#2563eb" stopOpacity={0.35} />
                          <stop offset="95%" stopColor="#2563eb" stopOpacity={0.0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                      <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#64748b' }} axisLine={{ stroke: '#e2e8f0' }} />
                      <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: '#64748b' }} axisLine={{ stroke: '#e2e8f0' }} />
                      <Tooltip content={<CustomTimelineTooltip />} />
                      <Area
                        type="monotone"
                        dataKey="score"
                        stroke="#2563eb"
                        strokeWidth={2.5}
                        fillOpacity={1}
                        fill="url(#scoreAreaGradient)"
                        dot={{ r: 3.5, stroke: '#2563eb', strokeWidth: 1.5, fill: '#ffffff' }}
                        activeDot={{ r: 6, fill: '#1d4ed8' }}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="chart-placeholder">No scan timeline records available</div>
                )}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
