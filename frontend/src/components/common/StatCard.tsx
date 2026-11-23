import React from 'react'
import { Card, Box, Typography } from '@mui/material'

interface StatCardProps {
  icon: string
  value: string | number
  label: string
  color?: string
  bg?: string
  variant?: string
}

export const StatCard: React.FC<StatCardProps> = ({
  icon,
  value,
  label,
  color = '#00843D',
  bg = 'rgba(0, 132, 61, 0.08)',
}) => {
  return (
    <Card
      sx={{
        p: 2.5,
        display: 'flex',
        alignItems: 'center',
        gap: 2.25,
        borderRadius: 3.5,
        border: '1px solid rgba(0, 0, 0, 0.07)',
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.04)',
        transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
        '&:hover': {
          transform: 'translateY(-2px)',
          borderColor: 'rgba(0, 132, 61, 0.3)',
          boxShadow: '0 8px 24px rgba(0, 0, 0, 0.08)',
        },
      }}
    >
      <Box
        sx={{
          width: 54,
          height: 54,
          borderRadius: 3,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '1.6rem',
          flexShrink: 0,
          backgroundColor: bg,
          color: color,
        }}
      >
        {icon}
      </Box>
      <Box sx={{ minWidth: 0, flex: 1 }}>
        <Typography
          variant="h4"
          sx={{
            fontWeight: 800,
            fontSize: '1.75rem',
            color: color || 'text.primary',
            lineHeight: 1.2,
          }}
        >
          {value}
        </Typography>
        <Typography
          variant="body2"
          sx={{
            color: 'text.secondary',
            fontWeight: 500,
            mt: 0.25,
            fontSize: '0.85rem',
          }}
        >
          {label}
        </Typography>
      </Box>
    </Card>
  )
}
