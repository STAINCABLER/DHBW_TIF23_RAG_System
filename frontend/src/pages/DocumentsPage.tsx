import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { apiClient } from '../api/client'
import type { DocumentMeta } from '../api/types'
import { formatBytes, formatDate } from '../utils/formatters'

export function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentMeta[]>([])

  useEffect(() => {
    apiClient.getDocuments().then(setDocuments).catch(console.error)
  }, [])

  return (
    <div className="page page--documents">
      <header className="page__header">
        <div>
          <p className="page__eyebrow u-no-select">Knowledge Base</p>
          <h1 className="page__title u-no-select">Documents</h1>
        </div>
        <p className="u-no-select">
          Uploads erfolgen ausschließlich innerhalb eines Chats, dieser Screen dient zur Nachverfolgung.
        </p>
      </header>

      <div className="table-wrapper">
        <table>
          <thead>
            <tr className="u-no-select">
              <th>File</th>
              <th>MIME</th>
              <th>Size</th>
              <th>Tags</th>
              <th>Uploaded</th>
              <th>Chats</th>
            </tr>
          </thead>
          <tbody>
            {documents.map((doc) => (
              <tr key={doc.fileId}>
                <td>{doc.fileName}</td>
                <td>{doc.mimeType}</td>
                <td>{formatBytes(doc.sizeBytes)}</td>
                <td>{doc.tags.join(', ') || '—'}</td>
                <td>{formatDate(doc.uploadedAt)}</td>
                <td>
                  {doc.linkedChats.length > 0 ? (
                    <div className="doc-chat-links">
                      {doc.linkedChats.map((chatId) => (
                        <Link key={chatId} to={`/chat/${chatId}`} className="badge badge--link">
                          {chatId}
                        </Link>
                      ))}
                    </div>
                  ) : (
                    '—'
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
