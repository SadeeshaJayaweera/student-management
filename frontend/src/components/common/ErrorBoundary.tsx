import React, { Component, ErrorInfo, ReactNode } from 'react'
import { Paper, Box, Typography, Button } from '@mui/material'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  }

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('EduSphere UI caught error:', error, errorInfo)
  }

  public render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <Paper
            elevation={0}
            sx={{
              p: 6,
              textAlign: 'center',
              my: 4,
              mx: 'auto',
              maxWidth: 600,
              borderRadius: 4,
              border: '1px solid rgba(0,0,0,0.08)',
              boxShadow: '0 8px 32px rgba(0,0,0,0.06)',
            }}
          >
            <Box sx={{ fontSize: '3rem', mb: 2 }}>⚠️</Box>
            <Typography variant="h5" sx={{ fontWeight: 800 }} gutterBottom>
              Something went wrong
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              {this.state.error?.message || 'An unexpected rendering error occurred.'}
            </Typography>
            <Button
              variant="contained"
              color="primary"
              onClick={() => this.setState({ hasError: false, error: null })}
            >
              Try Again
            </Button>
          </Paper>
        )
      )
    }

    return this.props.children
  }
}
