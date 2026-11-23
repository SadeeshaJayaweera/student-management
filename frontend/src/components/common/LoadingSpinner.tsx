import React from 'react'
import { CircularProgress, Box, Typography } from '@mui/material'

interface LoadingSpinnerProps {
  message?: string
  height?: number | string
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  message = 'Loading EduSphere…',
  height = 300,
}) => {
  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height,
        flexDirection: 'column',
        gap: 2,
      }}
    >
      <Box
        component="img"
        src="/nsbm-logo.svg"
        alt="NSBM Logo"
        sx={{
          width: 56,
          height: 56,
          animation: 'pulse 2s infinite ease-in-out',
        }}
      />
      <CircularProgress size={32} thickness={4} color="primary" />
      {message && (
        <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500 }}>
          {message}
        </Typography>
      )}
    </Box>
  )
}
