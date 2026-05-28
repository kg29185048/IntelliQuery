import { useState, useEffect, useRef } from 'react'
import Sidebar from './components/Sidebar'
import ChatMessage from './components/ChatMessage'
import ChatInput from './components/ChatInput'
import SignIn from './components/SignIn'
import McpModal from './components/McpModal'
import Dashboard from './components/Dashboard'
import WorkspaceSettings from './components/WorkspaceSettings'
import Home from './components/Home'
import './App.css'
function App() {
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
  })
  const [loading, setLoading] = useState(false)
  const [backendStatus, setBackendStatus] = useState('checking')
  const [sidebarOpen, setSidebarOpen] = useState(() => window.innerWidth > 900)
  const [mcpModalOpen, setMcpModalOpen] = useState(false)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [profileOpen, setProfileOpen] = useState(false)
  const [schema, setSchema] = useState({})   // cached schema for IntentCard collections
  const chatEndRef = useRef(null)
  
  const [signInView, setSignInView] = useState(null) // null = home, 'login' or 'signup'

  const dbType = currentWorkspace?.db_type ?? 'mongodb'

  const buildHeaders = () => {
    return {
      'Authorization': `Bearer ${token}`,
      'X-Workspace-Id': currentWorkspace?.id,
    }
  }

  // llm history format: [{user, query}]
  const llmHistory = messages
    .filter(m => m.role === 'assistant' && m.data)
    .slice(-5)
    .map(m => ({ user: m.userQuery, query: JSON.stringify(m.data.query) }))

  useEffect(() => {
    if (!token) return
    const checkBackend = async () => {
      try {
        const res = await fetch('/api/health')
        setBackendStatus(res.ok ? 'online' : 'offline')
      } catch {
        setBackendStatus('offline')
      }
    }
    checkBackend()
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

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

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
  }

  const handleSignOut = () => {
    sessionStorage.removeItem('iq_auth')
    setAuthData(null)
    setCurrentWorkspace(null)
    setMessages([])
    setBackendStatus('checking')
  }

  // ── Phase 1: extract intent ─────────────────────────────────────────────
  const handleSend = async (query) => {
    setMessages(prev => [...prev, { role: 'user', content: query }])
    setLoading(true)
    try {
      const response = await fetch('/api/extract-intent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...buildHeaders() },
        body: JSON.stringify({ query, history: llmHistory })
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

      // Show IntentCard for user to review/edit
      setMessages(prev => [...prev, {
        role: 'intent',
        extracted_intent: data.extracted_intent,
        collections: Object.keys(schema),
        userQuery: query,
      }])
    } catch (err) {
      setMessages(prev => [...prev, { role: 'error', content: err.message }])
    } finally {
      setLoading(false)
    }
  }

  // ── Phase 2: run query with confirmed intent ────────────────────────────
  const handleIntentConfirm = async (originalQuery, confirmedIntent) => {
    // Mark the intent card as resolved
    setMessages(prev => prev.map(m =>
      m.role === 'intent' && m.userQuery === originalQuery && !m.resolved
        ? { ...m, resolved: true }
        : m
    ))
    setLoading(true)
    try {
      const response = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...buildHeaders() },
        body: JSON.stringify({
          query: originalQuery,
          history: llmHistory,
          confirmed_intent: confirmedIntent,
        })
      })
      let data
      const text = await response.text()
      try { data = JSON.parse(text) } catch { throw new Error(text || `Server error ${response.status}`) }
      if (!response.ok) throw new Error(data.detail || `Server error ${response.status}`)

      if (data.requires_confirmation) {
        setMessages(prev => [...prev, {
          role: 'confirm',
          content: data.explanation,
          data: { query: data.query },
          userQuery: originalQuery,
        }])
        return
      }
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

  // ── Start Over: remove the pending IntentCard ───────────────────────────
  const handleIntentReset = () => {
    setMessages(prev => {
      // Remove the last unresolved intent card and its preceding user bubble
      const lastIntentIdx = [...prev].reverse().findIndex(m => m.role === 'intent' && !m.resolved)
      if (lastIntentIdx === -1) return prev
      const realIdx = prev.length - 1 - lastIntentIdx
      return prev.filter((_, i) => i !== realIdx && i !== realIdx - 1)
    })
  }

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

  if (!authData) {
    if (!signInView) {
      return <Home onNavigate={setSignInView} />
    }
    return <SignIn onSignIn={handleSignIn} initialView={signInView} onBackToHome={() => setSignInView(null)} />
  }
  if (!currentWorkspace) return <Dashboard user={user} token={token} onSelectWorkspace={setCurrentWorkspace} onSignOut={handleSignOut} />

  const statusColor = { checking: '#f0ad4e', online: '#28a745', offline: '#dc3545' }
  const statusLabel = { checking: 'Checking...', online: 'Backend Online', offline: 'Backend Offline' }

  return (
    <div className="app-shell">
      {/* Mobile Backdrop */}
      {sidebarOpen && <div className="mobile-backdrop" onClick={() => setSidebarOpen(false)} />}

      {/* Sidebar */}
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} onClear={handleClear} workspaceId={currentWorkspace.id} dbType={dbType} token={token} />

      {/* Main area */}
      <div className={`main-area ${sidebarOpen ? 'sidebar-open' : 'sidebar-closed'}`}>
        {/* Top navbar */}
        <div className="top-navbar">
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
            </div>
          </div>
          <div className="navbar-right">
            <div className="status-badge">
              <span className="status-dot" style={{ background: statusColor[backendStatus] }} />
              {statusLabel[backendStatus]}
            </div>
            <button className="nav-btn hide-mobile" onClick={() => setSettingsOpen(true)}>
              Settings
            </button>
            {import.meta.env.DEV && (
              <button className="nav-btn hide-mobile" onClick={() => setMcpModalOpen(true)} title="Connect to Claude Desktop">
                Claude {localStorage.getItem('iq_mcp_groq_key') ? <span className="mcp-nav-dot" /> : null}
              </button>
            )}
            <button className="nav-btn nav-btn--danger" onClick={() => setCurrentWorkspace(null)} title="Back to Dashboard">
              <span className="hide-text-mobile">Dashboard</span> <span style={{ opacity: 0.6 }}>↩</span>
            </button>
            <div className="profile-menu-container">
              <button className="profile-btn" onClick={() => setProfileOpen(!profileOpen)}>
                {user?.email?.charAt(0).toUpperCase() || 'U'}
              </button>
              {profileOpen && (
                <>
                  <div className="profile-backdrop" onClick={() => setProfileOpen(false)} />
                  <div className="profile-dropdown">
                    <div className="profile-header">
                      <strong>{user?.email}</strong>
                    </div>
                    <button className="profile-dropdown-item" onClick={handleSignOut}>
                      Sign Out
                    </button>
                  </div>
                </>
              )}
            </div>
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
            <ChatMessage
              key={idx}
              message={msg}
              onSuggest={handleSend}
              onConfirm={handleConfirmUpdate}
              onCancel={handleCancelUpdate}
              onIntentConfirm={handleIntentConfirm}
              onIntentReset={handleIntentReset}
            />
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
    </div>
  )
}

export default App
