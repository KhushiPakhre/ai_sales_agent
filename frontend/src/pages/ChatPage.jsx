import React, { useEffect, useRef, useState, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import { api, ApiError } from '../api/client.js'
import { MessageBubble, TypingIndicator } from '../components/chat/ChatBubble.jsx'
import ChatInput from '../components/chat/ChatInput.jsx'
import RecommendationCard from '../components/chat/RecommendationCard.jsx'
import BookingConfirmedCard from '../components/chat/BookingConfirmedCard.jsx'
import HandoffCard from '../components/chat/HandoffCard.jsx'

function newSessionId() {
  return `chat:session-${Math.random().toString(36).slice(2, 10)}`
}

function getOrCreateSessionId(leadIdFromRoute) {
  if (leadIdFromRoute) return leadIdFromRoute
  const existing = sessionStorage.getItem('qdesq_lead_id')
  if (existing) return existing
  const id = newSessionId()
  sessionStorage.setItem('qdesq_lead_id', id)
  return id
}

function createFreshSession() {
  const id = newSessionId()
  sessionStorage.setItem('qdesq_lead_id', id)
  return id
}

const SAMPLE_PROMPTS = [
  "I'm looking for a private office for 10 people in Mumbai",
  "What coworking options do you have in Bangalore under \u20b915,000/seat?",
  "I need a meeting room for tomorrow afternoon",
  "Looking for a managed office for 50 people, need to move in next month",
]

export default function ChatPage() {
  const { leadId: leadIdFromRoute } = useParams()
  const [leadId, setLeadId] = useState(() => getOrCreateSessionId(leadIdFromRoute))
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [loadingHistory, setLoadingHistory] = useState(true)
  const scrollRef = useRef(null)

  const scrollToBottom = useCallback(() => {
    requestAnimationFrame(() => {
      scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
    })
  }, [])

  useEffect(() => {
    let cancelled = false
    async function loadHistory() {
      setLoadingHistory(true)
      try {
        const res = await api.getChatHistory(leadId)
        if (cancelled) return
        setMessages(
          res.history.map((h, i) => ({
            id: `h-${i}`,
            role: h.direction === 'inbound' ? 'user' : 'agent',
            text: h.text,
            timestamp: h.timestamp,
          }))
        )
      } catch {
        // New session - no history yet is expected
      } finally {
        if (!cancelled) setLoadingHistory(false)
      }
    }
    loadHistory()
    return () => { cancelled = true }
  }, [leadId])

  useEffect(() => { scrollToBottom() }, [messages, sending, scrollToBottom])

  const send = async (overrideText, opts = {}) => {
    const text = (overrideText ?? input).trim()
    if (!text || sending) return

    if (!opts.isRetry) {
      const userMsg = { id: `u-${Date.now()}`, role: 'user', text, timestamp: new Date().toISOString() }
      setMessages((prev) => [...prev, userMsg])
      setInput('')
    }
    setSending(true)

    try {
      const res = await api.sendMessage({ lead_id: leadId, channel: 'chat', message: text })
      setMessages((prev) => [
        ...prev,
        {
          id: `a-${Date.now()}`,
          role: 'agent',
          text: res.message,
          timestamp: new Date().toISOString(),
          structured: res,
        },
      ])
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'Something went wrong. Please try again.'
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          role: 'agent',
          text: message,
          isError: true,
          retryText: text,
        },
      ])
    } finally {
      setSending(false)
    }
  }

  const handleRetry = (retryText) => {
    setMessages((prev) => prev.filter((m) => m.retryText !== retryText))
    send(retryText, { isRetry: true })
  }

  const handleScheduleTour = (workspace) => {
    send(`I'd like to schedule a tour for ${workspace.name}.`)
  }

  const handleNewConversation = () => {
    const newId = createFreshSession()
    setLeadId(newId)
    setMessages([])
    setInput('')
  }

  const handleSamplePrompt = (prompt) => {
    setInput(prompt)
  }

  return (
    <div
      className="flex flex-col -m-4 md:-m-6 lg:-m-8"
      style={{ height: 'calc(100dvh - 0px)' }}
    >
      {/* Chat header */}
      <div className="flex items-center justify-between px-4 sm:px-6 py-3 border-b border-slate-200 bg-white shrink-0">
        <div className="flex items-center gap-3">
          {/* Nia avatar */}
          <div className="h-9 w-9 rounded-full bg-gradient-to-br from-brand-500 to-brand-700 text-white flex items-center justify-center font-bold text-sm shadow-sm shrink-0">
            N
          </div>
          <div>
            <p className="text-sm font-semibold text-slate-900">Nia</p>
            <p className="text-xs text-slate-500 flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 inline-block" />
              Qdesq Sales+ AI Assistant
            </p>
          </div>
        </div>
        <button
          onClick={handleNewConversation}
          title="Start new conversation"
          className="btn-ghost text-xs gap-1.5 text-slate-500 hover:text-slate-800"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 5v14M5 12h14" />
          </svg>
          New chat
        </button>
      </div>

      {/* Messages area */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 sm:px-6 py-5 space-y-4 bg-slate-50">
        {loadingHistory && (
          <div className="text-center text-xs text-slate-400 py-10">Loading conversation…</div>
        )}

        {!loadingHistory && messages.length === 0 && (
          <div className="max-w-lg mx-auto">
            {/* Nia welcome card */}
            <div className="text-center mb-8">
              <div className="h-16 w-16 rounded-2xl bg-gradient-to-br from-brand-500 to-brand-700 text-white flex items-center justify-center font-bold text-2xl shadow-md mx-auto mb-4">
                N
              </div>
              <h2 className="text-lg font-semibold text-slate-900">Hi, I'm Nia</h2>
              <p className="text-sm text-slate-500 mt-1 max-w-xs mx-auto">
                Qdesq's AI sales assistant. Tell me what kind of workspace you need — I'll qualify your requirement, find the best options, and help you book.
              </p>
            </div>
            {/* Sample prompts */}
            <div className="space-y-2">
              <p className="text-xs font-medium text-slate-400 text-center mb-3">Try asking…</p>
              {SAMPLE_PROMPTS.map((prompt, i) => (
                <button
                  key={i}
                  onClick={() => handleSamplePrompt(prompt)}
                  className="w-full text-left px-4 py-3 rounded-xl border border-slate-200 bg-white hover:border-brand-300 hover:bg-brand-50/50 text-sm text-slate-700 hover:text-brand-800 transition-all duration-150 shadow-sm"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m) => (
          <div key={m.id} className="space-y-2">
            <MessageBubble
              role={m.role}
              text={m.text}
              timestamp={m.timestamp}
              isError={m.isError}
              onRetry={m.retryText ? () => handleRetry(m.retryText) : undefined}
            />
            {m.structured?.recommendations?.length > 0 && (
              <div className="ml-11 flex gap-3 overflow-x-auto pb-2 snap-x">
                {m.structured.recommendations.map((r, idx) => (
                  <RecommendationCard
                    key={idx}
                    recommendation={r}
                    onScheduleTour={handleScheduleTour}
                  />
                ))}
              </div>
            )}
            {m.structured?.action === 'instant_book_confirmed' && m.structured.booking && (
              <div className="ml-11">
                <BookingConfirmedCard
                  booking={m.structured.booking}
                  workspaceHint={m.structured.recommendations?.[0]?.workspace?.name}
                />
              </div>
            )}
            {m.structured?.handoff && (
              <div className="ml-11">
                <HandoffCard handoff={m.structured.handoff} tour={m.structured.tour} />
              </div>
            )}
          </div>
        ))}

        {sending && <TypingIndicator />}
      </div>

      <ChatInput value={input} onChange={setInput} onSend={() => send()} disabled={sending} />
    </div>
  )
}
