import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import ResultsTable from './ResultsTable'
import VisualizationChart from './VisualizationChart'
import './ChatMessage.css'

const ChatMessage = ({ message, onSuggest, onConfirm, onCancel }) => {
  const { role, content, data, userQuery, suggestions } = message

  if (role === 'user') {
    return (
      <div className="msg-row msg-row--user">
        <div className="msg-bubble msg-bubble--user">
          {content}
        </div>
        <div className="msg-avatar msg-avatar--user">🧑</div>
      </div>
    )
  }

  if (role === 'confirm') {
    const { resolved, cancelled } = message
    return (
      <div className="msg-row msg-row--assistant">
        <div className="msg-avatar msg-avatar--bot">🧠</div>
        <div className="msg-confirm-block">
          <div className="msg-confirm-warning">
            ⚠️ <strong>Update operation detected.</strong> This will modify documents in your database. Please review and confirm.
          </div>

          <div className="result-columns">
            <div className="result-col">
              <div className="result-col-title">Generated Query</div>
              <pre className="query-code">{JSON.stringify(data?.query, null, 2)}</pre>
            </div>
            <div className="result-col">
              <div className="result-col-title">Explanation</div>
              <div className="explanation-box">
                <ReactMarkdown>{content}</ReactMarkdown>
              </div>
            </div>
          </div>

          {resolved ? (
            <div className={`msg-confirm-resolved ${cancelled ? 'msg-confirm-resolved--cancelled' : 'msg-confirm-resolved--done'}`}>
              {cancelled ? '🚫 Update cancelled.' : '✅ Update confirmed — executing…'}
            </div>
          ) : (
            <div className="msg-confirm-actions">
              <button
                className="msg-confirm-btn msg-confirm-btn--confirm"
                onClick={() => onConfirm && onConfirm(userQuery)}
              >
                ✅ Confirm Update
              </button>
              <button
                className="msg-confirm-btn msg-confirm-btn--cancel"
                onClick={() => onCancel && onCancel(userQuery)}
              >
                🚫 Cancel
              </button>
            </div>
          )}
        </div>
      </div>
    )
  }

  if (role === 'error') {
    return (
      <div className="msg-row msg-row--assistant">
        <div className="msg-avatar msg-avatar--bot">🧠</div>
        <div className="msg-error-block">
          <div className="msg-bubble msg-bubble--error">
            <strong>Error:</strong> {content}
          </div>
          {suggestions && suggestions.length > 0 && (
            <div className="msg-suggestions">
              <div className="msg-suggestions-label">Did you mean one of these?</div>
              <div className="msg-suggestion-chips">
                {suggestions.map((s, i) => (
                  s.startsWith('None')
                    ? <span key={i} className="msg-suggestion-none">{s}</span>
                    : <button
                        key={i}
                        className="msg-suggestion-chip"
                        onClick={() => onSuggest && onSuggest(s)}
                        title={s}
                      >
                        {s}
                      </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    )
  }

  // Assistant message
  const isVisualizable =
    data?.query?.operation &&
    ['find', 'aggregate'].includes(data.query.operation) &&
    Array.isArray(data?.result) &&
    data.result.length > 0

  return (
    <div className="msg-row msg-row--assistant">
      <div className="msg-avatar msg-avatar--bot">🧠</div>

      <div className="msg-content">
        {/* Two-column: query code + explanation */}
        <div className="result-columns">
          <div className="result-col">
            <div className="result-col-title">Generated Query</div>
            <pre className="query-code">{JSON.stringify(data?.query, null, 2)}</pre>
          </div>

          <div className="result-col">
            <div className="result-col-title">Explanation</div>
            <div className="explanation-box">
              <ReactMarkdown>{content}</ReactMarkdown>
            </div>
          </div>
        </div>

        <hr className="result-divider" />

        {/* Results */}
        <div className="result-col-title">Results</div>
        <ResultsTable data={data?.result} />

        {/* Visualization button */}
        {isVisualizable && (
          <VisualizationChart userQuery={userQuery} resultData={data.result} />
        )}
      </div>
    </div>
  )
}

export default ChatMessage
