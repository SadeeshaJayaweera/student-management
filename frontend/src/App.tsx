import React from 'react'
import { BrowserRouter } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { ThemeProvider, CssBaseline } from '@mui/material'
import { theme } from './theme'
import { AuthProvider } from '@/contexts/AuthContext'
import { AppRoutes } from '@/routes/AppRoutes'
import { ErrorBoundary } from '@/components/common/ErrorBoundary'

export default function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <ErrorBoundary>
        <BrowserRouter>
          <AuthProvider>
            <AppRoutes />
            <Toaster
              position="bottom-right"
              toastOptions={{
                style: {
                  background: '#FFFFFF',
                  color: '#1A1A2E',
                  border: '1px solid rgba(0,0,0,0.08)',
                  borderRadius: 12,
                  boxShadow: '0 8px 32px rgba(0,0,0,0.08)',
                  fontSize: '.9rem',
                },
              }}
            />
          </AuthProvider>
        </BrowserRouter>
      </ErrorBoundary>
    </ThemeProvider>
  )
}
