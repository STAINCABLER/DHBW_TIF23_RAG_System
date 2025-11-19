import { createBrowserRouter } from 'react-router-dom'
import { DashboardPage } from '../pages/DashboardPage'
import { LandingPage } from '../pages/LandingPage'
import { ChatPage } from '../pages/ChatPage'
import { HistoryPage } from '../pages/HistoryPage'
import { AccountPage } from '../pages/AccountPage'
import { DocumentsPage } from '../pages/DocumentsPage'
import { AdministrativePage } from '../pages/AdministrativePage'
import { AuthPage } from '../pages/AuthPage'
import { NotFoundPage } from '../pages/NotFoundPage'
import { ProtectedLayout } from './ProtectedLayout'

export const router = createBrowserRouter([
  // Öffentliche Startseite
  {
    path: '/',
    element: <LandingPage />,
  },
  // Geschützte Bereiche innerhalb des AppLayouts
  {
    element: <ProtectedLayout />,
    children: [
      { path: '/dash', element: <DashboardPage /> },
      { path: '/chat/:chatId?', element: <ChatPage /> },
      { path: '/history', element: <HistoryPage /> },
      { path: '/account', element: <AccountPage /> },
      { path: '/docs', element: <DocumentsPage /> },
      { path: '/administrative', element: <AdministrativePage /> },
    ],
  },
  { path: '/login', element: <AuthPage mode="login" /> },
  { path: '/register', element: <AuthPage mode="register" /> },
  { path: '*', element: <NotFoundPage /> },
])
