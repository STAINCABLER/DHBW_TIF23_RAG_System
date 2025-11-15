import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { apiClient } from '../api/client'
import type { ChatDetail, ChatMessage } from '../api/types'
import { ChatExchange } from '../components/chat/ChatExchange'
import { Modal } from '../components/Modal'
import { UI_EVENTS, subscribeToUiEvent } from '../utils/events'

function createWelcomeMessage(title: string) {
  return {
    messageId: crypto.randomUUID(),
    role: 'assistant' as const,
    text: `Willkommen im Chat "${title}". Ich bin bereit, Fragen zum Wissensspeicher zu beantworten.`,
    files: [],
  }
}

export function ChatPage() {
  const { chatId } = useParams<{ chatId?: string }>()
  const navigate = useNavigate()
  const [chats, setChats] = useState<ChatDetail[]>([])
  const [message, setMessage] = useState('')
  const [showDocModal, setShowDocModal] = useState(false)
  const [showNewChatModal, setShowNewChatModal] = useState(false)
  const [newChatTitle, setNewChatTitle] = useState('')

  useEffect(() => {
    apiClient
      .getChats()
      .then((data) => {
        setChats(data)
      })
      .catch(console.error)
  }, [])

  useEffect(() => subscribeToUiEvent(UI_EVENTS.NEW_CHAT, () => setShowNewChatModal(true)), [])

  const activeChat = useMemo(() => {
    if (!chatId) return undefined
    return chats.find((chat) => chat.chatId === chatId)
  }, [chatId, chats])

  const handleSend = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!activeChat || message.trim().length === 0) return

    const newMessage = {
      messageId: crypto.randomUUID(),
      role: 'user' as const,
      text: message,
      files: [],
    }

    setChats((current) =>
      current.map((chat) => (chat.chatId === activeChat.chatId ? { ...chat, messages: [...chat.messages, newMessage] } : chat)),
    )
    setMessage('')
  }

  const handleCreateChat = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const title = newChatTitle.trim() || `Conversation ${chats.length + 1}`
    const newChatId = crypto.randomUUID()
    const welcomeMessage = createWelcomeMessage(title)
    const newChat: ChatDetail = {
      chatId: newChatId,
      chatTitle: title,
      messages: [welcomeMessage],
    }
    setChats((current) => [newChat, ...current])
    setShowNewChatModal(false)
    setNewChatTitle('')
    navigate(`/chat/${newChatId}`)
  }

  const handleDocumentUpload = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setShowDocModal(false)
  }

  const goToHistory = () => navigate('/history')

  const handleResetComposer = () => setMessage('')

  const handleExportChat = () => {
    if (!activeChat) return
    console.info('Export chat requested:', activeChat.chatId)
  }

  const exchanges = useMemo(() => (activeChat ? buildExchanges(activeChat.messages) : []), [activeChat])

  return (
    <div className="page page--chat">
      <header className="chat-page__header">
        <div>
          <p className="page__eyebrow u-no-select">Conversational Workspace</p>
          <h1 className="page__title u-no-select">{activeChat ? activeChat.chatTitle : 'Select or start a chat'}</h1>
        </div>
        <div className="chat-page__header-actions">
          <button type="button" className="btn btn--secondary" onClick={() => setShowNewChatModal(true)}>
            Start new chat
          </button>
          <button
            type="button"
            className="btn btn--ghost"
            onClick={handleResetComposer}
            disabled={message.trim().length === 0}
          >
            Reset input
          </button>
          <button
            type="button"
            className="btn btn--ghost"
            onClick={handleExportChat}
            disabled={!activeChat}
          >
            Export chat
          </button>
          <button type="button" className="btn btn--ghost" onClick={goToHistory}>
            Open history
          </button>
        </div>
      </header>

      {activeChat ? (
        <section className="chat-window" aria-live="polite">
          <div className="chat-window__messages">
            {exchanges.map((exchange, index) => {
              const key = exchange.user?.messageId ?? exchange.assistant?.messageId ?? `exchange-${index}`
              return (
              <ChatExchange
                  key={key}
                  assistant={exchange.assistant}
                  user={exchange.user}
                />
              )
            })}
          </div>

          <form className="chat-composer" onSubmit={handleSend}>
            <textarea
              rows={3}
              placeholder="Ask something..."
              value={message}
              onChange={(event) => setMessage(event.target.value)}
            />
            <div className="chat-composer__actions">
              <button
                type="button"
                className="btn btn--secondary"
                onClick={() => setShowDocModal(true)}
              >
                Upload documents
              </button>
              <div className="chat-composer__actions-group">
                <button type="submit" className="btn btn--primary">
                  Send
                </button>
              </div>
            </div>
          </form>
        </section>
      ) : (
        <section className="chat-window__empty">
          <p className="u-no-select">Öffne einen Chat über die History-Seite oder starte hier ein neues Gespräch.</p>
          <button type="button" className="btn btn--primary" onClick={() => setShowNewChatModal(true)}>
            Neues Gespräch starten
          </button>
        </section>
      )}

      <Modal open={showDocModal} onClose={() => setShowDocModal(false)} title="Upload documents to this chat">
        <form className="form-grid" onSubmit={handleDocumentUpload}>
          <label>
            <span className="u-no-select">Select files</span>
            <input type="file" multiple required />
          </label>
          <label>
            <span className="u-no-select">Notes for the assistant</span>
            <textarea rows={3} placeholder="Warum bekommt der Assistent diese Dateien?" />
          </label>
          <button type="submit" className="btn btn--primary">
            Upload to chat
          </button>
        </form>
      </Modal>

      <Modal open={showNewChatModal} onClose={() => setShowNewChatModal(false)} title="Start new chat">
        <form className="form-grid" onSubmit={handleCreateChat}>
          <label>
            <span className="u-no-select">Chat title</span>
            <input
              type="text"
              placeholder="Incident briefing"
              value={newChatTitle}
              onChange={(event) => setNewChatTitle(event.target.value)}
            />
          </label>
          <button type="submit" className="btn btn--primary">
            Create chat
          </button>
        </form>
      </Modal>
    </div>
  )
}

type Exchange = {
  assistant?: ChatMessage
  user?: ChatMessage
}

function buildExchanges(messages: ChatMessage[]): Exchange[] {
  const result: Exchange[] = []
  let current: Exchange | null = null

  messages.forEach((message) => {
    if (message.role === 'assistant') {
      if (current) {
        result.push(current)
      }
      current = { assistant: message }
      return
    }

    if (!current) {
      result.push({ user: message })
      return
    }

    if (!current.user) {
      current.user = message
      result.push(current)
      current = null
      return
    }

    result.push(current)
    current = { user: message }
  })

  if (current) {
    result.push(current)
  }

  return result
}
