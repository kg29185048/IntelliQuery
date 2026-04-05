import { useEffect, useState } from 'react'
import './Sidebar.css'

const Sidebar = ({ open, onClear, mongoUri, mongoDbName, sqlUri, dbType = 'mongodb' }) => {
  const [schema, setSchema] = useState(null)
  const [loading, setLoading] = useState(false)
  const [schemaError, setSchemaError] = useState('')
  const [expanded, setExpanded] = useState({})

  useEffect(() => {
    if (dbType === 'mongodb' && !mongoUri) return
    if (dbType !== 'mongodb' && !sqlUri) return

    const fetchSchema = async () => {
      setLoading(true)
      setSchemaError('')
      setSchema(null)
      const headers = { 'X-Db-Type': dbType }
      if (dbType === 'mongodb') {
        headers['X-Mongo-Uri'] = mongoUri
        if (mongoDbName) headers['X-Mongo-Db'] = mongoDbName
      } else {
        headers['X-Sql-Uri'] = sqlUri
      }
      try {
        const res = await fetch('/api/schema', { headers })
        const data = await res.json()
        if (!res.ok) {
          setSchemaError(data.detail || 'Failed to load schema')
        } else {
          setSchema(data.schema)
        }
      } catch {
        setSchemaError('Network error — is the backend running?')
      } finally {
        setLoading(false)
      }
    }
    fetchSchema()
  }, [mongoUri, mongoDbName, sqlUri, dbType])

  const toggle = (col) => setExpanded(prev => ({ ...prev, [col]: !prev[col] }))

  return (
    <div className={`sidebar ${open ? 'sidebar--open' : 'sidebar--closed'}`}>
      <div className="sidebar-header">
        <div className="sidebar-logo">
          IntelliQuery
          <small>Natural Language → {dbType === 'mongodb' ? 'MongoDB' : dbType.charAt(0).toUpperCase() + dbType.slice(1)}</small>
        </div>
      </div>

      <button className="btn-new-chat" onClick={onClear}>
        + New Chat
      </button>

      <div className="sidebar-section-label">Database Schema</div>

      <div className="sidebar-body">
        {loading && <p className="sidebar-loading">Loading schema...</p>}

        {!loading && schemaError && (
          <p className="sidebar-error">{schemaError}</p>
        )}

        {!loading && !schemaError && !schema && (
          <p className="sidebar-empty">Could not load schema</p>
        )}

        {!loading && schema && Object.keys(schema).length === 0 && (
          <p className="sidebar-empty">No collections / tables found</p>
        )}

        {!loading && schema && Object.entries(schema).map(([collection, fields]) => (
          <div key={collection} className="schema-collection">
            <button
              className="collection-toggle"
              onClick={() => toggle(collection)}
            >
              <span>{collection}</span>
              <span className="field-count">
                {Array.isArray(fields) ? fields.length : 0} fields {expanded[collection] ? '▲' : '▼'}
              </span>
            </button>

            {expanded[collection] && (
              <div className="fields-list">
                {(Array.isArray(fields) ? fields : Object.keys(fields))
                  .sort()
                  .map(field => (
                    <div key={field} className="field-item">
                      <code>{field}</code>
                    </div>
                  ))}
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="sidebar-footer">
        <button className="btn-clear-conv" onClick={onClear}>
          Clear Conversation
        </button>
      </div>
    </div>
  )
}

export default Sidebar
