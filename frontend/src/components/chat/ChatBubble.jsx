import React from 'react'

function formatTime(ts) {
  try {
    return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  } catch {
    return ''
  }
}

// Convert simple markdown-ish formatting to React elements
// Handles: **bold**, *italic*, \n line breaks
// Does NOT use dangerouslySetInnerHTML
function parseMessageText(text) {
  if (!text) return null
  // Split by newlines first
  const lines = text.split('\n')
  return lines.map((line, lineIdx) => {
    if (!line) return <br key={lineIdx} />
    // Process inline: **bold** and *italic*
    const parts = []
    const pattern = /(\*\*([^*]+)\*\*|\*([^*]+)\*)/g
    let lastIndex = 0
    let match
    while ((match = pattern.exec(line)) !== null) {
      if (match.index > lastIndex) {
        parts.push(line.slice(lastIndex, match.index))
      }
      if (match[2]) {
        // **bold**
        parts.push(<strong key={match.index} className="font-semibold">{match[2]}</strong>)
      } else if (match[3]) {
        // *italic*
        parts.push(<em key={match.index}>{match[3]}</em>)
      }
      lastIndex = match.index + match[0].length
    }
    if (lastIndex < line.length) {
      parts.push(line.slice(lastIndex))
    }
    return (
      <React.Fragment key={lineIdx}>
        {parts.length > 0 ? parts : line}
        {lineIdx < lines.length - 1 && lines.some(l => l) && <br />}
      </React.Fragment>
    )
  })
}

export function MessageBubble({ role, text, timestamp, isError, onRetry }) {
  const isUser = role === 'user'

  return (
    <div className={`flex items-end gap-2 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {/* Agent avatar */}
      {!isUser && (
        <div className="h-7 w-7 rounded-full bg-gradient-to-br from-brand-500 to-brand-700 text-white flex items-center justify-center font-bold text-xs shadow-sm shrink-0 mb-0.5">
          N
        </div>
      )}

      <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} max-w-[80%] sm:max-w-[70%]`}>
        <div
          className={
            'px-4 py-2.5 text-sm break-words rounded-2xl leading-relaxed ' +
            (isUser
              ? 'bg-brand-500 text-white rounded-br-sm'
              : isError
              ? 'bg-red-50 text-red-800 rounded-bl-sm border border-red-200'
              : 'bg-white text-slate-800 rounded-bl-sm border border-slate-200 shadow-sm')
          }
        >
          {parseMessageText(text)}
        </div>
        <div className="flex items-center gap-2 mt-1 px-1">
          {timestamp && <span className="text-[11px] text-slate-400">{formatTime(timestamp)}</span>}
          {isError && onRetry && (
            <button onClick={onRetry} className="text-[11px] font-medium text-brand-600 hover:underline">
              Retry
            </button>
          )}
        </div>
      </div>

      {/* User avatar placeholder for alignment */}
      {isUser && <div className="w-7 shrink-0" />}
    </div>
  )
}

export function TypingIndicator() {
  return (
    <div className="flex items-end gap-2 justify-start">
      <div className="h-7 w-7 rounded-full bg-gradient-to-br from-brand-500 to-brand-700 text-white flex items-center justify-center font-bold text-xs shadow-sm shrink-0">
        N
      </div>
      <div className="bg-white border border-slate-200 rounded-2xl rounded-bl-sm px-4 py-3 flex gap-1 items-center shadow-sm">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="h-2 w-2 rounded-full bg-slate-300 animate-bounce"
            style={{ animationDelay: `${i * 150}ms` }}
          />
        ))}
      </div>
    </div>
  )
}
