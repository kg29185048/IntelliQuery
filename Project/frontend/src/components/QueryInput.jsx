import { useState } from 'react'
import './QueryInput.css'

const QueryInput = ({ onQuery, loading, onClear }) => {
  const [query, setQuery] = useState('')

  const handleSubmit = () => {
    if (query.trim()) {
      onQuery(query)
    }
  }

  const handleClear = () => {
    setQuery('')
    onClear()
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && e.ctrlKey) {
      handleSubmit()
    }
  }

  return (
    <div className="query-input-container">
      <label className="query-input-label">Ask your question in natural language:</label>
      <textarea
        className="query-textarea"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyPress={handleKeyPress}
        placeholder="Example: Show me all users with status 'active' in the last 7 days"
        disabled={loading}
      />
      <div className="query-buttons">
        <button
          className="btn-submit"
          onClick={handleSubmit}
          disabled={loading || !query.trim()}
        >
          {loading ? (
            <>
              <span className="spinner">⚙️</span> Processing...
            </>
          ) : (
            '🚀 Submit Query'
          )}
        </button>
        <button
          className="btn-clear"
          onClick={handleClear}
          disabled={loading}
        >
          Clear
        </button>
      </div>
    </div>
  )
}

export default QueryInput
