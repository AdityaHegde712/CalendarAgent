import React from 'react';
import ChatWindow from './components/ChatWindow';

const styles = `
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg:        #0e0e10;
    --surface:   #16161a;
    --border:    #2a2a32;
    --accent:    #c8f04a;
    --accent-dim:#8aab24;
    --text:      #e8e8ec;
    --text-muted:#6b6b7a;
    --user-bg:   #1e1e26;
    --agent-bg:  #131318;
    --font-display: 'DM Serif Display', Georgia, serif;
    --font-mono:    'DM Mono', 'Courier New', monospace;
    --radius: 12px;
  }

  html, body, #root {
    height: 100%;
    background: var(--bg);
    color: var(--text);
    font-family: var(--font-mono);
    font-size: 14px;
    line-height: 1.6;
    -webkit-font-smoothing: antialiased;
  }

  /* Scrollbar */
  ::-webkit-scrollbar { width: 5px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }

  /* Markdown inside agent messages */
  .md-content p { margin-bottom: 0.6em; }
  .md-content p:last-child { margin-bottom: 0; }
  .md-content ul, .md-content ol { padding-left: 1.4em; margin-bottom: 0.6em; }
  .md-content li { margin-bottom: 0.2em; }
  .md-content strong { color: var(--accent); font-weight: 500; }
  .md-content code {
    background: #1e1e28;
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 1px 5px;
    font-size: 0.88em;
  }
  .md-content pre {
    background: #1a1a22;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px;
    overflow-x: auto;
    margin: 0.6em 0;
  }
  .md-content pre code { background: none; border: none; padding: 0; }
  .md-content h1,.md-content h2,.md-content h3 {
    font-family: var(--font-display);
    color: var(--text);
    margin-bottom: 0.4em;
    margin-top: 0.8em;
    font-weight: 400;
  }

  @keyframes fadeSlideUp {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  @keyframes pulse {
    0%, 100% { opacity: 0.3; }
    50%       { opacity: 1; }
  }

  @keyframes blink {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0; }
  }
`;

export default function App() {
  return (
    <>
      <style>{styles}</style>
      <ChatWindow />
    </>
  );
}
