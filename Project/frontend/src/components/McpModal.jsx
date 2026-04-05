import { useState } from 'react'
import './McpModal.css'

const MCP_KEY_STORAGE = 'iq_mcp_groq_key'

const McpModal = ({ defaultMongoUri, onClose }) => {
  const savedKey = localStorage.getItem(MCP_KEY_STORAGE) || ''
  const alreadyConnected = !!savedKey

  const [groqKey, setGroqKey] = useState(savedKey)
  const [mongoUri, setMongoUri] = useState(defaultMongoUri || '')
  const [status, setStatus] = useState('idle') // idle | loading | success | error
  const [error, setError] = useState('')

  const handleConnect = async () => {
    if (!groqKey.trim() || !mongoUri.trim()) {
      setError('Both fields are required.')
      return
    }
    setStatus('loading')
    setError('')
    try {
      const res = await fetch('/api/install-mcp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ groq_api_key: groqKey, mongo_uri: mongoUri })
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Failed to configure MCP')
      localStorage.setItem(MCP_KEY_STORAGE, groqKey)
      setStatus('success')
    } catch (err) {
      setError(err.message)
      setStatus('error')
    }
  }

  return (
    <div className="mcp-overlay" onClick={onClose}>
      <div className="mcp-modal" onClick={e => e.stopPropagation()}>
        <div className="mcp-modal-header">
          <span className="mcp-modal-title">Connect to Claude Desktop</span>
          <button className="mcp-close-btn" onClick={onClose}>✕</button>
        </div>

        {status !== 'success' ? (
          <>
            {alreadyConnected && (
              <div className="mcp-already-connected">
                ✅ Previously connected — your saved key is pre-filled. Reconnect to update.
              </div>
            )}
            <p className="mcp-modal-desc">
              Adds IntelliQuery as an MCP tool in Claude Desktop. Fully restart Claude after connecting.
            </p>

            <div className="mcp-field">
              <label>Groq API Key</label>
              <input
                type="password"
                placeholder="gsk_..."
                value={groqKey}
                onChange={e => setGroqKey(e.target.value)}
                disabled={status === 'loading'}
              />
            </div>

            <div className="mcp-field">
              <label>MongoDB URI</label>
              <input
                type="text"
                placeholder="mongodb+srv://..."
                value={mongoUri}
                onChange={e => setMongoUri(e.target.value)}
                disabled={status === 'loading'}
              />
            </div>

            {error && <div className="mcp-error">{error}</div>}

            <button
              className="mcp-connect-btn"
              onClick={handleConnect}
              disabled={status === 'loading'}
            >
              {status === 'loading' ? 'Connecting...' : 'Connect'}
            </button>
          </>
        ) : (
          <div className="mcp-success">
            <div className="mcp-success-icon">✅</div>
            <p className="mcp-success-msg">IntelliQuery has been added to Claude Desktop.</p>
            <p className="mcp-restart-note">Fully restart Claude Desktop to activate the connection.</p>
            <button className="mcp-connect-btn" onClick={onClose}>Done</button>
          </div>
        )}
      </div>
    </div>
  )
}

export default McpModal
