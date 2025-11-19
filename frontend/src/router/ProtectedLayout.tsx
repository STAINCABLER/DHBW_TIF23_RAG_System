import { Navigate } from 'react-router-dom'
import { useAuth } from '../auth/useAuth'
import { AppLayout } from '../components/layout/AppLayout'

export function ProtectedLayout() {
  const { user } = useAuth()
  if (!user) {
    return <Navigate to="/" replace />
  }
  return <AppLayout />
}
