import { useEffect, useRef } from 'react'
import Navbar from '../components/Navbar'
import ChatMessage from '../components/ChatMessage'
import MessageInput from '../components/MessageInput'
import { useChat } from '../context/ChatContext'

export default function ChatPage() {
  const { messages, loading, error, loadHistory, handleSend, handleClear } = useChat()
  const bottomRef = useRef(null)

  useEffect(() => {
    loadHistory()
  }, [loadHistory])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div className="chat-page">
      <Navbar />
      <div className="chat-container">
        <div className="message-box">
          {messages.length === 0 && (
            <div className="empty-chat">
              <p>输入游戏描述开始生成</p>
              <p className="hint">例如：贪吃蛇、射击游戏、2048...</p>
            </div>
          )}
          {messages.map((msg, i) => (
            <ChatMessage key={msg.id} message={msg} index={i} />
          ))}
          {error && <div className="chat-error">{error}</div>}
          <div ref={bottomRef} />
        </div>
        <MessageInput onSend={handleSend} disabled={loading} />
        <div className="chat-actions">
          <button className="clear-btn" onClick={handleClear} disabled={loading}>
            清空对话
          </button>
        </div>
      </div>
    </div>
  )
}
