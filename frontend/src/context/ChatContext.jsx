import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { useAuth } from './AuthContext'
import * as api from '../api/client'

const ChatContext = createContext(null)

export function ChatProvider({ children }) {
  const { user } = useAuth()
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [historyLoaded, setHistoryLoaded] = useState(false)

  useEffect(() => {
    setMessages([])
    setLoading(false)
    setError('')
    setHistoryLoaded(false)
  }, [user?.username])

  const loadHistory = useCallback(async () => {
    if (historyLoaded) return
    try {
      const data = await api.getHistory()
      if (data.messages && data.messages.length > 0) {
        const formatted = data.messages.map((m) => {
          if (m.role === 'assistant') {
            const cleaned = m.content
              .replace(/^```html\s*/i, '')
              .replace(/```\s*$/, '')
              .trim()
            if (cleaned && (cleaned.startsWith('<') || cleaned.includes('<'))) {
              return { id: m.id, role: 'ai', content: m.content, html: cleaned, type: 'game' }
            }
          }
          return { id: m.id, role: m.role === 'assistant' ? 'ai' : 'user', content: m.content, type: 'text' }
        })
        setMessages(formatted)
      }
      setHistoryLoaded(true)
    } catch {
      // 未登录等错误由 AuthContext 处理
    }
  }, [historyLoaded])

  const handleSend = useCallback(async (text) => {
    setError('')
    const userMsg = { id: Date.now().toString(), role: 'user', content: text, type: 'text' }
    const aiMsg = { id: (Date.now() + 1).toString(), role: 'ai', content: '正在生成游戏...', type: 'text' }
    setMessages((prev) => [...prev, userMsg, aiMsg])
    setLoading(true)

    let fullContent = ''

    try {
      await api.generateGame(text, (chunk) => {
        fullContent += chunk
        setMessages((prev) =>
          prev.map((m) =>
            m.id === aiMsg.id ? { ...m, content: fullContent, type: 'text' } : m
          )
        )
      })

      const cleanContent = fullContent
        .replace(/^```html\s*/i, '')
        .replace(/```\s*$/, '')
        .trim()

      if (cleanContent) {
        const isGameHTML = cleanContent.startsWith('<') && cleanContent.includes('<html')
        setMessages((prev) =>
          prev.map((m) =>
            m.id === aiMsg.id
              ? { ...m, html: isGameHTML ? cleanContent : '', content: cleanContent, type: isGameHTML ? 'game' : 'text' }
              : m
          )
        )
      }
    } catch (err) {
      setError(err.message)
      setMessages((prev) =>
        prev.map((m) =>
          m.id === aiMsg.id ? { ...m, content: `生成失败: ${err.message}`, type: 'text' } : m
        )
      )
    } finally {
      setLoading(false)
    }
  }, [])

  const handleClear = useCallback(async () => {
    try {
      await api.clearChat()
      setMessages([])
    } catch (err) {
      setError(err.message)
    }
  }, [])

  return (
    <ChatContext.Provider value={{ messages, loading, error, loadHistory, handleSend, handleClear }}>
      {children}
    </ChatContext.Provider>
  )
}

export function useChat() {
  const ctx = useContext(ChatContext)
  if (!ctx) {
    throw new Error('useChat must be used within ChatProvider')
  }
  return ctx
}
