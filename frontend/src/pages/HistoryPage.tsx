import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { apiClient } from '../api/client'
import type { ChatSummary } from '../api/types'
import { formatDate } from '../utils/formatters'

export function HistoryPage() {
  const [chats, setChats] = useState<ChatSummary[]>([])
  const [query, setQuery] = useState('')

  useEffect(() => {
    apiClient.getChatSummaries().then(setChats).catch(console.error)
  }, [])

  const filtered = useMemo(() => {
    const lower = query.toLowerCase()
    return chats.filter((chat) => chat.chatTitle.toLowerCase().includes(lower))
  }, [query, chats])

  return (
    <div className="page page--history">
      <header className="page__header">
        <div>
          <p className="u-no-select page__eyebrow">Audit Trail</p>
          <h1 className="page__title u-no-select">Chat History</h1>
        </div>
        <input
          type="search"
          placeholder="Filter chats"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
      </header>

      <div className="table-wrapper">
        <table className="history-table">
          <thead>
            <tr className="u-no-select">
              <th>Title</th>
              <th>Created</th>
              <th>Chat ID</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((chat) => (
              <tr key={chat.chatId}>
                <td>{chat.chatTitle}</td>
                <td>{formatDate(chat.createdAt)}</td>
                <td className="u-no-select">{chat.chatId}</td>
                <td className="history-table__action">
                  <Link
                    to={`/chat/${chat.chatId}`}
                    className="btn btn--ghost btn--compact history-table__open-btn"
                    aria-label={`Open chat ${chat.chatTitle}`}
                  >
                    Open chat
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
