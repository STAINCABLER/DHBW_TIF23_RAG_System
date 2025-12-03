import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.tsx'
import { ThemeProvider } from './theme/ThemeProvider'
import { AuthProvider } from './auth/AuthProvider'
import { RuntimeModeProvider } from './runtime/RuntimeModeProvider'
import './index.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <RuntimeModeProvider>
      <AuthProvider>
        <ThemeProvider>
          <App />
        </ThemeProvider>
      </AuthProvider>
    </RuntimeModeProvider>
  </StrictMode>,
)
