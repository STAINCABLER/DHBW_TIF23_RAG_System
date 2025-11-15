export type MockAccount = {
  id: 'test-user' | 'test-admin'
  displayName: string
  role: 'user' | 'admin'
  email: string
  password: string
}

export const MOCK_ACCOUNTS: MockAccount[] = [
  {
    id: 'test-user',
    displayName: 'Test User',
    role: 'user',
    email: 'test.user@example.com',
    password: 'user-pass',
  },
  {
    id: 'test-admin',
    displayName: 'Test Admin',
    role: 'admin',
    email: 'test.admin@example.com',
    password: 'admin-pass',
  },
]
