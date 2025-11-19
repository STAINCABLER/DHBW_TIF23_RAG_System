import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { apiClient } from '../api/client'
import type { ChatSummary, DocumentMeta } from '../api/types'
import { formatBytes, formatDate } from '../utils/formatters'
import { useAuth } from '../auth/useAuth'

export function DashboardPage() {
  const { user } = useAuth()
  const [documents, setDocuments] = useState<DocumentMeta[]>([])
  const [chatSummaries, setChatSummaries] = useState<ChatSummary[]>([])

  useEffect(() => {
    if (!user) return
    let cancelled = false

    const load = async () => {
      try {
        const [docs, chats] = await Promise.all([apiClient.getDocuments(), apiClient.getChatSummaries()])
        if (!cancelled) {
          setDocuments(docs)
          setChatSummaries(chats)
        }
      } catch (error) {
        console.error(error)
      }
    }

    load()
    return () => {
      cancelled = true
    }
  }, [user])

  if (!user) return null

  return (
    <div className="page page--dashboard">
      <div className="page__header">
        <div>
          <p className="u-no-select page__eyebrow">Realtime Overview</p>
          <h1 className="page__title u-no-select">Retrieval Control Center</h1>
        </div>
      </div>

      <section className="dashboard__split">
        <article className="card">
          <header className="card__header">
            <p className="card__eyebrow u-no-select">Recent Documents</p>
            <Link to="/docs" className="btn btn--ghost">
              View all
            </Link>
          </header>
          <ul className="list list--documents">
            {documents.slice(0, 4).map((doc) => (
              <li key={doc.fileId}>
                <div>
                  <p className="u-no-select">{doc.fileName}</p>
                  <small>{doc.tags.join(', ') || 'untagged'}</small>
                </div>
                <span>{formatBytes(doc.sizeBytes)}</span>
              </li>
            ))}
          </ul>
        </article>

        <article className="card">
          <header className="card__header">
            <p className="card__eyebrow u-no-select">Latest Chats</p>
            <Link to="/history" className="btn btn--ghost">
              Open History
            </Link>
          </header>
          <ul className="list list--activity">
            {chatSummaries.slice(0, 5).map((chat) => (
              <li key={chat.chatId} className="chat-activity__item">
                <div className="chat-activity__details">
                  <p className="u-no-select">{chat.chatTitle}</p>
                  <small>Created {formatDate(chat.createdAt)}</small>
                </div>
                <Link
                  to={`/chat/${chat.chatId}`}
                  className="btn btn--ghost btn--compact chat-activity__open-btn"
                  aria-label={`Open chat ${chat.chatTitle}`}
                >
                  Open chat
                </Link>
              </li>
            ))}
            {chatSummaries.length === 0 && <li>No chats available</li>}
          </ul>
        </article>
      </section>
    </div>
  )
}
