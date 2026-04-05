import './ResultsTable.css'

const downloadCSV = (data) => {
  const cols = Object.keys(data[0])
  const escape = (val) => {
    const str = typeof val === 'object' && val !== null ? JSON.stringify(val) : String(val ?? '')
    return `"${str.replace(/"/g, '""')}"`
  }
  const rows = data.map(row => cols.map(col => escape(row[col])).join(','))
  const csv = [cols.join(','), ...rows].join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `intelliquery_results_${Date.now()}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

const ResultsTable = ({ data }) => {
  if (!data) return null

  if (typeof data === 'string') {
    return <div className="results-string">{data}</div>
  }

  if (!Array.isArray(data)) {
    return (
      <pre className="results-json">
        {JSON.stringify(data, null, 2)}
      </pre>
    )
  }

  if (data.length === 0) {
    return <div className="results-empty">No matching documents found.</div>
  }

  if (typeof data[0] !== 'object' || data[0] === null) {
    return (
      <ul className="results-plain-list">
        {data.map((item, i) => <li key={i}>{String(item)}</li>)}
      </ul>
    )
  }

  const cols = Object.keys(data[0])

  return (
    <div className="results-table-wrapper">
      <div className="results-table-header">
        <span className="results-count">{data.length} record{data.length !== 1 ? 's' : ''}</span>
        <button className="btn-download-csv" onClick={() => downloadCSV(data)} title="Download as CSV">
          ⬇ Download CSV
        </button>
      </div>
      <div className="table-scroll">
        <table className="results-table">
          <thead>
            <tr>
              {cols.map(col => <th key={col}>{col}</th>)}
            </tr>
          </thead>
          <tbody>
            {data.map((row, i) => (
              <tr key={i}>
                {cols.map(col => (
                  <td key={col}>
                    {typeof row[col] === 'object' && row[col] !== null
                      ? JSON.stringify(row[col])
                      : String(row[col] ?? '')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default ResultsTable
