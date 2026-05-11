export default function ChatMessage({ message, index }) {
  if (message.type === 'game') {
    const gameId = `game-${index}`

    const toggleFullscreen = () => {
      const container = document.getElementById(gameId)
      const iframe = container?.querySelector('iframe')
      if (!document.fullscreenElement) {
        iframe?.requestFullscreen().catch(() => {})
      } else {
        document.exitFullscreen().catch(() => {})
      }
    }

    return (
      <div className="message ai">
        <div className="game-container" id={gameId}>
          <div className="game-toolbar">
            <span>游戏预览</span>
            <button className="game-fullscreen-btn" onClick={toggleFullscreen}>全屏</button>
          </div>
          <iframe
            srcDoc={message.html}
            width="100%"
            height="420"
            frameBorder="0"
            className="game-iframe"
            onLoad={(e) => {
              try {
                const doc = e.target.contentDocument
                if (doc && doc.body) {
                  e.target.style.height = Math.min(doc.body.scrollHeight + 20, 800) + 'px'
                }
              } catch {}
            }}
          />
        </div>
      </div>
    )
  }

  return (
    <div className={`message ${message.role}`}>
      {message.content}
    </div>
  )
}
