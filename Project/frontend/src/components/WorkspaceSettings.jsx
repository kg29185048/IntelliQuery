import { useState, useEffect } from 'react'
import './WorkspaceSettings.css'

const WorkspaceSettings = ({ workspace, user, token, onClose, onWorkspaceDeleted }) => {
  const [members, setMembers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchMembers = async () => {
    if (workspace.role !== 'admin') {
      setLoading(false)
      return
    }
    setLoading(true)
    try {
      const res = await fetch(`/api/workspaces/${workspace.id}/members`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (!res.ok) throw new Error('Failed to load members')
      const data = await res.json()
      setMembers(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchMembers()
  }, [workspace.id, token])

  const handleUpdatePermission = async (userId, newPermission) => {
    try {
      const res = await fetch(`/api/workspaces/${workspace.id}/members/${userId}`, {
        method: 'PUT',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ permission: newPermission })
      })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Failed to update permission')
      }
      fetchMembers()
    } catch (err) {
      alert(err.message)
    }
  }

  const handleRemoveMember = async (userId, isSelf) => {
    if (!window.confirm(isSelf ? "Are you sure you want to leave this workspace?" : "Are you sure you want to remove this user?")) return;
    try {
      const res = await fetch(`/api/workspaces/${workspace.id}/members/${userId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Failed to remove member')
      }
      if (isSelf) {
        if (onWorkspaceDeleted) onWorkspaceDeleted()
      } else {
        fetchMembers()
      }
    } catch (err) {
      alert(err.message)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="settings-modal" onClick={e => e.stopPropagation()}>
        <div className="settings-header">
          <h2>Workspace Settings</h2>
          <button className="close-btn" onClick={onClose}>&times;</button>
        </div>

        <div className="settings-content">
          <div className="ws-details">
            <p><strong>Name:</strong> {workspace.name}</p>
            <p><strong>Join Code:</strong> <code 
              className="join-code"
              onClick={() => {
                navigator.clipboard.writeText(workspace.join_code);
                alert('Join code copied to clipboard!');
              }}
              style={{ cursor: 'pointer' }}
              title="Click to copy"
            >
              {workspace.join_code} 📋
            </code></p>
            <p className="hint">Share this code with users to let them join your workspace.</p>
          </div>

          {workspace.role === 'admin' && (
            <>
              <h3>Members</h3>
              {loading ? (
                <p>Loading members...</p>
              ) : error ? (
                <p className="error-text">{error}</p>
              ) : (
                <div className="members-list">
                  {members.map(member => (
                    <div key={member.user_id} className="member-item">
                      <div className="member-info">
                        <div className="member-name">{member.name}</div>
                        <div className="member-email">{member.email}</div>
                      </div>
                      <div className="member-controls">
                        <span className="role-badge">{member.role}</span>
                        {member.role !== 'admin' && (
                          <select 
                            value={member.permission} 
                            onChange={(e) => handleUpdatePermission(member.user_id, e.target.value)}
                            className="permission-select"
                          >
                            <option value="read_only">Read Only</option>
                            <option value="read_write">Read & Write</option>
                          </select>
                        )}
                        {workspace.role === 'admin' && member.user_id !== user.id && (
                          <button 
                            className="btn-danger" 
                            style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }}
                            onClick={() => handleRemoveMember(member.user_id, false)}
                          >
                            Remove
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}

          {/* Actions Section */}
          <div className="workspace-actions">
            <button 
              className="btn-outline-danger" 
              onClick={() => handleRemoveMember(user.id, true)}
            >
              Leave Workspace
            </button>

            {workspace.role === 'admin' && (
              <button 
                className="btn-outline-danger" 
                onClick={async () => {
                  if (window.confirm(`Are you absolutely sure you want to delete the workspace "${workspace.name}"? This action cannot be undone.`)) {
                    try {
                      const res = await fetch(`/api/workspaces/${workspace.id}`, {
                        method: 'DELETE',
                        headers: { 'Authorization': `Bearer ${token}` }
                      })
                      if (!res.ok) {
                        const data = await res.json()
                        throw new Error(data.detail || 'Failed to delete workspace')
                      }
                      if (onWorkspaceDeleted) onWorkspaceDeleted()
                    } catch (err) {
                      alert(err.message)
                    }
                  }
                }}
              >
                Delete Workspace
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default WorkspaceSettings
