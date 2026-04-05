import './QueryResult.css'

const QueryResult = ({ result }) => {
  return (
    <div className="query-result-container">
      <div className="result-section">
        <h5 className="result-title">🔍 Generated MongoDB Query</h5>
        <div className="result-code">
          <pre>{JSON.stringify(result.query, null, 2)}</pre>
        </div>
      </div>

      <div className="result-section">
        <h5 className="result-title">💡 Explanation</h5>
        <div className="result-explanation">
          {result.explanation}
        </div>
      </div>
    </div>
  )
}

export default QueryResult
