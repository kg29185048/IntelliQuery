import './ResultsDisplay.css'

const ResultsDisplay = ({ results }) => {
  if (!results) {
    return null
  }

  // Handle different result types
  if (Array.isArray(results)) {
    if (results.length === 0) {
      return (
        <div className="results-container">
          <h5 className="results-title">📊 Results</h5>
          <p className="text-muted">No results found</p>
        </div>
      )
    }

    // Check if results are objects (multiple fields)
    if (typeof results[0] === 'object' && results[0] !== null) {
      const keys = Object.keys(results[0])
      return (
        <div className="results-container">
          <h5 className="results-title">📊 Results ({results.length} records)</h5>
          <div className="table-responsive">
            <table className="results-table">
              <thead>
                <tr>
                  {keys.map((key) => (
                    <th key={key}>{key}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {results.map((item, idx) => (
                  <tr key={idx}>
                    {keys.map((key) => (
                      <td key={`${idx}-${key}`}>
                        {typeof item[key] === 'object'
                          ? JSON.stringify(item[key])
                          : String(item[key])}
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

    // Simple list of values
    return (
      <div className="results-container">
        <h5 className="results-title">📊 Results ({results.length} items)</h5>
        <div className="results-list">
          {results.map((item, idx) => (
            <div key={idx} className="result-item">
              {String(item)}
            </div>
          ))}
        </div>
      </div>
    )
  }

  // Single object result
  if (typeof results === 'object') {
    return (
      <div className="results-container">
        <h5 className="results-title">📊 Result</h5>
        <div className="result-code">
          <pre>{JSON.stringify(results, null, 2)}</pre>
        </div>
      </div>
    )
  }

  // String or other primitive
  return (
    <div className="results-container">
      <h5 className="results-title">📊 Result</h5>
      <div className="result-item">{String(results)}</div>
    </div>
  )
}

export default ResultsDisplay
