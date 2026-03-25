import React, { useState, useRef, useEffect, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import { v4 as uuidv4 } from 'uuid';

const SUGGESTIONS = [
  'Schedule 2 hours for studying before this Friday',
  'Block 90 minutes for project work tomorrow',
  'Find time for a 3-hour deep work session this week',
];

const API_BASE = process.env.REACT_APP_API_URL || '';

async function sendMessage(sessionId, message) {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, message }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

function CalendarIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
      <line x1="16" y1="2" x2="16" y2="6"/>
      <line x1="8" y1="2" x2="8" y2="6"/>
      <line x1="3" y1="10" x2="21" y2="10"/>
    </svg>
  );
}

function SendIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="22" y1="2" x2="11" y2="13"/>
      <polygon points="22 2 15 22 11 13 2 9 22 2"/>
    </svg>
  );
}

function ThinkingDots() {
  return (
    <div style={{ display: 'flex', gap: 5, padding: '4px 0', alignItems: 'center' }}>
      {[0, 1, 2].map(i => (
        <div key={i} style={{
          width: 6, height: 6, borderRadius: '50%',
          background: 'var(--accent)',
          animation: `pulse 1.2s ease-in-out ${i * 0.2}s infinite`,
        }} />
      ))}
    </div>
  );
}

function Message({ msg, index }) {
  const isUser = msg.role === 'user';
  const isError = msg.role === 'error';

  return (
    <div style={{
      animation: `fadeSlideUp 0.25s ease forwards`,
      animationDelay: `${Math.min(index * 0.03, 0.15)}s`,
      opacity: 0,
      display: 'flex',
      flexDirection: 'column',
      alignItems: isUser ? 'flex-end' : 'flex-start',
      marginBottom: 16,
    }}>
      <div style={{
        fontSize: 10,
        letterSpacing: '0.12em',
        textTransform: 'uppercase',
        color: isUser ? 'var(--accent-dim)' : 'var(--text-muted)',
        marginBottom: 5,
        fontWeight: 500,
      }}>
        {isUser ? 'you' : isError ? 'error' : 'agent'}
      </div>
      <div style={{
        maxWidth: '78%',
        padding: '12px 16px',
        borderRadius: isUser ? '14px 14px 4px 14px' : '14px 14px 14px 4px',
        background: isError ? '#2a1010' : isUser ? 'var(--user-bg)' : 'var(--agent-bg)',
        border: `1px solid ${isError ? '#5a2020' : isUser ? '#2e2e3a' : 'var(--border)'}`,
        color: isError ? '#ff6b6b' : 'var(--text)',
        lineHeight: 1.65,
      }}>
        {isUser ? (
          <span style={{ fontFamily: 'var(--font-mono)' }}>{msg.content}</span>
        ) : (
          <div className="md-content">
            <ReactMarkdown>{msg.content}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}

export default function ChatWindow() {
  const [messages, setMessages] = useState([
    {
      role: 'agent',
      content: "Hello! I'm your calendar scheduling assistant.\n\nTell me what you need to schedule — task name, total time needed, and deadline — and I'll find the best available slots for you.\n\nFor example: *\"Schedule 3 hours of work on Essay Draft before Friday\"*",
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(() => uuidv4());
  const bottomRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const submit = useCallback(async (text) => {
    const trimmed = (text || input).trim();
    if (!trimmed || loading) return;

    setMessages(prev => [...prev, { role: 'user', content: trimmed }]);
    setInput('');
    setLoading(true);

    try {
      const data = await sendMessage(sessionId, trimmed);
      setMessages(prev => [...prev, { role: 'agent', content: data.reply }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'error', content: err.message }]);
    } finally {
      setLoading(false);
      setTimeout(() => textareaRef.current?.focus(), 50);
    }
  }, [input, loading, sessionId]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  const clearChat = async () => {
    try { await fetch(`${API_BASE}/chat/${sessionId}`, { method: 'DELETE' }); } catch {}
    setMessages([{
      role: 'agent',
      content: "Session cleared. Start fresh — what would you like to schedule?",
    }]);
  };

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      maxWidth: 760,
      margin: '0 auto',
    }}>

      {/* Header */}
      <div style={{
        padding: '20px 24px 16px',
        borderBottom: '1px solid var(--border)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        background: 'var(--surface)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{
            width: 36, height: 36,
            borderRadius: 10,
            background: 'var(--accent)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: '#0e0e10',
          }}>
            <CalendarIcon />
          </div>
          <div>
            <div style={{
              fontFamily: 'var(--font-display)',
              fontSize: 20,
              letterSpacing: '-0.02em',
              lineHeight: 1.2,
            }}>
              Calendar Agent
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', letterSpacing: '0.08em' }}>
              SMART SCHEDULING
            </div>
          </div>
        </div>
        <button
          onClick={clearChat}
          style={{
            background: 'transparent',
            border: '1px solid var(--border)',
            borderRadius: 8,
            color: 'var(--text-muted)',
            padding: '6px 12px',
            fontSize: 12,
            cursor: 'pointer',
            fontFamily: 'var(--font-mono)',
            letterSpacing: '0.06em',
            transition: 'all 0.15s',
          }}
          onMouseEnter={e => { e.target.style.borderColor = 'var(--accent)'; e.target.style.color = 'var(--accent)'; }}
          onMouseLeave={e => { e.target.style.borderColor = 'var(--border)'; e.target.style.color = 'var(--text-muted)'; }}
        >
          CLEAR
        </button>
      </div>

      {/* Messages */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '24px 24px 8px',
        display: 'flex',
        flexDirection: 'column',
      }}>
        {messages.map((msg, i) => (
          <Message key={i} msg={msg} index={i} />
        ))}
        {loading && (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', marginBottom: 16 }}>
            <div style={{ fontSize: 10, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 5 }}>agent</div>
            <div style={{
              padding: '12px 16px',
              borderRadius: '14px 14px 14px 4px',
              background: 'var(--agent-bg)',
              border: '1px solid var(--border)',
            }}>
              <ThinkingDots />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Suggestions (shown when only initial message exists) */}
      {messages.length === 1 && (
        <div style={{ padding: '0 24px 16px', display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {SUGGESTIONS.map((s, i) => (
            <button
              key={i}
              onClick={() => submit(s)}
              style={{
                background: 'transparent',
                border: '1px solid var(--border)',
                borderRadius: 20,
                color: 'var(--text-muted)',
                padding: '6px 14px',
                fontSize: 12,
                cursor: 'pointer',
                fontFamily: 'var(--font-mono)',
                transition: 'all 0.15s',
                letterSpacing: '0.03em',
              }}
              onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--accent)'; e.currentTarget.style.color = 'var(--text)'; }}
              onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.color = 'var(--text-muted)'; }}
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div style={{
        padding: '12px 24px 20px',
        borderTop: '1px solid var(--border)',
        background: 'var(--surface)',
      }}>
        <div style={{
          display: 'flex',
          gap: 10,
          alignItems: 'flex-end',
          background: 'var(--bg)',
          border: '1px solid var(--border)',
          borderRadius: 14,
          padding: '10px 12px 10px 16px',
          transition: 'border-color 0.15s',
        }}
          onFocusCapture={e => e.currentTarget.style.borderColor = 'var(--accent)'}
          onBlurCapture={e => e.currentTarget.style.borderColor = 'var(--border)'}
        >
          <textarea
            ref={textareaRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Schedule a task... (Shift+Enter for new line)"
            rows={1}
            style={{
              flex: 1,
              background: 'transparent',
              border: 'none',
              outline: 'none',
              color: 'var(--text)',
              fontFamily: 'var(--font-mono)',
              fontSize: 14,
              lineHeight: 1.6,
              resize: 'none',
              minHeight: 24,
              maxHeight: 120,
              overflowY: 'auto',
            }}
            onInput={e => {
              e.target.style.height = 'auto';
              e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
            }}
          />
          <button
            onClick={() => submit()}
            disabled={!input.trim() || loading}
            style={{
              width: 34, height: 34,
              borderRadius: 9,
              border: 'none',
              background: !input.trim() || loading ? 'var(--border)' : 'var(--accent)',
              color: !input.trim() || loading ? 'var(--text-muted)' : '#0e0e10',
              cursor: !input.trim() || loading ? 'not-allowed' : 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              flexShrink: 0,
              transition: 'all 0.15s',
            }}
          >
            <SendIcon />
          </button>
        </div>
        <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 8, letterSpacing: '0.06em', textAlign: 'center' }}>
          ENTER TO SEND · SHIFT+ENTER FOR NEW LINE
        </div>
      </div>
    </div>
  );
}
