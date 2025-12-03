import type {
  Account,
  ChatMessage,
  ChatDetail,
  ChatSummary,
  DocumentMeta,
  SessionToken,
  SystemStatus,
} from './types'
import {
  mockAccount,
  mockChatSummaries,
  mockChats,
  mockDocuments,
  mockSessions,
  mockSystemStatus,
} from '../data/mockData'
import { appConfig } from '../config/appConfig'

type RequestOptions = RequestInit & { path: string }
type LoginResult = {
  status: number
  ok: boolean
  message?: string
}

type BackendAccountPayload = {
  accountId?: string
  id?: number | string
  account_id?: number | string
  email?: string
  username?: string
  displayName?: string
  created_at?: string
  createdAt?: string
  displayNameUpdatedAt?: string
  emailUpdatedAt?: string
  passwordUpdatedAt?: string
  last_login?: string
  lastLogin?: string
  profileType?: string
  profile_type?: string
}

type BackendConversationSummary = {
  conversation_id?: number | string
  chat_id?: number | string
  chatId?: number | string
  title?: string
  created_at?: string
  createdAt?: string
}

type BackendMessage = {
  message_id?: number | string
  messageId?: number | string
  role?: string
  content?: string
  text?: string
}

type BackendConversationDetail = BackendConversationSummary & {
  messages?: BackendMessage[]
}

export type ApiRuntimeMode = 'mock' | 'productive'

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api'
export const BACKEND_BASE_URL = API_BASE_URL.replace(/\/(?:api)\/?$/, '') || API_BASE_URL

let currentMode: ApiRuntimeMode = appConfig.mockModeEnabled ? 'mock' : 'productive'

export function setApiRuntimeMode(nextMode: ApiRuntimeMode) {
  currentMode = nextMode
}

export function getApiRuntimeMode(): ApiRuntimeMode {
  return currentMode
}

const isMockMode = () => currentMode === 'mock'

async function request<T>({ path, ...options }: RequestOptions): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  })

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`)
  }

  return (await response.json()) as T
}

export const apiClient = {
  async checkBackendHealth(options?: { forceNetwork?: boolean }): Promise<boolean> {
    if (!options?.forceNetwork && isMockMode()) return true
    try {
      const response = await fetch(`${BACKEND_BASE_URL}/health`, { method: 'GET' })
      return response.ok
    } catch {
      return false
    }
  },
  async login(email: string, password: string): Promise<LoginResult> {
    const body = new URLSearchParams({ email, password })
    const response = await fetch(`${API_BASE_URL}/accounts/login`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: body.toString(),
    })

    let message: string | undefined
    const contentType = response.headers.get('content-type') ?? ''
    if (contentType.includes('application/json')) {
      try {
        const payload = await response.json()
        if (typeof payload?.message === 'string') {
          message = payload.message
        }
      } catch {
        // ignore body parse errors; fallback message below
      }
    } else {
      try {
        const payloadText = await response.text()
        if (payloadText.trim().length > 0) {
          message = payloadText
        }
      } catch {
        // ignore text parse errors
      }
    }

    if (!response.ok && !message) {
      message = `Login fehlgeschlagen (Status ${response.status})`
    }

    return { status: response.status, ok: response.ok, message }
  },
  async logout(): Promise<void> {
    if (isMockMode()) return
    try {
      await fetch(`${API_BASE_URL}/accounts/logout`, {
        method: 'POST',
        credentials: 'include',
      })
    } catch {
      // swallow logout errors to keep UX responsive
    }
  },
  async getAccount(): Promise<Account> {
    if (isMockMode()) return mockAccount

    const payload = await request<BackendAccountPayload>({ path: '/accounts/', method: 'GET' })

    const accountId = payload?.accountId ?? payload?.id ?? payload?.account_id ?? ''
    const createdAt = payload?.createdAt ?? payload?.created_at ?? new Date().toISOString()
    const displayName = payload?.displayName ?? payload?.username ?? payload?.email ?? 'User'
    const lastLogin = payload?.last_login ?? payload?.lastLogin
    const profileType = payload?.profileType ?? payload?.profile_type

    return {
      accountId: typeof accountId === 'string' ? accountId : String(accountId ?? ''),
      email: payload?.email ?? '',
      displayName,
      createdAt,
      displayNameUpdatedAt: payload?.displayNameUpdatedAt ?? lastLogin,
      emailUpdatedAt: payload?.emailUpdatedAt ?? lastLogin,
      passwordUpdatedAt: payload?.passwordUpdatedAt ?? lastLogin,
      profileType,
    }
  },
  async getSessions(): Promise<SessionToken[]> {
    if (isMockMode()) return mockSessions
    try {
      const result = await request<{ sessions: SessionToken[] }>({ path: '/accounts/sessions', method: 'GET' })
      return result.sessions
    } catch {
      return []
    }
  },
  async getSystemStatus(): Promise<SystemStatus[]> {
    if (isMockMode()) return mockSystemStatus
    try {
      const result = await request<{ services: SystemStatus[] }>({ path: '/', method: 'GET' })
      return result.services
    } catch {
      return []
    }
  },
  async getChats(): Promise<ChatDetail[]> {
    if (isMockMode()) return mockChats

    const summaries = await request<BackendConversationSummary[]>({ path: '/chats/', method: 'GET' })
    const chats = await Promise.all(
      summaries.map(async (summary) => {
        const chatId = summary?.conversation_id ?? summary?.chat_id ?? summary?.chatId
        if (!chatId) {
          return {
            chatId: crypto.randomUUID(),
            chatTitle: summary?.title ?? 'Conversation',
            messages: [],
          }
        }
        try {
          const detail = await request<BackendConversationDetail>({ path: `/chats/${chatId}`, method: 'GET' })
          return normalizeChatDetail(detail)
        } catch {
          return normalizeChatDetail(summary)
        }
      }),
    )

    return chats
  },
  async getChatSummaries(): Promise<ChatSummary[]> {
    if (isMockMode()) return mockChatSummaries
    const summaries = await request<BackendConversationSummary[]>({ path: '/chats/', method: 'GET' })
    return summaries.map(normalizeChatSummary)
  },
  async getDocuments(): Promise<DocumentMeta[]> {
    if (isMockMode()) return mockDocuments
    return []
  },
}

function normalizeChatSummary(input: BackendConversationSummary): ChatSummary {
  const chatId = input.conversation_id ?? input.chat_id ?? input.chatId ?? crypto.randomUUID()
  const createdAt = input.created_at ?? input.createdAt ?? new Date().toISOString()

  return {
    chatId: String(chatId),
    chatTitle: input.title ?? 'Conversation',
    createdAt,
  }
}

function normalizeChatDetail(input: BackendConversationDetail | BackendConversationSummary): ChatDetail {
  const summary = normalizeChatSummary(input)
  const messageSource = 'messages' in input ? input.messages : undefined
  const messages = Array.isArray(messageSource) ? messageSource.map(mapBackendMessage) : []

  return {
    ...summary,
    messages,
  }
}

function mapBackendMessage(message: BackendMessage): ChatMessage {
  const messageId = message.message_id ?? message.messageId ?? crypto.randomUUID()
  const role = message.role === 'assistant' ? 'assistant' : 'user'
  const text = message.content ?? message.text ?? ''

  return {
    messageId: String(messageId),
    role,
    text,
    files: [],
  }
}
