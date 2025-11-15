import type { ChatMessage } from '../../api/types'
import { MessageBubble } from './MessageBubble'

type Props = {
  assistant?: ChatMessage
  user?: ChatMessage
}

export function ChatExchange({ assistant, user }: Props) {
  if (!assistant && !user) return null
  return (
    <div className="chat-exchange">
      {assistant && <MessageBubble message={assistant} className="chat-exchange__assistant" hideFiles />}
      {user && <MessageBubble message={user} className="chat-exchange__user" />}
    </div>
  )
}
