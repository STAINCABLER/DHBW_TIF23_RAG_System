import type {
  Account,
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

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api'
const USE_MOCK = appConfig.mockModeEnabled

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
  async getAccount(): Promise<Account> {
    if (USE_MOCK) return mockAccount
    return request<Account>({ path: '/accounts/me', method: 'GET' })
  },
  async getSessions(): Promise<SessionToken[]> {
    if (USE_MOCK) return mockSessions
    return request<{ sessions: SessionToken[] }>({ path: '/accounts/sessions', method: 'GET' }).then(
      (res) => res.sessions,
    )
  },
  async getSystemStatus(): Promise<SystemStatus[]> {
    if (USE_MOCK) return mockSystemStatus
    return request<{ services: SystemStatus[] }>({ path: '/', method: 'GET' }).then((res) => res.services)
  },
  async getChats(): Promise<ChatDetail[]> {
    if (USE_MOCK) return mockChats
    return request<{ chats: ChatDetail[] }>({ path: '/chats', method: 'GET' }).then((res) => res.chats)
  },
  async getChatSummaries(): Promise<ChatSummary[]> {
    if (USE_MOCK) return mockChatSummaries
    return request<{ chats: ChatSummary[] }>({ path: '/chats', method: 'GET' }).then((res) => res.chats)
  },
  async getDocuments(): Promise<DocumentMeta[]> {
    if (USE_MOCK) return mockDocuments
    return request<{ documents: DocumentMeta[] }>({ path: '/docs', method: 'GET' }).then((res) => res.documents)
  },
}
