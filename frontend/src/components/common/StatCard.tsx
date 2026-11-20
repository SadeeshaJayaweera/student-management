import React from 'react'

interface StatCardProps {
  icon: string
  value: string | number
  label: string
  color: string
  bg: string
  variant?: string
}

export const StatCard: React.FC<StatCardProps> = ({
  icon,
  value,
  label,
  color,
  bg,
  variant = 'stat-purple',
}) => {
  return (
    <div className={`stat-card ${variant}`}>
      <div className="stat-icon" style={{ background: bg }}>
        {icon}
      </div>
      <div>
        <div className="stat-value" style={{ color }}>
          {value}
        </div>
        <div className="stat-label">{label}</div>
      </div>
    </div>
  )
}
