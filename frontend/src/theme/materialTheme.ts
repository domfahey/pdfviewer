import { createTheme } from '@mui/material/styles';

// PDF Viewer Material Theme
export const pdfViewerTheme = createTheme({
  palette: {
    primary: {
      main: '#1976d2', // Professional blue
      light: '#42a5f5',
      dark: '#1565c0',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#dc004e', // Accent red for important actions
      light: '#ff5983',
      dark: '#9a0036',
      contrastText: '#ffffff',
    },
    background: {
      default: '#f5f5f5', // Light gray background
      paper: '#ffffff',
    },
    text: {
      primary: '#212121',
      secondary: '#757575',
    },
    grey: {
      50: '#fafafa',
      100: '#f5f5f5',
      200: '#eeeeee',
      300: '#e0e0e0',
      400: '#bdbdbd',
      500: '#9e9e9e',
      600: '#757575',
      700: '#616161',
      800: '#424242',
      900: '#212121',
    },
    divider: '#e0e0e0',
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 300,
      lineHeight: 1.2,
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 400,
      lineHeight: 1.3,
    },
    h3: {
      fontSize: '1.5rem',
      fontWeight: 500,
      lineHeight: 1.4,
    },
    h4: {
      fontSize: '1.25rem',
      fontWeight: 500,
      lineHeight: 1.4,
    },
    h5: {
      fontSize: '1.125rem',
      fontWeight: 500,
      lineHeight: 1.5,
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 500,
      lineHeight: 1.6,
    },
    subtitle1: {
      fontSize: '1rem',
      fontWeight: 400,
      lineHeight: 1.75,
    },
    subtitle2: {
      fontSize: '0.875rem',
      fontWeight: 500,
      lineHeight: 1.57,
    },
    body1: {
      fontSize: '1rem',
      fontWeight: 400,
      lineHeight: 1.5,
    },
    body2: {
      fontSize: '0.875rem',
      fontWeight: 400,
      lineHeight: 1.43,
    },
    button: {
      fontSize: '0.875rem',
      fontWeight: 500,
      textTransform: 'none', // Keep original casing
    },
    caption: {
      fontSize: '0.75rem',
      fontWeight: 400,
      lineHeight: 1.66,
    },
    overline: {
      fontSize: '0.625rem',
      fontWeight: 400,
      lineHeight: 2.66,
      textTransform: 'uppercase',
    },
  },
  shape: {
    borderRadius: 8, // Consistent rounded corners
  },
  spacing: 8, // 8px grid system
  components: {
    // Customize Material components for PDF viewer
    MuiAppBar: {
      styleOverrides: {
        root: {
          boxShadow: '0px 2px 4px -1px rgba(0,0,0,0.2)',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          transition: 'box-shadow 0.3s ease-in-out',
          '&:hover': {
            boxShadow: '0px 4px 8px -2px rgba(0,0,0,0.2)',
          },
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          textTransform: 'none',
          fontWeight: 500,
          minHeight: 36,
        },
        contained: {
          boxShadow: '0px 2px 4px -1px rgba(0,0,0,0.2)',
          '&:hover': {
            boxShadow: '0px 4px 8px -2px rgba(0,0,0,0.2)',
          },
        },
      },
    },
    MuiIconButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: 8,
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 8,
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 8,
        },
        elevation1: {
          boxShadow: '0px 2px 4px -1px rgba(0,0,0,0.2)',
        },
        elevation2: {
          boxShadow: '0px 3px 6px -2px rgba(0,0,0,0.2)',
        },
        elevation3: {
          boxShadow: '0px 4px 8px -2px rgba(0,0,0,0.2)',
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          borderRadius: 0, // Drawers typically don't have rounded corners
        },
      },
    },
    MuiToolbar: {
      styleOverrides: {
        root: {
          minHeight: 64,
          paddingLeft: 16,
          paddingRight: 16,
        },
      },
    },
    MuiFab: {
      styleOverrides: {
        root: {
          boxShadow: '0px 3px 6px -2px rgba(0,0,0,0.2)',
          '&:hover': {
            boxShadow: '0px 6px 12px -4px rgba(0,0,0,0.2)',
          },
        },
      },
    },
  },
  breakpoints: {
    values: {
      xs: 0,
      sm: 600,
      md: 960,
      lg: 1280,
      xl: 1920,
    },
  },
});

// Dark theme variant (for future dark mode support)
export const pdfViewerDarkTheme = createTheme({
  ...pdfViewerTheme,
  palette: {
    ...pdfViewerTheme.palette,
    mode: 'dark',
    primary: {
      main: '#90caf9',
      light: '#e3f2fd',
      dark: '#42a5f5',
      contrastText: '#000000',
    },
    background: {
      default: '#121212',
      paper: '#1e1e1e',
    },
    text: {
      primary: '#ffffff',
      secondary: '#b3b3b3',
    },
  },
});
