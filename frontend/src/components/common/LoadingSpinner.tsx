import React from 'react'
import { CircularProgress, Box, Typography } from '@mui/material'

interface LoadingSpinnerProps {
  message?: string
  height?: number | string
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  message = 'Loading EduSphere…',
  height = 340,
}) => {
  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height,
        flexDirection: 'column',
        gap: 2.5,
      }}
    >
      <Box sx={{ position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <CircularProgress
          size={64}
          thickness={3}
          sx={{
            color: '#00843D',
            position: 'absolute',
            zIndex: 1,
          }}
        />
        <CircularProgress
          variant="determinate"
          value={100}
          size={64}
          thickness={3}
          sx={{
            color: '#E2E8F0',
          }}
        />
        <Box
          component="img"
          src="/nsbm-logo-icon.png"
          alt="NSBM Logo"
          sx={{
            width: 38,
            height: 38,
            objectFit: 'contain',
          }}
        />
      </Box>
      {message && (
        <Typography variant="body2" sx={{ color: '#64748B', fontWeight: 600, fontSize: '0.85rem' }}>
          {message}
        </Typography>
      )}
    </Box>
  )
}
