import { useState } from 'react'
import './SignIn.css'

const SignIn = ({ onSignIn }) => {
  const [isLogin, setIsLogin] = useState(true)
  const [form, setForm] = useState({ name: '', email: '', password: '' })
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(false)
  const [globalError, setGlobalError] = useState('')

  const validate = () => {
    const e = {}
    if (!isLogin && !form.name.trim()) e.name = 'Name is required'
    if (!form.email.trim()) e.email = 'Email is required'
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) e.email = 'Enter a valid email'
    if (!form.password) e.password = 'Password is required'
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
      const endpoint = isLogin ? '/api/auth/login' : '/api/auth/signup'
      const payload = isLogin 
        ? { email: form.email, password: form.password }
        : { name: form.name, email: form.email, password: form.password }

      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Authentication failed')

      // the backend returns { token: "...", user: { id, name, email } }
      onSignIn(data)
    } catch (err) {
      setGlobalError(err.message || 'Could not reach backend. Make sure it is running.')
    } finally {
      setLoading(false)
    }
  }

  const set = (field) => (e) => {
    setForm(prev => ({ ...prev, [field]: e.target.value }))
    setErrors(prev => ({ ...prev, [field]: '' }))
  }

  return (
    <div className="signin-shell">
      <div className="signin-card">
        <div className="signin-header">
          <div className="signin-logo">IntelliQuery</div>
          <div className="signin-tagline">Natural Language → Any Database</div>
        </div>

        <div className="signin-tabs">
          <button 
            type="button" 
            className={`signin-tab ${isLogin ? 'active' : ''}`}
            onClick={() => { setIsLogin(true); setErrors({}); setGlobalError(''); }}
          >
            Login
          </button>
          <button 
            type="button" 
            className={`signin-tab ${!isLogin ? 'active' : ''}`}
            onClick={() => { setIsLogin(false); setErrors({}); setGlobalError(''); }}
          >
            Sign Up
          </button>
        </div>

        <form className="signin-form" onSubmit={handleSubmit} noValidate>
          {!isLogin && (
            <div className="signin-field">
              <label className="signin-label">Name</label>
              <input
                className={`signin-input ${errors.name ? 'signin-input--error' : ''}`}
                type="text" placeholder="Your name" value={form.name}
                onChange={set('name')} autoComplete="name"
              />
              {errors.name && <span className="signin-error">{errors.name}</span>}
            </div>
          )}

          <div className="signin-field">
            <label className="signin-label">Email</label>
            <input
              className={`signin-input ${errors.email ? 'signin-input--error' : ''}`}
              type="email" placeholder="you@example.com" value={form.email}
              onChange={set('email')} autoComplete="email"
            />
            {errors.email && <span className="signin-error">{errors.email}</span>}
          </div>

          <div className="signin-field">
            <label className="signin-label">Password</label>
            <input
              className={`signin-input ${errors.password ? 'signin-input--error' : ''}`}
              type="password" placeholder="••••••••" value={form.password}
              onChange={set('password')} autoComplete="current-password"
            />
            {errors.password && <span className="signin-error">{errors.password}</span>}
          </div>

          {globalError && <div className="signin-global-error">{globalError}</div>}

          <button className="signin-btn" type="submit" disabled={loading}>
            {loading ? <span className="signin-spinner" /> : (isLogin ? 'Login' : 'Sign Up')}
          </button>
        </form>
      </div>
    </div>
  )
}

export default SignIn
