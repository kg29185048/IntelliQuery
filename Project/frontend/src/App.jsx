import { useState, useEffect, useRef } from 'react'
import Sidebar from './components/Sidebar'
import ChatMessage from './components/ChatMessage'
import ChatInput from './components/ChatInput'
import SignIn from './components/SignIn'
import './App.css'

function App() {
<<<<<<< Updated upstream
  const [user, setUser] = useState(() => {
    try { return JSON.parse(sessionStorage.getItem('iq_user')) } catch { return null }
=======
  const [authData, setAuthData] = useState(() => {
    try { return JSON.parse(sessionStorage.getItem('iq_auth')) } catch { return null }
  })

  const user = authData?.user
  const token = authData?.token

  const [currentWorkspace, setCurrentWorkspace] = useState(null)

  const [messages, setMessages] = useState(() => {
    try {
      if (!user?.email || !currentWorkspace?.id) return []
      return JSON.parse(localStorage.getItem(`iq_history_${user.email}_ws_${currentWorkspace.id}`)) || []
    } catch { return [] }
>>>>>>> Stashed changes
  })
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [backendStatus, setBackendStatus] = useState('checking')
<<<<<<< Updated upstream
  const [sidebarOpen, setSidebarOpen] = useState(true)
=======
  const [sidebarOpen, setSidebarOpen] = useState(() => window.innerWidth > 900)
  const [mcpModalOpen, setMcpModalOpen] = useState(false)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [schema, setSchema] = useState({})   // cached schema for IntentCard collections
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
  }, [user])
=======
  }, [token])

  // Auto-collapse sidebar on resize
  useEffect(() => {
    const mql = window.matchMedia('(max-width: 900px)')
    const handleMediaChange = (e) => setSidebarOpen(!e.matches)
    mql.addEventListener('change', handleMediaChange)
    return () => mql.removeEventListener('change', handleMediaChange)
  }, [])

  // Fetch schema for collection list in IntentCard
  useEffect(() => {
    if (!token || !currentWorkspace?.id) return
    const fetchSchema = async () => {
      try {
        const res = await fetch('/api/schema', { headers: buildHeaders() })
        if (res.ok) {
          const data = await res.json()
          setSchema(data.schema || {})
        }
      } catch { }
    }
    fetchSchema()
  }, [token, currentWorkspace?.id])
>>>>>>> Stashed changes

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

<<<<<<< Updated upstream
  const handleSignIn = (userData) => {
    sessionStorage.setItem('iq_user', JSON.stringify(userData))
    setUser(userData)
=======
  // Persist chat history to localStorage scoped to the user and workspace
  useEffect(() => {
    if (!user?.email || !currentWorkspace?.id) return
    try { localStorage.setItem(`iq_history_${user.email}_ws_${currentWorkspace.id}`, JSON.stringify(messages)) } catch { }
  }, [messages, user?.email, currentWorkspace?.id])

  // When workspace changes, load its history
  useEffect(() => {
    if (!user?.email || !currentWorkspace?.id) {
      setMessages([])
      return
    }
    try {
      const hist = JSON.parse(localStorage.getItem(`iq_history_${user.email}_ws_${currentWorkspace.id}`)) || []
      setMessages(hist)
    } catch {
      setMessages([])
    }
  }, [currentWorkspace?.id, user?.email])

  const handleSignIn = (data) => {
    sessionStorage.setItem('iq_auth', JSON.stringify(data))
    setAuthData(data)
>>>>>>> Stashed changes
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

<<<<<<< Updated upstream
  if (!user) return <SignIn onSignIn={handleSignIn} />
=======
  const handleConfirmUpdate = async (originalQuery) => {
    // Mark the confirm bubble as resolved so buttons are disabled
    setMessages(prev => prev.map(m =>
      m.role === 'confirm' && m.userQuery === originalQuery
        ? { ...m, resolved: true }
        : m
    ))
    setLoading(true)
    try {
      const response = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...buildHeaders() },
        body: JSON.stringify({ query: originalQuery, history: llmHistory, confirmed: true })
      })
      let data
      const text = await response.text()
      try { data = JSON.parse(text) } catch { throw new Error(text || `Server error ${response.status}`) }
      if (!response.ok) throw new Error(data.detail || `Server error ${response.status}`)
      if (data.error && data.suggestions) {
        setMessages(prev => [...prev, { role: 'error', content: data.error, suggestions: data.suggestions }])
        return
      }
      if (data.error) {
        setMessages(prev => [...prev, { role: 'error', content: data.error }])
        return
      }
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.explanation,
        data,
        userQuery: originalQuery
      }])
    } catch (err) {
      setMessages(prev => [...prev, { role: 'error', content: err.message }])
    } finally {
      setLoading(false)
    }
  }

  const handleCancelUpdate = (originalQuery) => {
    setMessages(prev => prev.map(m =>
      m.role === 'confirm' && m.userQuery === originalQuery
        ? { ...m, resolved: true, cancelled: true }
        : m
    ))
  }

  const handleClear = () => {
    setMessages([])
    if (user?.email && currentWorkspace?.id) {
      localStorage.removeItem(`iq_history_${user.email}_ws_${currentWorkspace.id}`)
    }
  }

  if (!authData) return <SignIn onSignIn={handleSignIn} />
  if (!currentWorkspace) return <Dashboard user={user} token={token} onSelectWorkspace={setCurrentWorkspace} onSignOut={handleSignOut} />
>>>>>>> Stashed changes

  const statusColor = { checking: '#f0ad4e', online: '#28a745', offline: '#dc3545' }
  const statusLabel = { checking: 'Checking...', online: 'Backend Online', offline: 'Backend Offline' }

  return (
    <div className="app-shell">
<<<<<<< Updated upstream
      {/* Sidebar */}
      <Sidebar open={sidebarOpen} onClear={handleClear} mongoUri={mongoUri} mongoDbName={mongoDbName} sqlUri={sqlUri} dbType={dbType} />
=======
      {/* Mobile Backdrop */}
      {sidebarOpen && <div className="mobile-backdrop" onClick={() => setSidebarOpen(false)} />}

      {/* Sidebar */}
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} onClear={handleClear} workspaceId={currentWorkspace.id} dbType={dbType} token={token} />
>>>>>>> Stashed changes

      {/* Main area */}
      <div className={`main-area ${sidebarOpen ? 'sidebar-open' : 'sidebar-closed'}`}>
        {/* Top navbar */}
        <div className="top-navbar">
<<<<<<< Updated upstream
          <button className="sidebar-toggle" onClick={() => setSidebarOpen(o => !o)}>
            ☰
          </button>
          <div className="navbar-brand">
            <div>
              <div className="navbar-title">IntelliQuery</div>
              <div className="navbar-subtitle">Natural Language → {dbType === 'mongodb' ? 'MongoDB' : dbType.charAt(0).toUpperCase() + dbType.slice(1)}</div>
=======
          <div className="navbar-brand">
            <button className="navbar-hamburger" onClick={() => setSidebarOpen(!sidebarOpen)} aria-label="Toggle sidebar">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <div className="navbar-title">IntelliQuery</div>
            <div className="navbar-divider" />
            <div className="navbar-subtitle">
              {currentWorkspace.name}
              <span className="navbar-db-type">{dbType === 'mongodb' ? 'MongoDB' : dbType.charAt(0).toUpperCase() + dbType.slice(1)}</span>
>>>>>>> Stashed changes
            </div>
          </div>
          <div className="navbar-right">
            <div className="status-badge">
              <span className="status-dot" style={{ background: statusColor[backendStatus] }} />
              {statusLabel[backendStatus]}
            </div>
<<<<<<< Updated upstream
            <button className="signout-btn" onClick={handleSignOut} title="Sign out">
              <span className="signout-name">{user.name}</span>
              <span className="signout-arrow">↩</span>
=======
            <button className="nav-btn hide-mobile" onClick={() => setSettingsOpen(true)}>
              Settings
            </button>
            <button className="nav-btn hide-mobile" onClick={() => setMcpModalOpen(true)} title="Connect to Claude Desktop">
              Claude {localStorage.getItem('iq_mcp_groq_key') ? <span className="mcp-nav-dot" /> : null}
            </button>
            <button className="nav-btn nav-btn--danger" onClick={() => setCurrentWorkspace(null)} title="Back to Dashboard">
              <span className="hide-text-mobile">Dashboard</span> <span style={{ opacity: 0.6 }}>↩</span>
>>>>>>> Stashed changes
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
            <ChatMessage key={idx} message={msg} />
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
<<<<<<< Updated upstream
=======

      {/* MCP Connect Modal */}
      {mcpModalOpen && (
        <McpModal
          defaultMongoUri={""}
          onClose={() => setMcpModalOpen(false)}
        />
      )}

      {/* Workspace Settings Modal */}
      {settingsOpen && (
        <WorkspaceSettings
          workspace={currentWorkspace}
          user={user}
          token={token}
          onClose={() => setSettingsOpen(false)}
          onWorkspaceDeleted={() => {
            setSettingsOpen(false)
            setCurrentWorkspace(null)
          }}
        />
      )}
>>>>>>> Stashed changes
    </div>
  )
}

export default App
