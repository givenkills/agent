import { useState } from 'react'

export default function MessageInput({ onSend, disabled }) {
  const [text, setText] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    const trimmed = text.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setText('')
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <form className="input-area" onSubmit={handleSubmit}>
      <input
        className="chat-input"
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="输入你想要的小游戏，比如：射击游戏"
        disabled={disabled}
      />
      <button className="send-btn" type="submit" disabled={disabled || !text.trim()}>
        发送
      </button>
    </form>
  )
}
