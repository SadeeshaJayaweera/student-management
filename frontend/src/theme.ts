import { createTheme, alpha } from '@mui/material/styles';

export const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#00843D',
      light: '#4CAF72',
      dark: '#006B30',
      contrastText: '#FFFFFF',
    },
    secondary: {
      main: '#1565C0',
      light: '#5E92F3',
      dark: '#003C8F',
      contrastText: '#FFFFFF',
    },
    background: {
      default: '#F5F7FA',
      paper: '#FFFFFF',
    },
    text: {
      primary: '#1A1A2E',
      secondary: '#5A6474',
    },
    error: {
      main: '#E53935',
      light: '#FF6F60',
      dark: '#AB000D',
    },
    warning: {
      main: '#F9A825',
      light: '#FFD95A',
      dark: '#C17900',
    },
    success: {
      main: '#00843D',
      light: '#4CAF72',
      dark: '#006B30',
    },
    info: {
      main: '#1565C0',
      light: '#5E92F3',
      dark: '#003C8F',
    },
    divider: 'rgba(0, 0, 0, 0.08)',
    action: {
      hover: 'rgba(0, 132, 61, 0.06)',
      selected: 'rgba(0, 132, 61, 0.1)',
    },
  },
  typography: {
    fontFamily: "'Inter', system-ui, -apple-system, sans-serif",
    h1: {
      fontFamily: "'Outfit', 'Inter', sans-serif",
      fontWeight: 800,
      fontSize: '2rem',
      color: '#1A1A2E',
    },
    h2: {
      fontFamily: "'Outfit', 'Inter', sans-serif",
      fontWeight: 700,
      fontSize: '1.75rem',
      color: '#1A1A2E',
    },
    h3: {
      fontFamily: "'Outfit', 'Inter', sans-serif",
      fontWeight: 700,
      fontSize: '1.5rem',
      color: '#1A1A2E',
    },
    h4: {
      fontFamily: "'Outfit', 'Inter', sans-serif",
      fontWeight: 700,
      fontSize: '1.25rem',
      color: '#1A1A2E',
    },
    h5: {
      fontFamily: "'Outfit', 'Inter', sans-serif",
      fontWeight: 600,
      fontSize: '1.1rem',
      color: '#1A1A2E',
    },
    h6: {
      fontFamily: "'Outfit', 'Inter', sans-serif",
      fontWeight: 600,
      fontSize: '1rem',
      color: '#1A1A2E',
    },
    subtitle1: {
      fontWeight: 500,
      fontSize: '0.95rem',
      color: '#5A6474',
    },
    subtitle2: {
      fontWeight: 600,
      fontSize: '0.85rem',
      color: '#5A6474',
    },
    body1: {
      fontSize: '0.925rem',
      lineHeight: 1.6,
    },
    body2: {
      fontSize: '0.85rem',
      lineHeight: 1.5,
      color: '#5A6474',
    },
    button: {
      textTransform: 'none',
      fontWeight: 600,
      fontSize: '0.875rem',
    },
    caption: {
      fontSize: '0.75rem',
      color: '#8A94A6',
    },
    overline: {
      fontSize: '0.68rem',
      fontWeight: 700,
      letterSpacing: '0.08em',
      color: '#8A94A6',
    },
  },
  shape: {
    borderRadius: 12,
  },
  shadows: [
    'none',
    '0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.06)',
    '0 2px 6px rgba(0,0,0,0.05), 0 1px 3px rgba(0,0,0,0.06)',
    '0 4px 12px rgba(0,0,0,0.06), 0 1px 4px rgba(0,0,0,0.04)',
    '0 6px 16px rgba(0,0,0,0.07), 0 2px 6px rgba(0,0,0,0.04)',
    '0 8px 24px rgba(0,0,0,0.08), 0 2px 8px rgba(0,0,0,0.04)',
    '0 12px 28px rgba(0,0,0,0.09), 0 4px 10px rgba(0,0,0,0.04)',
    '0 14px 32px rgba(0,0,0,0.10), 0 4px 12px rgba(0,0,0,0.04)',
    '0 16px 36px rgba(0,0,0,0.10), 0 6px 14px rgba(0,0,0,0.04)',
    '0 18px 40px rgba(0,0,0,0.11), 0 6px 16px rgba(0,0,0,0.04)',
    '0 20px 44px rgba(0,0,0,0.11), 0 8px 18px rgba(0,0,0,0.04)',
    '0 22px 48px rgba(0,0,0,0.12), 0 8px 20px rgba(0,0,0,0.04)',
    '0 24px 52px rgba(0,0,0,0.12), 0 10px 22px rgba(0,0,0,0.04)',
    '0 26px 56px rgba(0,0,0,0.13), 0 10px 24px rgba(0,0,0,0.04)',
    '0 28px 60px rgba(0,0,0,0.13), 0 12px 26px rgba(0,0,0,0.04)',
    '0 30px 64px rgba(0,0,0,0.14), 0 12px 28px rgba(0,0,0,0.04)',
    '0 32px 68px rgba(0,0,0,0.14), 0 14px 30px rgba(0,0,0,0.04)',
    '0 34px 72px rgba(0,0,0,0.15), 0 14px 32px rgba(0,0,0,0.04)',
    '0 36px 76px rgba(0,0,0,0.15), 0 16px 34px rgba(0,0,0,0.04)',
    '0 38px 80px rgba(0,0,0,0.16), 0 16px 36px rgba(0,0,0,0.04)',
    '0 40px 84px rgba(0,0,0,0.16), 0 18px 38px rgba(0,0,0,0.04)',
    '0 42px 88px rgba(0,0,0,0.17), 0 18px 40px rgba(0,0,0,0.04)',
    '0 44px 92px rgba(0,0,0,0.17), 0 20px 42px rgba(0,0,0,0.04)',
    '0 46px 96px rgba(0,0,0,0.18), 0 20px 44px rgba(0,0,0,0.04)',
    '0 48px 100px rgba(0,0,0,0.18), 0 22px 46px rgba(0,0,0,0.04)',
  ],
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundColor: '#F5F7FA',
          color: '#1A1A2E',
        },
      },
    },
    MuiCard: {
      defaultProps: {
        elevation: 0,
      },
      styleOverrides: {
        root: {
          borderRadius: 16,
          border: '1px solid rgba(0, 0, 0, 0.06)',
          backgroundColor: '#FFFFFF',
          transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
          '&:hover': {
            borderColor: 'rgba(0, 132, 61, 0.2)',
            boxShadow: '0 8px 28px rgba(0, 0, 0, 0.08)',
          },
        },
      },
    },
    MuiCardContent: {
      styleOverrides: {
        root: {
          padding: 24,
          '&:last-child': {
            paddingBottom: 24,
          },
        },
      },
    },
    MuiButton: {
      defaultProps: {
        disableElevation: true,
      },
      styleOverrides: {
        root: {
          borderRadius: 10,
          padding: '10px 22px',
          fontWeight: 600,
          fontSize: '0.875rem',
          textTransform: 'none',
          transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
        },
        contained: {
          '&.MuiButton-containedPrimary': {
            background: 'linear-gradient(135deg, #00843D 0%, #00A34A 100%)',
            boxShadow: '0 4px 14px rgba(0, 132, 61, 0.3)',
            '&:hover': {
              background: 'linear-gradient(135deg, #006B30 0%, #00843D 100%)',
              boxShadow: '0 6px 20px rgba(0, 132, 61, 0.4)',
              transform: 'translateY(-1px)',
            },
          },
          '&.MuiButton-containedSecondary': {
            boxShadow: '0 4px 14px rgba(21, 101, 192, 0.3)',
            '&:hover': {
              boxShadow: '0 6px 20px rgba(21, 101, 192, 0.4)',
              transform: 'translateY(-1px)',
            },
          },
        },
        outlined: {
          borderWidth: '1.5px',
          '&:hover': {
            borderWidth: '1.5px',
          },
        },
      },
    },
    MuiAppBar: {
      defaultProps: {
        elevation: 0,
      },
      styleOverrides: {
        root: {
          backgroundColor: '#FFFFFF',
          color: '#1A1A2E',
          borderBottom: '1px solid rgba(0, 0, 0, 0.06)',
          backdropFilter: 'blur(20px)',
          background: 'rgba(255, 255, 255, 0.92)',
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: '#FFFFFF',
          borderRight: '1px solid rgba(0, 0, 0, 0.06)',
          boxShadow: 'none',
        },
      },
    },
    MuiTextField: {
      defaultProps: {
        variant: 'outlined',
        size: 'small',
      },
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 10,
            backgroundColor: '#FFFFFF',
            transition: 'all 0.2s ease',
            '& fieldset': {
              borderColor: 'rgba(0, 0, 0, 0.12)',
              borderWidth: '1.5px',
            },
            '&:hover fieldset': {
              borderColor: 'rgba(0, 132, 61, 0.4)',
            },
            '&.Mui-focused fieldset': {
              borderColor: '#00843D',
              borderWidth: '2px',
            },
            '&.Mui-focused': {
              boxShadow: '0 0 0 3px rgba(0, 132, 61, 0.1)',
            },
          },
        },
      },
    },
    MuiPaper: {
      defaultProps: {
        elevation: 0,
      },
      styleOverrides: {
        root: {
          borderRadius: 12,
          border: '1px solid rgba(0, 0, 0, 0.06)',
          backgroundImage: 'none',
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          fontWeight: 600,
          fontSize: '0.78rem',
        },
        colorPrimary: {
          backgroundColor: alpha('#00843D', 0.1),
          color: '#00843D',
          '&:hover': {
            backgroundColor: alpha('#00843D', 0.18),
          },
        },
        colorSecondary: {
          backgroundColor: alpha('#1565C0', 0.1),
          color: '#1565C0',
          '&:hover': {
            backgroundColor: alpha('#1565C0', 0.18),
          },
        },
      },
    },
    MuiAvatar: {
      styleOverrides: {
        root: {
          fontWeight: 700,
          fontSize: '0.9rem',
        },
        colorDefault: {
          backgroundColor: alpha('#00843D', 0.12),
          color: '#00843D',
        },
      },
    },
    MuiTableHead: {
      styleOverrides: {
        root: {
          '& .MuiTableCell-head': {
            backgroundColor: '#F5F7FA',
            color: '#5A6474',
            fontWeight: 700,
            fontSize: '0.75rem',
            textTransform: 'uppercase',
            letterSpacing: '0.06em',
            borderBottom: '1px solid rgba(0, 0, 0, 0.08)',
          },
        },
      },
    },
    MuiTableRow: {
      styleOverrides: {
        root: {
          transition: 'background 0.2s ease',
          '&:hover': {
            backgroundColor: 'rgba(0, 132, 61, 0.03)',
          },
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderBottom: '1px solid rgba(0, 0, 0, 0.05)',
          padding: '14px 16px',
          fontSize: '0.875rem',
        },
      },
    },
    MuiDialog: {
      styleOverrides: {
        paper: {
          borderRadius: 16,
          border: '1px solid rgba(0, 0, 0, 0.08)',
          boxShadow: '0 20px 60px rgba(0, 0, 0, 0.12)',
        },
      },
    },
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          borderRadius: 8,
          fontSize: '0.78rem',
          fontWeight: 500,
          backgroundColor: '#1A1A2E',
          boxShadow: '0 4px 14px rgba(0, 0, 0, 0.15)',
        },
      },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: {
          borderRadius: 10,
          marginBottom: 2,
          transition: 'all 0.2s ease',
          '&.Mui-selected': {
            backgroundColor: alpha('#00843D', 0.1),
            color: '#00843D',
            '&:hover': {
              backgroundColor: alpha('#00843D', 0.15),
            },
          },
          '&:hover': {
            backgroundColor: 'rgba(0, 0, 0, 0.04)',
          },
        },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 600,
          fontSize: '0.875rem',
          minHeight: 44,
          borderRadius: 8,
          '&.Mui-selected': {
            color: '#00843D',
          },
        },
      },
    },
    MuiTabs: {
      styleOverrides: {
        indicator: {
          height: 3,
          borderRadius: '3px 3px 0 0',
          backgroundColor: '#00843D',
        },
      },
    },
    MuiLinearProgress: {
      styleOverrides: {
        root: {
          borderRadius: 999,
          height: 8,
          backgroundColor: 'rgba(0, 132, 61, 0.1)',
        },
        bar: {
          borderRadius: 999,
          background: 'linear-gradient(90deg, #00843D, #00A34A)',
        },
      },
    },
    MuiSwitch: {
      styleOverrides: {
        root: {
          '& .MuiSwitch-switchBase.Mui-checked': {
            color: '#00843D',
          },
          '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': {
            backgroundColor: '#00843D',
          },
        },
      },
    },
    MuiAlert: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          fontWeight: 500,
        },
      },
    },
    MuiBadge: {
      styleOverrides: {
        colorPrimary: {
          backgroundColor: '#00843D',
        },
      },
    },
    MuiIconButton: {
      styleOverrides: {
        root: {
          borderRadius: 10,
          transition: 'all 0.2s ease',
          '&:hover': {
            backgroundColor: 'rgba(0, 132, 61, 0.08)',
          },
        },
      },
    },
    MuiDivider: {
      styleOverrides: {
        root: {
          borderColor: 'rgba(0, 0, 0, 0.06)',
        },
      },
    },
    MuiMenu: {
      styleOverrides: {
        paper: {
          borderRadius: 12,
          border: '1px solid rgba(0, 0, 0, 0.08)',
          boxShadow: '0 10px 40px rgba(0, 0, 0, 0.1)',
        },
      },
    },
    MuiMenuItem: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          margin: '2px 6px',
          padding: '8px 14px',
          fontSize: '0.875rem',
          '&:hover': {
            backgroundColor: 'rgba(0, 132, 61, 0.06)',
          },
          '&.Mui-selected': {
            backgroundColor: 'rgba(0, 132, 61, 0.1)',
            '&:hover': {
              backgroundColor: 'rgba(0, 132, 61, 0.14)',
            },
          },
        },
      },
    },
    MuiSkeleton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          backgroundColor: 'rgba(0, 0, 0, 0.06)',
        },
      },
    },
  },
});
