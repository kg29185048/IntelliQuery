import { useState } from 'react'
import './SignIn.css'

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

const SignIn = ({ onSignIn }) => {
  const [form, setForm] = useState({
    name: '', email: '', password: '',
    dbType: 'mongodb',
    mongoUri: '',
    mongoDbName: '',
    sqlUri: '',
  })
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(false)
  const [globalError, setGlobalError] = useState('')

  const isSql = SQL_TYPES.has(form.dbType)

  const validate = () => {
    const e = {}
    if (!form.name.trim()) e.name = 'Name is required'
    if (!form.email.trim()) e.email = 'Email is required'
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) e.email = 'Enter a valid email'
    if (!form.password) e.password = 'Password is required'
    else if (form.password.length < 6) e.password = 'At least 6 characters'

    if (!isSql) {
      if (!form.mongoUri.trim()) e.mongoUri = 'MongoDB URI is required'
      else if (!form.mongoUri.startsWith('mongodb')) e.mongoUri = 'Must start with mongodb:// or mongodb+srv://'
      if (!form.mongoDbName.trim()) e.mongoDbName = 'Database name is required'
    } else {
      if (!form.sqlUri.trim()) e.sqlUri = 'Connection URI is required'
    }
    return e
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const errs = validate()
    if (Object.keys(errs).length) { setErrors(errs); return }
    setErrors({})
    setGlobalError('')
    setLoading(true)
    try {
      const res = await fetch('/api/health')
      if (!res.ok) throw new Error()
      onSignIn({
        name:        form.name,
        email:       form.email,
        dbType:      form.dbType,
        mongoUri:    isSql ? '' : form.mongoUri,
        mongoDbName: isSql ? '' : form.mongoDbName,
        sqlUri:      isSql ? form.sqlUri : '',
      })
    } catch {
      setGlobalError('Could not reach backend. Make sure it is running.')
    } finally {
      setLoading(false)
    }
  }

  const set = (field) => (e) => {
    setForm(prev => ({ ...prev, [field]: e.target.value }))
    setErrors(prev => ({ ...prev, [field]: '' }))
  }

  const setDbType = (val) => setForm(prev => ({ ...prev, dbType: val }))

  return (
    <div className="signin-shell">
      <div className="signin-card">
        <div className="signin-header">
          <div className="signin-logo">IntelliQuery</div>
          <div className="signin-tagline">Natural Language → Any Database</div>
        </div>

        <form className="signin-form" onSubmit={handleSubmit} noValidate>

          {/* Name */}
          <div className="signin-field">
            <label className="signin-label">Name</label>
            <input
              className={`signin-input ${errors.name ? 'signin-input--error' : ''}`}
              type="text" placeholder="Your name" value={form.name}
              onChange={set('name')} autoComplete="name"
            />
            {errors.name && <span className="signin-error">{errors.name}</span>}
          </div>

          {/* Email */}
          <div className="signin-field">
            <label className="signin-label">Email</label>
            <input
              className={`signin-input ${errors.email ? 'signin-input--error' : ''}`}
              type="email" placeholder="you@example.com" value={form.email}
              onChange={set('email')} autoComplete="email"
            />
            {errors.email && <span className="signin-error">{errors.email}</span>}
          </div>

          {/* Password */}
          <div className="signin-field">
            <label className="signin-label">Password</label>
            <input
              className={`signin-input ${errors.password ? 'signin-input--error' : ''}`}
              type="password" placeholder="••••••••" value={form.password}
              onChange={set('password')} autoComplete="current-password"
            />
            {errors.password && <span className="signin-error">{errors.password}</span>}
          </div>

          {/* DB Type selector */}
          <div className="signin-field">
            <label className="signin-label">Database Type</label>
            <div className="signin-db-tabs">
              {DB_TYPES.map(db => (
                <button
                  key={db.value}
                  type="button"
                  className={`signin-db-tab ${form.dbType === db.value ? 'signin-db-tab--active' : ''}`}
                  onClick={() => setDbType(db.value)}
                >
                  {db.label}
                </button>
              ))}
            </div>
          </div>

          {/* MongoDB URI + DB name */}
          {!isSql && (
            <>
              <div className="signin-field">
                <label className="signin-label">MongoDB URI</label>
                <input
                  className={`signin-input signin-input--mono ${errors.mongoUri ? 'signin-input--error' : ''}`}
                  type="text"
                  placeholder="mongodb+srv://user:pass@cluster.mongodb.net"
                  value={form.mongoUri} onChange={set('mongoUri')}
                  autoComplete="off" spellCheck={false}
                />
                {errors.mongoUri && <span className="signin-error">{errors.mongoUri}</span>}
                <span className="signin-hint">Connection string is used locally — never stored.</span>
              </div>
              <div className="signin-field">
                <label className="signin-label">Database Name</label>
                <input
                  className={`signin-input ${errors.mongoDbName ? 'signin-input--error' : ''}`}
                  type="text"
                  placeholder="e.g. sample_mflix"
                  value={form.mongoDbName} onChange={set('mongoDbName')}
                  autoComplete="off" spellCheck={false}
                />
                {errors.mongoDbName && <span className="signin-error">{errors.mongoDbName}</span>}
              </div>
            </>
          )}

          {/* SQL URI */}
          {isSql && (
            <div className="signin-field">
              <label className="signin-label">Connection URI</label>
              <input
                className={`signin-input signin-input--mono ${errors.sqlUri ? 'signin-input--error' : ''}`}
                type="text"
                placeholder={SQL_PLACEHOLDERS[form.dbType]}
                value={form.sqlUri} onChange={set('sqlUri')}
                autoComplete="off" spellCheck={false}
              />
              {errors.sqlUri && <span className="signin-error">{errors.sqlUri}</span>}
              <span className="signin-hint">SQLAlchemy connection string — used locally, never stored.</span>
            </div>
          )}

          {globalError && <div className="signin-global-error">{globalError}</div>}

          <button className="signin-btn" type="submit" disabled={loading}>
            {loading ? <span className="signin-spinner" /> : 'Continue'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default SignIn
