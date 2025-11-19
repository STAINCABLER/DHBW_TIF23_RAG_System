export type SessionToken = {
  tokenId: string
  createdAt: string
  lastUsedAt: string
  device: string
  location: string
}

export type Account = {
  accountId: string
  email: string
  displayName: string
  createdAt: string
  displayNameUpdatedAt?: string
  emailUpdatedAt?: string
  passwordUpdatedAt?: string
}

export type DocumentMeta = {
  fileId: string
  fileName: string
  mimeType: string
  sizeBytes: number
  uploadedAt: string
  tags: string[]
  linkedChats: string[]
}

export type ChatSummary = {
  chatId: string
  chatTitle: string
  createdAt: string
}

export type MessageFile = {
  fileId: string
  fileName: string
}

export type ChatMessage = {
  messageId: string
  role: 'user' | 'assistant'
  text: string
  files: MessageFile[]
}

export type ChatDetail = {
  chatId: string
  chatTitle: string
  messages: ChatMessage[]
}

export type SystemStatus = {
  name: string
  status: 'online' | 'degraded' | 'offline'
  description: string
  updatedAt: string
}
