import { createBrowserRouter } from 'react-router-dom'
import { AppLayout } from '../components/layout/AppLayout'
import { DashboardPage } from '../pages/DashboardPage'
import { ChatPage } from '../pages/ChatPage'
import { HistoryPage } from '../pages/HistoryPage'
import { AccountPage } from '../pages/AccountPage'
import { DocumentsPage } from '../pages/DocumentsPage'
import { AdministrativePage } from '../pages/AdministrativePage'
import { AuthPage } from '../pages/AuthPage'
import { NotFoundPage } from '../pages/NotFoundPage'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: 'chat/:chatId?', element: <ChatPage /> },
      { path: 'history', element: <HistoryPage /> },
      { path: 'account', element: <AccountPage /> },
      { path: 'docs', element: <DocumentsPage /> },
      { path: 'administrative', element: <AdministrativePage /> },
    ],
  },
  { path: '/login', element: <AuthPage mode="login" /> },
  { path: '/register', element: <AuthPage mode="register" /> },
  { path: '*', element: <NotFoundPage /> },
])
