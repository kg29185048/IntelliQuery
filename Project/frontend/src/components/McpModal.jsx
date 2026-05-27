import { useState } from 'react'
import './McpModal.css'

const McpModal = ({ token, onClose }) => {
  const [status, setStatus] = useState('idle') // idle | loading_token | token_ready | installing | success | error
  const [error, setError] = useState('')
  const [mcpToken, setMcpToken] = useState('')
  const [copied, setCopied] = useState(false)

  const handleGenerateToken = async () => {
    setStatus('loading_token')
    setError('')
    try {
      if (!token) throw new Error('Please log in first.')

      const res = await fetch('/api/mcp-token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Failed to generate MCP token')
      setMcpToken(data.token)
      setStatus('token_ready')
    } catch (err) {
      setError(err.message)
      setStatus('error')
    }
  }

  const handleCopyConfig = () => {
    const config = JSON.stringify({
      "mcpServers": {
        "intelliquery-agent": {
          "url": `${window.location.origin}/api/mcp/sse`,
          "headers": {
            "Authorization": `Bearer ${mcpToken}`
          }
        }
      }
    }, null, 2)

    navigator.clipboard.writeText(config)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleAutoInstall = async () => {
    setStatus('installing')
    setError('')
    try {
      const res = await fetch('/api/install-mcp', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ mcp_token: mcpToken })
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Failed to configure MCP')
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

        {status === 'success' ? (
          <div className="mcp-success">
            <div className="mcp-success-icon">✅</div>
            <p className="mcp-success-msg">IntelliQuery has been added to Claude Desktop.</p>
            <p className="mcp-restart-note">Fully restart Claude Desktop to activate the connection.</p>
            <div className="mcp-tools-info">
              <p><strong>Claude will have two tools:</strong></p>
              <ul>
                <li>📂 <strong>list_workspaces</strong> — discover your databases</li>
                <li>🔍 <strong>ask_database</strong> — query any workspace</li>
              </ul>
            </div>
            <button className="mcp-connect-btn" onClick={onClose}>Done</button>
          </div>
        ) : (
          <>
            <p className="mcp-modal-desc">
              Connect IntelliQuery as a remote MCP tool in Claude Desktop.
              Your workspaces and permissions carry over automatically.
            </p>

            {/* Step 1: Generate Token */}
            {status === 'idle' || (status === 'error' && !mcpToken) ? (
              <>
                <div className="mcp-step">
                  <span className="mcp-step-badge">1</span>
                  <span>Generate a secure MCP token (valid for 30 days)</span>
                </div>

                {error && <div className="mcp-error">{error}</div>}

                <button
                  className="mcp-connect-btn"
                  onClick={handleGenerateToken}
                  disabled={status === 'loading_token'}
                >
                  {status === 'loading_token' ? 'Generating...' : 'Generate MCP Token'}
                </button>
              </>
            ) : null}

            {/* Step 2: Install or Copy */}
            {(status === 'token_ready' || status === 'installing' || (status === 'error' && mcpToken)) ? (
              <>
                <div className="mcp-step">
                  <span className="mcp-step-badge">✓</span>
                  <span>Token generated successfully</span>
                </div>

                <div className="mcp-step">
                  <span className="mcp-step-badge">2</span>
                  <span>Choose how to connect:</span>
                </div>

                <div className="mcp-actions">
                  <button
                    className="mcp-connect-btn"
                    onClick={handleAutoInstall}
                    disabled={status === 'installing'}
                  >
                    {status === 'installing' ? 'Installing...' : '⚡ Auto-Install (Local Claude)'}
                  </button>

                  <button
                    className="mcp-copy-btn"
                    onClick={handleCopyConfig}
                  >
                    {copied ? '✓ Copied!' : '📋 Copy Config JSON'}
                  </button>
                </div>

                <p className="mcp-hint">
                  <strong>Auto-Install</strong> writes directly to Claude Desktop's config (requires Claude to be installed on this machine).
                  <br />
                  <strong>Copy Config</strong> gives you the JSON to paste manually into <code>claude_desktop_config.json</code>.
                </p>

                {error && <div className="mcp-error">{error}</div>}
              </>
            ) : null}
          </>
        )}
      </div>
    </div>
  )
}

export default McpModal
