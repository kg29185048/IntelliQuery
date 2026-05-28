import { useState } from 'react'
import {
  BarChart, Bar, LineChart, Line, ScatterChart, Scatter,
  PieChart, Pie, Cell, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts'
import './VisualizationChart.css'

const COLORS = ['#667eea', '#764ba2', '#FFBB28', '#FF8042', '#00C49F', '#F4A261', '#E76F51', '#2A9D8F'];

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

    let { chart_type, x_axis, y_axis, title } = vizConfig
    const cols = resultData[0] ? Object.keys(resultData[0]) : []

    // Smart fallback for aggregations (which usually have exactly 2 columns like `_id` and `count`)
    if (!cols.includes(x_axis) || !cols.includes(y_axis)) {
      if (cols.length === 2) {
        const numCol = cols.find(c => typeof resultData[0][c] === 'number' || !isNaN(Number(resultData[0][c])))
        const strCol = cols.find(c => c !== numCol)
        if (numCol && strCol) {
          x_axis = strCol
          y_axis = numCol
        }
      }
    }

    if (!cols.includes(x_axis) || !cols.includes(y_axis)) {
      return (
        <div className="viz-error">
          ⚠️ Chart config references columns [{x_axis}, {y_axis}] not found in data.<br/>
          <small>Available columns: [{cols.join(', ')}]</small>
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
          ) : chart_type === 'area' ? (
            <AreaChart {...commonProps}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={x_axis} angle={-30} textAnchor="end" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Legend />
              <Area type="monotone" dataKey={y_axis} stroke="#667eea" fill="#667eea" fillOpacity={0.6} />
            </AreaChart>
          ) : chart_type === 'pie' ? (
            <PieChart margin={{ top: 10, right: 10, left: 10, bottom: 10 }}>
              <Tooltip />
              <Legend />
              <Pie
                data={resultData}
                dataKey={y_axis}
                nameKey={x_axis}
                cx="50%"
                cy="50%"
                outerRadius={100}
                fill="#8884d8"
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              >
                {resultData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
            </PieChart>
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
