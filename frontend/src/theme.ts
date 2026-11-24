import { createTheme, alpha } from '@mui/material/styles';

export const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#00843D',
      light: '#059669',
      dark: '#005E2B',
      contrastText: '#FFFFFF',
    },
    secondary: {
      main: '#0F172A',
      light: '#334155',
      dark: '#020617',
      contrastText: '#FFFFFF',
    },
    background: {
      default: '#F8FAFC',
      paper: '#FFFFFF',
    },
    text: {
      primary: '#0F172A',
      secondary: '#475569',
    },
    error: {
      main: '#DC2626',
      light: '#EF4444',
      dark: '#B91C1C',
    },
    warning: {
      main: '#D97706',
      light: '#F59E0B',
      dark: '#B45309',
    },
    success: {
      main: '#059669',
      light: '#10B981',
      dark: '#047857',
    },
    info: {
      main: '#2563EB',
      light: '#3B82F6',
      dark: '#1D4ED8',
    },
    divider: '#E2E8F0',
    action: {
      hover: 'rgba(0, 132, 61, 0.04)',
      selected: 'rgba(0, 132, 61, 0.08)',
    },
  },
  typography: {
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    h1: {
      fontFamily: "'Outfit', 'Inter', sans-serif",
      fontWeight: 800,
      fontSize: '2.25rem',
      letterSpacing: '-0.025em',
      color: '#0F172A',
    },
    h2: {
      fontFamily: "'Outfit', 'Inter', sans-serif",
      fontWeight: 800,
      fontSize: '1.875rem',
      letterSpacing: '-0.02em',
      color: '#0F172A',
    },
    h3: {
      fontFamily: "'Outfit', 'Inter', sans-serif",
      fontWeight: 700,
      fontSize: '1.5rem',
      letterSpacing: '-0.015em',
      color: '#0F172A',
    },
    h4: {
      fontFamily: "'Outfit', 'Inter', sans-serif",
      fontWeight: 700,
      fontSize: '1.25rem',
      letterSpacing: '-0.01em',
      color: '#0F172A',
    },
    h5: {
      fontFamily: "'Outfit', 'Inter', sans-serif",
      fontWeight: 600,
      fontSize: '1.1rem',
      color: '#0F172A',
    },
    h6: {
      fontFamily: "'Outfit', 'Inter', sans-serif",
      fontWeight: 600,
      fontSize: '1rem',
      color: '#0F172A',
    },
    subtitle1: {
      fontWeight: 500,
      fontSize: '0.95rem',
      color: '#475569',
    },
    subtitle2: {
      fontWeight: 600,
      fontSize: '0.85rem',
      color: '#475569',
    },
    body1: {
      fontSize: '0.925rem',
      lineHeight: 1.6,
      color: '#1E293B',
    },
    body2: {
      fontSize: '0.85rem',
      lineHeight: 1.55,
      color: '#475569',
    },
    button: {
      textTransform: 'none',
      fontWeight: 600,
      fontSize: '0.875rem',
      letterSpacing: '-0.005em',
    },
    caption: {
      fontSize: '0.75rem',
      color: '#64748B',
    },
    overline: {
      fontSize: '0.68rem',
      fontWeight: 700,
      letterSpacing: '0.08em',
      color: '#64748B',
      textTransform: 'uppercase',
    },
  },
  shape: {
    borderRadius: 12,
  },
  shadows: [
    'none',
    '0 1px 3px 0 rgba(0, 0, 0, 0.04), 0 1px 2px -1px rgba(0, 0, 0, 0.02)',
    '0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.03)',
    '0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -4px rgba(0, 0, 0, 0.03)',
    '0 14px 20px -3px rgba(0, 0, 0, 0.06), 0 6px 8px -4px rgba(0, 0, 0, 0.03)',
    '0 20px 25px -5px rgba(0, 0, 0, 0.06), 0 8px 10px -6px rgba(0, 0, 0, 0.03)',
    '0 25px 30px -5px rgba(0, 0, 0, 0.07), 0 10px 12px -6px rgba(0, 0, 0, 0.04)',
    '0 30px 35px -5px rgba(0, 0, 0, 0.08), 0 12px 14px -6px rgba(0, 0, 0, 0.04)',
    '0 35px 40px -5px rgba(0, 0, 0, 0.09), 0 14px 16px -6px rgba(0, 0, 0, 0.04)',
    '0 40px 45px -5px rgba(0, 0, 0, 0.09), 0 16px 18px -6px rgba(0, 0, 0, 0.04)',
    '0 45px 50px -5px rgba(0, 0, 0, 0.10), 0 18px 20px -6px rgba(0, 0, 0, 0.05)',
    '0 50px 55px -5px rgba(0, 0, 0, 0.10), 0 20px 22px -6px rgba(0, 0, 0, 0.05)',
    '0 55px 60px -5px rgba(0, 0, 0, 0.11), 0 22px 24px -6px rgba(0, 0, 0, 0.05)',
    '0 60px 65px -5px rgba(0, 0, 0, 0.11), 0 24px 26px -6px rgba(0, 0, 0, 0.05)',
    '0 65px 70px -5px rgba(0, 0, 0, 0.12), 0 26px 28px -6px rgba(0, 0, 0, 0.06)',
    '0 70px 75px -5px rgba(0, 0, 0, 0.12), 0 28px 30px -6px rgba(0, 0, 0, 0.06)',
    '0 75px 80px -5px rgba(0, 0, 0, 0.13), 0 30px 32px -6px rgba(0, 0, 0, 0.06)',
    '0 80px 85px -5px rgba(0, 0, 0, 0.13), 0 32px 34px -6px rgba(0, 0, 0, 0.06)',
    '0 85px 90px -5px rgba(0, 0, 0, 0.14), 0 34px 36px -6px rgba(0, 0, 0, 0.07)',
    '0 90px 95px -5px rgba(0, 0, 0, 0.14), 0 36px 38px -6px rgba(0, 0, 0, 0.07)',
    '0 95px 100px -5px rgba(0, 0, 0, 0.15), 0 38px 40px -6px rgba(0, 0, 0, 0.07)',
    '0 100px 105px -5px rgba(0, 0, 0, 0.15), 0 40px 42px -6px rgba(0, 0, 0, 0.07)',
    '0 105px 110px -5px rgba(0, 0, 0, 0.16), 0 42px 44px -6px rgba(0, 0, 0, 0.08)',
    '0 110px 115px -5px rgba(0, 0, 0, 0.16), 0 44px 46px -6px rgba(0, 0, 0, 0.08)',
    '0 115px 120px -5px rgba(0, 0, 0, 0.17), 0 46px 48px -6px rgba(0, 0, 0, 0.08)',
  ],
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundColor: '#F8FAFC',
          color: '#0F172A',
        },
      },
    },
    MuiCard: {
      defaultProps: {
        elevation: 0,
      },
      styleOverrides: {
        root: {
          borderRadius: 14,
          border: '1px solid #E2E8F0',
          backgroundColor: '#FFFFFF',
          transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
          boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.04), 0 1px 2px -1px rgba(0, 0, 0, 0.02)',
          '&:hover': {
            borderColor: '#CBD5E1',
            boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.06), 0 8px 10px -6px rgba(0, 0, 0, 0.04)',
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
          padding: '9px 20px',
          fontWeight: 600,
          fontSize: '0.875rem',
          textTransform: 'none',
          transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
        },
        contained: {
          '&.MuiButton-containedPrimary': {
            background: 'linear-gradient(135deg, #00843D 0%, #059669 100%)',
            boxShadow: '0 2px 6px rgba(0, 132, 61, 0.25)',
            '&:hover': {
              background: 'linear-gradient(135deg, #006B30 0%, #00843D 100%)',
              boxShadow: '0 4px 14px rgba(0, 132, 61, 0.35)',
              transform: 'translateY(-1px)',
            },
          },
          '&.MuiButton-containedSecondary': {
            background: '#0F172A',
            color: '#FFFFFF',
            boxShadow: '0 2px 6px rgba(15, 23, 42, 0.2)',
            '&:hover': {
              background: '#1E293B',
              boxShadow: '0 4px 14px rgba(15, 23, 42, 0.3)',
              transform: 'translateY(-1px)',
            },
          },
        },
        outlined: {
          borderColor: '#E2E8F0',
          color: '#334155',
          borderWidth: '1.5px',
          '&:hover': {
            borderColor: '#00843D',
            color: '#00843D',
            backgroundColor: 'rgba(0, 132, 61, 0.04)',
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
          backgroundColor: 'rgba(255, 255, 255, 0.92)',
          backdropFilter: 'blur(16px)',
          color: '#0F172A',
          borderBottom: '1px solid #E2E8F0',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.03)',
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: '#FFFFFF',
          borderRight: '1px solid #E2E8F0',
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
              borderColor: '#E2E8F0',
              borderWidth: '1.5px',
            },
            '&:hover fieldset': {
              borderColor: '#94A3B8',
            },
            '&.Mui-focused fieldset': {
              borderColor: '#00843D',
              borderWidth: '2px',
            },
            '&.Mui-focused': {
              boxShadow: '0 0 0 3px rgba(0, 132, 61, 0.12)',
            },
          },
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
          backgroundColor: 'rgba(0, 132, 61, 0.08)',
          color: '#00843D',
          border: '1px solid rgba(0, 132, 61, 0.2)',
          '&:hover': {
            backgroundColor: 'rgba(0, 132, 61, 0.15)',
          },
        },
        colorSecondary: {
          backgroundColor: 'rgba(15, 23, 42, 0.06)',
          color: '#0F172A',
          border: '1px solid rgba(15, 23, 42, 0.12)',
          '&:hover': {
            backgroundColor: 'rgba(15, 23, 42, 0.1)',
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
          backgroundColor: 'rgba(0, 132, 61, 0.1)',
          color: '#00843D',
          border: '1.5px solid rgba(0, 132, 61, 0.2)',
        },
      },
    },
    MuiTableHead: {
      styleOverrides: {
        root: {
          '& .MuiTableCell-head': {
            backgroundColor: '#F8FAFC',
            color: '#475569',
            fontWeight: 700,
            fontSize: '0.72rem',
            textTransform: 'uppercase',
            letterSpacing: '0.06em',
            borderBottom: '1px solid #E2E8F0',
          },
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderBottom: '1px solid #F1F5F9',
          padding: '14px 16px',
          fontSize: '0.875rem',
        },
      },
    },
    MuiDialog: {
      styleOverrides: {
        paper: {
          borderRadius: 16,
          border: '1px solid #E2E8F0',
          boxShadow: '0 20px 60px rgba(0, 0, 0, 0.12)',
        },
      },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: {
          borderRadius: 10,
          marginBottom: 3,
          transition: 'all 0.2s ease',
          '&.Mui-selected': {
            backgroundColor: 'rgba(0, 132, 61, 0.09)',
            color: '#00843D',
            '&:hover': {
              backgroundColor: 'rgba(0, 132, 61, 0.14)',
            },
          },
          '&:hover': {
            backgroundColor: '#F1F5F9',
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
    MuiDivider: {
      styleOverrides: {
        root: {
          borderColor: '#E2E8F0',
        },
      },
    },
  },
});
