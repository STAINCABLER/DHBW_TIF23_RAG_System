import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { ChatMessage } from '../../api/types'

const MARKDOWN_PLUGINS = [remarkGfm]

type Props = {
  message: ChatMessage
  className?: string
  hideFiles?: boolean
}

export function MessageBubble({ message, className, hideFiles = false }: Props) {
  const classes = ['message', `message--${message.role}`, className].filter(Boolean).join(' ')
  return (
    <article className={classes}>
      <header className="message__meta">
        <strong className="u-no-select">{message.role === 'user' ? 'You' : 'Assistant'}</strong>
      </header>
      <div className="message__content">
        <ReactMarkdown remarkPlugins={MARKDOWN_PLUGINS}>{message.text}</ReactMarkdown>
      </div>
      {!hideFiles && message.files.length > 0 && (
        <ul className="message__files">
          {message.files.map((file) => (
            <li key={file.fileId}>
              <button type="button" className="link link--subtle">
                {file.fileName}
              </button>
            </li>
          ))}
        </ul>
      )}
    </article>
  )
}
