import { useState, useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'
import './Dashboard.css'

const DB_TYPES = [
  { value: 'mongodb',    label: 'MongoDB' },
  { value: 'postgresql', label: 'PostgreSQL' },
  { value: 'mysql',      label: 'MySQL' },
  { value: 'sqlite',     label: 'SQLite' },
]

const SQL_TYPES = new Set(['postgresql', 'mysql', 'sqlite'])

const SQL_PLACEHOLDERS = {
  postgresql: 'postgresql+psycopg2://user:pass@host:5432/dbname',
  mysql:      'mysql+pymysql://user:pass@host:3306/dbname',
  sqlite:     'sqlite:////absolute/path/to/database.db',
}

const Dashboard = ({ user, token, onSelectWorkspace, onSignOut }) => {
  const [workspaces, setWorkspaces] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const [showCreate, setShowCreate] = useState(false)
  const [showJoin, setShowJoin] = useState(false)
  const [profileOpen, setProfileOpen] = useState(false)
  const [dropdownPos, setDropdownPos] = useState({ top: 0, right: 0 })
  const profileBtnRef = useRef(null)

  // Create Form State
  const [createForm, setCreateForm] = useState({
    name: '', dbType: 'mongodb', dbUri: '', dbName: ''
  })
  const [createLoading, setCreateLoading] = useState(false)

  // Join Form State
  const [joinCode, setJoinCode] = useState('')
  const [joinLoading, setJoinLoading] = useState(false)

  const fetchWorkspaces = async () => {
    setLoading(true)
    try {
      const res = await fetch('/api/workspaces/', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (!res.ok) throw new Error('Failed to fetch workspaces')
      const data = await res.json()
      setWorkspaces(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchWorkspaces()
  }, [])

  const handleCreate = async (e) => {
    e.preventDefault()
    setCreateLoading(true)
    try {
      const res = await fetch('/api/workspaces/', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          name: createForm.name,
          db_type: createForm.dbType,
          db_uri: createForm.dbUri,
          db_name: createForm.dbType === 'mongodb' ? createForm.dbName : null
        })
      })
      if (!res.ok) throw new Error('Failed to create workspace')
      await fetchWorkspaces()
      setShowCreate(false)
      setCreateForm({ name: '', dbType: 'mongodb', dbUri: '', dbName: '' })
    } catch (err) {
      alert(err.message)
    } finally {
      setCreateLoading(false)
    }
  }

  const handleJoin = async (e) => {
    e.preventDefault()
    setJoinLoading(true)
    try {
      const res = await fetch('/api/workspaces/join', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ join_code: joinCode })
      })
      if (!res.ok) throw new Error('Failed to join workspace. Invalid code?')
      await fetchWorkspaces()
      setShowJoin(false)
      setJoinCode('')
    } catch (err) {
      alert(err.message)
    } finally {
      setJoinLoading(false)
    }
  }

  const isSql = SQL_TYPES.has(createForm.dbType)

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <div className="dashboard-header-content">
          <h1>Welcome, {user.name}</h1>
          <div className="dashboard-actions">
            <button className="btn-outline" onClick={() => setShowJoin(true)}>Join Workspace</button>
            <button className="btn-outline" onClick={() => setShowCreate(true)}>Create Workspace</button>
            <div className="profile-menu-container">
              <button
                ref={profileBtnRef}
                className="profile-btn"
                onClick={() => {
                  if (!profileOpen && profileBtnRef.current) {
                    const rect = profileBtnRef.current.getBoundingClientRect()
                    setDropdownPos({
                      top: rect.bottom + 8,
                      right: window.innerWidth - rect.right
                    })
                  }
                  setProfileOpen(prev => !prev)
                }}
              >
                {user?.email?.charAt(0).toUpperCase() || 'U'}
              </button>
              {profileOpen && createPortal(
                <>
                  <div
                    style={{ position: 'fixed', inset: 0, zIndex: 9998 }}
                    onClick={() => setProfileOpen(false)}
                  />
                  <div
                    className="profile-dropdown"
                    style={{
                      position: 'fixed',
                      top: dropdownPos.top,
                      right: dropdownPos.right,
                      zIndex: 9999
                    }}
                  >
                    <div className="profile-header">
                      <strong>{user?.email}</strong>
                    </div>
                    <button className="profile-dropdown-item" onClick={onSignOut}>
                      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                        <polyline points="16 17 21 12 16 7"/>
                        <line x1="21" y1="12" x2="9" y2="12"/>
                      </svg>
                      Logout
                    </button>
                  </div>
                </>,
                document.body
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="dashboard-main">
        {loading ? (
          <div className="loading-spinner">Loading workspaces...</div>
        ) : error ? (
          <div className="error-msg">{error}</div>
        ) : workspaces.length === 0 ? (
          <div className="empty-state">
            <h3>No Workspaces Yet</h3>
            <p>Create a new workspace or join an existing one to get started.</p>
          </div>
        ) : (
          <div className="workspaces-grid">
            {workspaces.map(ws => (
              <div key={ws.id} className="workspace-card" onClick={() => onSelectWorkspace(ws)}>
                <div className="ws-icon">{ws.name.charAt(0).toUpperCase()}</div>
                <div className="ws-info">
                  <h3>{ws.name}</h3>
                  <div className="ws-meta">
                    <span className="ws-role badge">{ws.role}</span>
                    <span className="ws-db badge outline">{ws.db_type}</span>
                  </div>
                  {ws.role === 'admin' && (
                    <div className="ws-code"
                         onClick={(e) => {
                           e.stopPropagation();
                           navigator.clipboard.writeText(ws.join_code);
                           alert('Join code copied to clipboard!');
                         }}
                         style={{ cursor: 'pointer' }}
                         title="Click to copy"
                    >
                      Join Code: <code>{ws.join_code}</code> 📋
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Modals */}
      {showCreate && (
        <div className="modal-overlay" onClick={() => setShowCreate(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <h2>Create Workspace</h2>
            <form onSubmit={handleCreate}>
              <div className="form-group">
                <label>Workspace Name</label>
                <input required value={createForm.name} onChange={e => setCreateForm({...createForm, name: e.target.value})} placeholder="e.g. Sales DB" />
              </div>

              <div className="form-group">
                <label>Database Type</label>
                <div className="db-tabs">
                  {DB_TYPES.map(db => (
                    <button type="button" key={db.value} className={`db-tab ${createForm.dbType === db.value ? 'active' : ''}`} onClick={() => setCreateForm({...createForm, dbType: db.value})}>
                      {db.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="form-group">
                <label>{isSql ? 'Connection URI' : 'MongoDB URI'}</label>
                <input required value={createForm.dbUri} onChange={e => setCreateForm({...createForm, dbUri: e.target.value})} placeholder={isSql ? SQL_PLACEHOLDERS[createForm.dbType] : 'mongodb+srv://...'} />
              </div>

              {!isSql && (
                <div className="form-group">
                  <label>Database Name</label>
                  <input required value={createForm.dbName} onChange={e => setCreateForm({...createForm, dbName: e.target.value})} placeholder="e.g. sample_mflix" />
                </div>
              )}

              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowCreate(false)}>Cancel</button>
                <button type="submit" className="btn-primary" disabled={createLoading}>{createLoading ? 'Creating...' : 'Create'}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showJoin && (
        <div className="modal-overlay" onClick={() => setShowJoin(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <h2>Join Workspace</h2>
            <form onSubmit={handleJoin}>
              <div className="form-group">
                <label>Join Code</label>
                <input required value={joinCode} onChange={e => setJoinCode(e.target.value.toUpperCase())} placeholder="Enter 6-character code" maxLength={6} />
              </div>
              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowJoin(false)}>Cancel</button>
                <button type="submit" className="btn-primary" disabled={joinLoading}>{joinLoading ? 'Joining...' : 'Join'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default Dashboard
