import { useState } from 'react'
import { GoogleLogin } from '@react-oauth/google'
import './SignIn.css'

const SignIn = ({ onSignIn }) => {
  // Views: 'login', 'signup', 'verify-signup', 'forgot-password', 'reset-password'
  const [view, setView] = useState('login') 
  const [form, setForm] = useState({ name: '', email: '', password: '', otp: '', newPassword: '' })
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(false)
  const [globalError, setGlobalError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')

  const validate = () => {
    const e = {}
    if ((view === 'signup' || view === 'verify-signup') && !form.name.trim()) e.name = 'Name is required'
    if (!form.email.trim()) e.email = 'Email is required'
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) e.email = 'Enter a valid email'
    
    if (view === 'login' && !form.password) e.password = 'Password is required'
    if (view === 'signup' && !form.password) e.password = 'Password is required'
    if (view === 'reset-password' && !form.newPassword) e.newPassword = 'New password is required'
    
    if ((view === 'verify-signup' || view === 'reset-password') && !form.otp) e.otp = 'OTP is required'
    
    return e
  }

  const handleSendSignupOtp = async () => {
    try {
      const res = await fetch('/api/auth/send-signup-otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: form.name, email: form.email, password: form.password })
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Failed to send OTP')
      setView('verify-signup')
      setSuccessMessage('OTP sent to your email!')
    } catch (err) {
      setGlobalError(err.message)
    }
  }

  const handleSendResetOtp = async () => {
    try {
      const res = await fetch('/api/auth/forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: form.email })
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Failed to send OTP')
      setView('reset-password')
      setSuccessMessage(data.message || 'OTP sent to your email!')
    } catch (err) {
      setGlobalError(err.message)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const errs = validate()
    if (Object.keys(errs).length) { setErrors(errs); return }
    setErrors({})
    setGlobalError('')
    setSuccessMessage('')
    setLoading(true)

    try {
      if (view === 'signup') {
        await handleSendSignupOtp()
      } 
      else if (view === 'forgot-password') {
        await handleSendResetOtp()
      }
      else if (view === 'verify-signup') {
        const res = await fetch('/api/auth/signup', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: form.name, email: form.email, password: form.password, otp: form.otp })
        })
        const data = await res.json()
        if (!res.ok) throw new Error(data.detail || 'Verification failed')
        onSignIn(data)
      }
      else if (view === 'reset-password') {
        const res = await fetch('/api/auth/reset-password', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: form.email, otp: form.otp, new_password: form.newPassword })
        })
        const data = await res.json()
        if (!res.ok) throw new Error(data.detail || 'Password reset failed')
        setView('login')
        setForm(prev => ({ ...prev, password: '', newPassword: '', otp: '' }))
        setSuccessMessage('Password reset successfully. Please login.')
      }
      else if (view === 'login') {
        const res = await fetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: form.email, password: form.password })
        })
        const data = await res.json()
        if (!res.ok) throw new Error(data.detail || 'Authentication failed')
        onSignIn(data)
      }
    } catch (err) {
      setGlobalError(err.message || 'Could not reach backend.')
    } finally {
      setLoading(false)
    }
  }

  const handleResendOtp = async () => {
    setGlobalError('')
    setSuccessMessage('')
    setLoading(true)
    try {
      if (view === 'verify-signup') {
        await handleSendSignupOtp()
      } else if (view === 'reset-password') {
        await handleSendResetOtp()
      }
    } finally {
      setLoading(false)
    }
  }

  const set = (field) => (e) => {
    setForm(prev => ({ ...prev, [field]: e.target.value }))
    setErrors(prev => ({ ...prev, [field]: '' }))
  }

  const switchView = (newView) => {
    setView(newView)
    setErrors({})
    setGlobalError('')
    setSuccessMessage('')
  }

  const handleGoogleSuccess = async (credentialResponse) => {
    setGlobalError('')
    setLoading(true)
    try {
      const res = await fetch('/api/auth/google', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: credentialResponse.credential })
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Google Authentication failed')
      onSignIn(data)
    } catch (err) {
      setGlobalError(err.message || 'Could not reach backend.')
    } finally {
      setLoading(false)
    }
  }

  const handleGoogleError = () => {
    setGlobalError('Google Sign-In was unsuccessful. Try again later.')
  }

  return (
    <div className="signin-shell">
      <div className="signin-card">
        <div className="signin-header">
          <div className="signin-logo">IntelliQuery</div>
          <div className="signin-tagline">Natural Language → Any Database</div>
        </div>

        {(view === 'login' || view === 'signup') && (
          <div className="signin-tabs">
            <button 
              type="button" 
              className={`signin-tab ${view === 'login' ? 'active' : ''}`}
              onClick={() => switchView('login')}
            >
              Login
            </button>
            <button 
              type="button" 
              className={`signin-tab ${view === 'signup' ? 'active' : ''}`}
              onClick={() => switchView('signup')}
            >
              Sign Up
            </button>
          </div>
        )}

        {(view === 'forgot-password' || view === 'reset-password' || view === 'verify-signup') && (
          <div className="signin-back" onClick={() => switchView(view === 'verify-signup' ? 'signup' : 'login')}>
            ← Back
          </div>
        )}

        <form className="signin-form" onSubmit={handleSubmit} noValidate>
          
          {/* Header text for OTP flows */}
          {view === 'verify-signup' && <h3 className="signin-flow-title">Verify Your Email</h3>}
          {view === 'forgot-password' && <h3 className="signin-flow-title">Forgot Password</h3>}
          {view === 'reset-password' && <h3 className="signin-flow-title">Reset Password</h3>}

          {/* Name field */}
          {(view === 'signup' || view === 'verify-signup') && (
            <div className="signin-field">
              <label className="signin-label">Name</label>
              <input
                className={`signin-input ${errors.name ? 'signin-input--error' : ''}`}
                type="text" placeholder="Your name" value={form.name}
                onChange={set('name')} autoComplete="name" disabled={view === 'verify-signup'}
              />
              {errors.name && <span className="signin-error">{errors.name}</span>}
            </div>
          )}

          {/* Email field */}
          {(view === 'login' || view === 'signup' || view === 'forgot-password' || view === 'reset-password' || view === 'verify-signup') && (
            <div className="signin-field">
              <label className="signin-label">Email</label>
              <input
                className={`signin-input ${errors.email ? 'signin-input--error' : ''}`}
                type="email" placeholder="you@example.com" value={form.email}
                onChange={set('email')} autoComplete="email" disabled={view === 'verify-signup' || view === 'reset-password'}
              />
              {errors.email && <span className="signin-error">{errors.email}</span>}
            </div>
          )}

          {/* Password field */}
          {(view === 'login' || view === 'signup') && (
            <div className="signin-field">
              <label className="signin-label">Password</label>
              <input
                className={`signin-input ${errors.password ? 'signin-input--error' : ''}`}
                type="password" placeholder="••••••••" value={form.password}
                onChange={set('password')} autoComplete={view === 'login' ? 'current-password' : 'new-password'}
              />
              {errors.password && <span className="signin-error">{errors.password}</span>}
              {view === 'login' && (
                <div className="signin-forgot-link" onClick={() => switchView('forgot-password')}>
                  Forgot Password?
                </div>
              )}
            </div>
          )}

          {/* OTP field */}
          {(view === 'verify-signup' || view === 'reset-password') && (
            <div className="signin-field">
              <label className="signin-label">6-Digit OTP</label>
              <input
                className={`signin-input signin-input-otp ${errors.otp ? 'signin-input--error' : ''}`}
                type="text" placeholder="123456" value={form.otp} maxLength={6}
                onChange={set('otp')} autoComplete="off"
              />
              {errors.otp && <span className="signin-error">{errors.otp}</span>}
            </div>
          )}

          {/* New Password field */}
          {view === 'reset-password' && (
            <div className="signin-field">
              <label className="signin-label">New Password</label>
              <input
                className={`signin-input ${errors.newPassword ? 'signin-input--error' : ''}`}
                type="password" placeholder="••••••••" value={form.newPassword}
                onChange={set('newPassword')} autoComplete="new-password"
              />
              {errors.newPassword && <span className="signin-error">{errors.newPassword}</span>}
            </div>
          )}

          {globalError && <div className="signin-global-error">{globalError}</div>}
          {successMessage && <div className="signin-success-message">{successMessage}</div>}

          <button className="signin-btn" type="submit" disabled={loading}>
            {loading ? <span className="signin-spinner" /> : (
              view === 'login' ? 'Login' :
              view === 'signup' ? 'Create Account' :
              view === 'verify-signup' ? 'Verify & Register' :
              view === 'forgot-password' ? 'Send OTP' :
              'Reset Password'
            )}
          </button>

          {(view === 'verify-signup' || view === 'reset-password') && (
            <div className="signin-resend">
              Didn't receive the email?{' '}
              <button type="button" className="signin-resend-btn" onClick={handleResendOtp} disabled={loading}>
                Resend OTP
              </button>
            </div>
          )}

        </form>

        {(view === 'login' || view === 'signup') && (
          <div style={{ marginTop: '20px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <div style={{ width: '100%', borderBottom: '1px solid var(--border)', margin: '10px 0', position: 'relative' }}>
              <span style={{ position: 'absolute', top: '-10px', left: '50%', transform: 'translateX(-50%)', background: 'var(--surface)', padding: '0 10px', fontSize: '12px', color: 'var(--text-3)' }}>
                OR
              </span>
            </div>
            <div style={{ marginTop: '15px' }}>
              <GoogleLogin
                onSuccess={handleGoogleSuccess}
                onError={handleGoogleError}
                useOneTap
                theme="filled_black"
                shape="rectangular"
              />
            </div>
          </div>
        )}

      </div>
    </div>
  )
}

export default SignIn
