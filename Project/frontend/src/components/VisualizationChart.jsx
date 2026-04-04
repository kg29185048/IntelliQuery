import { useState } from 'react'
import {
  BarChart, Bar, LineChart, Line, ScatterChart, Scatter,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts'
import './VisualizationChart.css'

const VisualizationChart = ({ userQuery, resultData }) => {
  const [vizConfig, setVizConfig] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [generated, setGenerated] = useState(false)

  const handleGenerate = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch('/api/visualize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_query: userQuery, result_data: resultData })
      })
      const config = await res.json()
      if (!res.ok) throw new Error(config.detail || 'Failed to get visualization config')
      setVizConfig(config)
      setGenerated(true)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const renderChart = () => {
    if (!vizConfig?.visualizable) {
      return (
        <div className="viz-not-applicable">
          ℹ️ This dataset isn't suitable for charting (e.g. missing numeric values).
        </div>
      )
    }

    const { chart_type, x_axis, y_axis, title } = vizConfig
    const cols = resultData[0] ? Object.keys(resultData[0]) : []

    if (!cols.includes(x_axis) || !cols.includes(y_axis)) {
      return (
        <div className="viz-error">
          ⚠️ Chart config references columns [{x_axis}, {y_axis}] not found in data.
        </div>
      )
    }

    const commonProps = {
      data: resultData,
      margin: { top: 10, right: 20, left: 0, bottom: 50 }
    }

    return (
      <div className="chart-wrapper">
        {title && <div className="chart-title">{title}</div>}
        <ResponsiveContainer width="100%" height={300}>
          {chart_type === 'bar' ? (
            <BarChart {...commonProps}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={x_axis} angle={-30} textAnchor="end" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Legend />
              <Bar dataKey={y_axis} fill="#667eea" />
            </BarChart>
          ) : chart_type === 'line' ? (
            <LineChart {...commonProps}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={x_axis} angle={-30} textAnchor="end" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey={y_axis} stroke="#667eea" strokeWidth={2} dot={{ r: 3 }} />
            </LineChart>
          ) : chart_type === 'scatter' ? (
            <ScatterChart {...commonProps}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={x_axis} name={x_axis} tick={{ fontSize: 11 }} />
              <YAxis dataKey={y_axis} name={y_axis} tick={{ fontSize: 11 }} />
              <Tooltip cursor={{ strokeDasharray: '3 3' }} />
              <Scatter data={resultData} fill="#764ba2" />
            </ScatterChart>
          ) : (
            <div className="viz-error">Unsupported chart type: {chart_type}</div>
          )}
        </ResponsiveContainer>
      </div>
    )
  }

  return (
    <div className="viz-section">
      {!generated && (
        <button
          className="btn-generate-viz"
          onClick={handleGenerate}
          disabled={loading}
        >
          {loading ? '⏳ Analyzing data...' : '📊 Generate Visualization'}
        </button>
      )}

      {error && <div className="viz-error">⚠️ {error}</div>}

      {generated && vizConfig && renderChart()}
    </div>
  )
}

export default VisualizationChart
