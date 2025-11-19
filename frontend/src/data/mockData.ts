import type {
  Account,
  ChatDetail,
  ChatSummary,
  DocumentMeta,
  SessionToken,
  SystemStatus,
} from '../api/types'

export const mockAccount: Account = {
  accountId: 'acct-001',
  email: 'rag-admin@example.com',
  displayName: 'RAG Admin',
  createdAt: '2025-10-04T09:10:23Z',
  displayNameUpdatedAt: '2025-11-15T07:45:00Z',
  emailUpdatedAt: '2025-11-10T12:30:00Z',
  passwordUpdatedAt: '2025-11-12T06:15:00Z',
}

export const mockSessions: SessionToken[] = [
  {
    tokenId: 'sess-01',
    createdAt: '2025-11-10T08:00:00Z',
    lastUsedAt: '2025-11-14T08:15:00Z',
    device: 'Edge / Windows',
    location: 'DE',
  },
  {
    tokenId: 'sess-02',
    createdAt: '2025-11-12T11:20:00Z',
    lastUsedAt: '2025-11-14T07:55:00Z',
    device: 'Chrome / Linux',
    location: 'VPN',
  },
]

export const mockDocuments: DocumentMeta[] = [
  {
    fileId: 'file-1',
    fileName: 'kundenaudit.pdf',
    mimeType: 'application/pdf',
    sizeBytes: 865432,
    uploadedAt: '2025-11-12T07:30:00Z',
    tags: ['audit', 'kunde-a'],
    linkedChats: ['chat-01'],
  },
  {
    fileId: 'file-2',
    fileName: 'faq-intern.json',
    mimeType: 'application/json',
    sizeBytes: 20480,
    uploadedAt: '2025-11-13T13:10:00Z',
    tags: ['faq'],
    linkedChats: ['chat-01'],
  },
  {
    fileId: 'file-3',
    fileName: 'training-vorlage.csv',
    mimeType: 'text/csv',
    sizeBytes: 40690,
    uploadedAt: '2025-11-13T15:44:00Z',
    tags: ['training'],
    linkedChats: ['chat-02'],
  },
]

export const mockChatSummaries: ChatSummary[] = [
  {
    chatId: 'chat-01',
    chatTitle: 'Onboarding Leitfaden',
    createdAt: '2025-11-10T09:00:00Z',
  },
  {
    chatId: 'chat-02',
    chatTitle: 'Rechtsfragen Q4',
    createdAt: '2025-11-11T11:30:00Z',
  },
  {
    chatId: 'chat-03',
    chatTitle: 'Produktwissen Retail',
    createdAt: '2025-11-12T14:10:00Z',
  },
]

export const mockChats: ChatDetail[] = [
  {
    chatId: 'chat-01',
    chatTitle: 'Onboarding Leitfaden',
    messages: [
      {
        messageId: 'msg-000',
        role: 'assistant',
        text: 'Willkommen im Chat "Onboarding Leitfaden" – ich liste dir alle relevanten Richtlinien auf Anfrage auf.',
        files: [],
      },
      {
        messageId: 'msg-001',
        role: 'user',
        text: 'Wie sieht der Standard-Onboardingprozess aus?',
        files: [],
      },
      {
        messageId: 'msg-002',
        role: 'assistant',
        text: 'Der Prozess besteht aus den Phasen Anmeldung, Dokumentenupload und Kick-off-Call. Ich habe dir die wichtigsten Dokumente verlinkt.',
        files: [
          { fileId: 'file-1', fileName: 'kundenaudit.pdf' },
          { fileId: 'file-2', fileName: 'faq-intern.json' },
        ],
      },
    ],
  },
  {
    chatId: 'chat-02',
    chatTitle: 'Rechtsfragen Q4',
    messages: [
      {
        messageId: 'msg-009',
        role: 'assistant',
        text: 'Willkommen im Chat "Rechtsfragen Q4". Ich halte rechtliche Deadlines und Vertragsstatus bereit.',
        files: [],
      },
      {
        messageId: 'msg-010',
        role: 'user',
        text: 'Welche Verträge müssen für Q4 erneuert werden?',
        files: [],
      },
      {
        messageId: 'msg-011',
        role: 'assistant',
        text: 'Es stehen die Lieferantenverträge von AlphaTech und ByteLogistics zur Verlängerung an.',
        files: [],
      },
    ],
  },
]

export const mockSystemStatus: SystemStatus[] = [
  {
    name: 'Frontend',
    status: 'online',
    description: 'Build 0.1.0 (docker) – 35ms median response',
    updatedAt: '2025-11-14T08:00:00Z',
  },
  {
    name: 'Backend API',
    status: 'online',
    description: 'Flask API @4000 with 128 active sessions',
    updatedAt: '2025-11-14T08:00:00Z',
  },
  {
    name: 'Retrieval Engine',
    status: 'degraded',
    description: 'Vector sync in progress (ETA 6m)',
    updatedAt: '2025-11-14T07:50:00Z',
  },
  {
    name: 'Redis Cache',
    status: 'online',
    description: 'Hit rate 98%',
    updatedAt: '2025-11-14T07:55:00Z',
  },
]
