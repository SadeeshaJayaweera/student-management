import React from 'react'
import { Card, Box, Typography, Chip } from '@mui/material'
import TrendingUpIcon from '@mui/icons-material/TrendingUp'
import TrendingDownIcon from '@mui/icons-material/TrendingDown'

interface StatCardProps {
  icon: React.ReactNode | string
  value: string | number
  label: string
  color?: string
  bg?: string
  trend?: string
  trendPositive?: boolean
}

export const StatCard: React.FC<StatCardProps> = ({
  icon,
  value,
  label,
  color = '#00843D',
  bg = 'rgba(0, 132, 61, 0.08)',
  trend,
  trendPositive = true,
}) => {
  return (
    <Card
      sx={{
        p: 2.5,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        borderRadius: 3.5,
        border: '1px solid #E2E8F0',
        backgroundColor: '#FFFFFF',
        boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.04), 0 1px 2px -1px rgba(0, 0, 0, 0.02)',
        transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
        '&:hover': {
          transform: 'translateY(-2px)',
          borderColor: '#CBD5E1',
          boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.06), 0 8px 10px -6px rgba(0, 0, 0, 0.04)',
        },
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mb: 2 }}>
        <Box
          sx={{
            width: 48,
            height: 48,
            borderRadius: 2.75,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1.4rem',
            backgroundColor: bg,
            color: color,
            border: `1px solid ${bg}`,
          }}
        >
          {icon}
        </Box>
        {trend && (
          <Chip
            icon={
              trendPositive ? (
                <TrendingUpIcon sx={{ fontSize: '0.85rem !important', color: '#059669 !important' }} />
              ) : (
                <TrendingDownIcon sx={{ fontSize: '0.85rem !important', color: '#DC2626 !important' }} />
              )
            }
            label={trend}
            size="small"
            sx={{
              height: 22,
              fontSize: '0.68rem',
              fontWeight: 700,
              bgcolor: trendPositive ? 'rgba(5, 150, 105, 0.08)' : 'rgba(220, 38, 38, 0.08)',
              color: trendPositive ? '#059669' : '#DC2626',
              borderRadius: 1.5,
            }}
          />
        )}
      </Box>

      <Box>
        <Typography
          variant="h4"
          sx={{
            fontWeight: 800,
            fontSize: '1.85rem',
            fontFamily: "'Outfit', sans-serif",
            color: '#0F172A',
            letterSpacing: '-0.02em',
            lineHeight: 1.15,
          }}
        >
          {value}
        </Typography>
        <Typography
          variant="body2"
          sx={{
            color: '#64748B',
            fontWeight: 600,
            mt: 0.5,
            fontSize: '0.825rem',
          }}
        >
          {label}
        </Typography>
      </Box>
    </Card>
  )
}
