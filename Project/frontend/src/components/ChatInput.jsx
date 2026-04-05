import { useState, useRef } from 'react'
import './ChatInput.css'

const ChatInput = ({ onSend, loading }) => {
  const [value, setValue] = useState('')
  const textareaRef = useRef(null)

  const handleSubmit = () => {
    if (value.trim() && !loading) {
      onSend(value.trim())
      setValue('')
      textareaRef.current?.focus()
    }
  }

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="chat-input-bar">
      <div className="chat-input-inner">
        <textarea
          ref={textareaRef}
          className="chat-textarea"
          value={value}
          onChange={e => setValue(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Ask your question (e.g. Show me sci-fi movies after 2010)…"
          rows={1}
          disabled={loading}
        />
        <button
          className="chat-send-btn"
          onClick={handleSubmit}
          disabled={loading || !value.trim()}
          title="Send (Enter)"
        >
          {loading
            ? <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="6" stroke="currentColor" strokeWidth="2" strokeDasharray="28" strokeDashoffset="10" style={{animation:'spin .7s linear infinite',transformOrigin:'center'}} /></svg>
            : <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M2 8h12M10 4l4 4-4 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
          }
        </button>
      </div>
      <div className="chat-input-hint">Press Enter to send · Shift+Enter for new line</div>
    </div>
  )
}

export default ChatInput
