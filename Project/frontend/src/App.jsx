import { useState, useEffect, useRef } from 'react'
import Sidebar from './components/Sidebar'
import ChatMessage from './components/ChatMessage'
import ChatInput from './components/ChatInput'
import SignIn from './components/SignIn'
import McpModal from './components/McpModal'
import './App.css'

function App() {
  const [user, setUser] = useState(() => {
    try { return JSON.parse(sessionStorage.getItem('iq_user')) } catch { return null }
  })
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [backendStatus, setBackendStatus] = useState('checking')
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [mcpModalOpen, setMcpModalOpen] = useState(false)
  const chatEndRef = useRef(null)

  const mongoUri    = user?.mongoUri    ?? ''
  const mongoDbName = user?.mongoDbName ?? ''
  const sqlUri      = user?.sqlUri      ?? ''
  const dbType      = user?.dbType      ?? 'mongodb'

  const buildDbHeaders = () => {
    const h = { 'X-Db-Type': dbType }
    if (dbType === 'mongodb') {
      h['X-Mongo-Uri'] = mongoUri
      if (mongoDbName) h['X-Mongo-Db'] = mongoDbName
    } else {
      h['X-Sql-Uri'] = sqlUri
    }
    return h
  }

  // llm history format: [{user, query}]
  const llmHistory = messages
    .filter(m => m.role === 'assistant' && m.data)
    .slice(-5)
    .map(m => ({ user: m.userQuery, query: JSON.stringify(m.data.query) }))

  useEffect(() => {
    if (!user) return
    const checkBackend = async () => {
      try {
        const res = await fetch('/api/health', { headers: buildDbHeaders() })
        setBackendStatus(res.ok ? 'online' : 'offline')
      } catch {
        setBackendStatus('offline')
      }
    }
    checkBackend()
  }, [user])

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const handleSignIn = (userData) => {
    sessionStorage.setItem('iq_user', JSON.stringify(userData))
    setUser(userData)
  }

  const handleSignOut = () => {
    sessionStorage.removeItem('iq_user')
    setUser(null)
    setMessages([])
    setBackendStatus('checking')
  }

  const handleSend = async (query) => {
    setMessages(prev => [...prev, { role: 'user', content: query }])
    setLoading(true)
    try {
      const response = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...buildDbHeaders() },
        body: JSON.stringify({ query, history: llmHistory })
      })
      let data
      const text = await response.text()
      try { data = JSON.parse(text) } catch { throw new Error(text || `Server error ${response.status}`) }
      if (!response.ok) throw new Error(data.detail || `Server error ${response.status}`)

      // Soft failure: server returned suggestions instead of results
      if (data.error && data.suggestions) {
        setMessages(prev => [...prev, {
          role: 'error',
          content: data.error,
          suggestions: data.suggestions,
        }])
        return
      }

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.explanation,
        data,
        userQuery: query
      }])
    } catch (err) {
      setMessages(prev => [...prev, { role: 'error', content: err.message }])
    } finally {
      setLoading(false)
    }
  }

  const handleClear = () => setMessages([])

  if (!user) return <SignIn onSignIn={handleSignIn} />

  const statusColor = { checking: '#f0ad4e', online: '#28a745', offline: '#dc3545' }
  const statusLabel = { checking: 'Checking...', online: 'Backend Online', offline: 'Backend Offline' }

  return (
    <div className="app-shell">
      {/* Sidebar */}
      <Sidebar open={sidebarOpen} onClear={handleClear} mongoUri={mongoUri} mongoDbName={mongoDbName} sqlUri={sqlUri} dbType={dbType} />

      {/* Main area */}
      <div className={`main-area ${sidebarOpen ? 'sidebar-open' : 'sidebar-closed'}`}>
        {/* Top navbar */}
        <div className="top-navbar">
          <button className="sidebar-toggle" onClick={() => setSidebarOpen(o => !o)}>
            ☰
          </button>
          <div className="navbar-brand">
            <div>
              <div className="navbar-title">IntelliQuery</div>
              <div className="navbar-subtitle">Natural Language → {dbType === 'mongodb' ? 'MongoDB' : dbType.charAt(0).toUpperCase() + dbType.slice(1)}</div>
            </div>
          </div>
          <div className="navbar-right">
            <div className="status-badge">
              <span className="status-dot" style={{ background: statusColor[backendStatus] }} />
              {statusLabel[backendStatus]}
            </div>
            <button className="mcp-nav-btn" onClick={() => setMcpModalOpen(true)} title="Connect to Claude Desktop">
              🤖 Claude
            </button>
            <button className="signout-btn" onClick={handleSignOut} title="Sign out">
              <span className="signout-name">{user.name}</span>
              <span className="signout-arrow">↩</span>
            </button>
          </div>
        </div>

        {/* Chat messages */}
        <div className="chat-area">
          {backendStatus === 'offline' && (
            <div className="offline-banner">
              <strong>Backend offline.</strong> Run: <code>uvicorn api.main:app --reload</code>
            </div>
          )}

          {messages.length === 0 && (
            <div className="empty-state">
              <h3>What would you like to know?</h3>
              <p>Ask anything about your database in plain English.</p>
              <div className="example-chips">
                {[
                  'Show me all documents',
                  'Count records by category',
                  'Find top 5 by rating',
                  'Show recent entries'
                ].map(ex => (
                  <button key={ex} className="chip" onClick={() => handleSend(ex)}>{ex}</button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, idx) => (
            <ChatMessage key={idx} message={msg} onSuggest={handleSend} />
          ))}

          {loading && (
            <div className="typing-indicator">
              <div className="typing-bubble"><span /><span /><span /></div>
              <small>Processing your query...</small>
            </div>
          )}

          <div ref={chatEndRef} />
        </div>

        {/* Chat Input */}
        <ChatInput onSend={handleSend} loading={loading} />
      </div>

      {/* MCP Connect Modal */}
      {mcpModalOpen && (
        <McpModal
          defaultMongoUri={mongoUri}
          onClose={() => setMcpModalOpen(false)}
        />
      )}
    </div>
  )
}

export default App
