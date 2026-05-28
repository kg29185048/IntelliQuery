import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import ResultsTable from './ResultsTable'
import VisualizationChart from './VisualizationChart'
import IntentCard from './IntentCard'
import './ChatMessage.css'

const BotIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="11" width="18" height="10" rx="2" />
    <circle cx="12" cy="5" r="2" />
    <path d="M12 7v4" />
    <line x1="8" y1="16" x2="8.01" y2="16" />
    <line x1="16" y1="16" x2="16.01" y2="16" />
  </svg>
)

const UserIcon = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" />
    <circle cx="12" cy="7" r="4" />
  </svg>
)

const ChatMessage = ({ message, onSuggest, onConfirm, onCancel, onIntentConfirm, onIntentReset }) => {
  const { role, content, data, userQuery, suggestions } = message

  // ── Intent confirmation card (Phase 1 output) ──────────────────────────
  if (role === 'intent') {
    const { resolved, extracted_intent, collections } = message
    if (resolved) {
      return (
        <div className="msg-row msg-row--assistant">
          <div className="msg-avatar msg-avatar--bot"><BotIcon /></div>
          <div className="msg-bubble msg-bubble--intent-resolved">
            Intent confirmed — generating query…
          </div>
        </div>
      )
    }
    return (
      <div className="msg-row msg-row--assistant">
        <div className="msg-avatar msg-avatar--bot"><BotIcon /></div>
        <IntentCard
          intent={extracted_intent}
          collections={collections || []}
          onConfirm={(editedIntent) => onIntentConfirm && onIntentConfirm(userQuery, editedIntent)}
          onStartOver={() => onIntentReset && onIntentReset()}
        />
      </div>
    )
  }

  if (role === 'user') {
    return (
      <div className="msg-row msg-row--user">
        <div className="msg-bubble msg-bubble--user">
          {content}
        </div>
        <div className="msg-avatar msg-avatar--user"><UserIcon /></div>
      </div>
    )
  }

  if (role === 'confirm') {
    const { resolved, cancelled } = message
    return (
      <div className="msg-row msg-row--assistant">
        <div className="msg-avatar msg-avatar--bot"><BotIcon /></div>
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
              {cancelled ? '🚫 Update cancelled.' : 'Update confirmed — executing…'}
            </div>
          ) : (
            <div className="msg-confirm-actions">
              <button
                className="msg-confirm-btn msg-confirm-btn--confirm"
                onClick={() => onConfirm && onConfirm(userQuery, data?.confirmed_intent)}
              >
                Confirm Update
              </button>
              <button
                className="msg-confirm-btn msg-confirm-btn--cancel"
                onClick={() => onCancel && onCancel(userQuery)}
              >
                🚫Cancel
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
        <div className="msg-avatar msg-avatar--bot"><BotIcon /></div>
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
      <div className="msg-avatar msg-avatar--bot"><BotIcon /></div>

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
