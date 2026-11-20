import React from 'react'

interface LoadingSpinnerProps {
  message?: string
  height?: number | string
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  message = 'Loading EduSphere…',
  height = 300,
}) => {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height,
        flexDirection: 'column',
        gap: 16,
      }}
    >
      <div style={{ fontSize: '2rem' }}>🎓</div>
      <div className="spinner" />
      {message && <div className="text-muted text-sm">{message}</div>}
    </div>
  )
}
