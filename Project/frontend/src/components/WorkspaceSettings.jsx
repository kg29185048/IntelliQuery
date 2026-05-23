import { useState, useEffect } from 'react'
import './WorkspaceSettings.css'

const WorkspaceSettings = ({ workspace, token, onClose }) => {
  const [members, setMembers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchMembers = async () => {
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
            <p><strong>Join Code:</strong> <code className="join-code">{workspace.join_code}</code></p>
            <p className="hint">Share this code with users to let them join your workspace.</p>
          </div>

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
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default WorkspaceSettings
