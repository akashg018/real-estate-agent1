import React from 'react';
import { ThemeProvider, createTheme, AppBar, Toolbar, Typography, Box } from '@mui/material';
import ChatInterface from './components/ChatInterface';

const theme = createTheme({
  palette: {
    primary: {
      main: '#2196f3',
      dark: '#1976d2',
      light: '#64b5f6'
    },
    secondary: {
      main: '#4caf50',
      dark: '#388e3c',
      light: '#81c784'
    },
    background: {
      default: '#f5f5f5',
      paper: '#ffffff'
    },
    text: {
      primary: '#1A1D1F',
      secondary: '#666666'
    }
  },
  typography: {
    fontFamily: "'Roboto', 'Helvetica', 'Arial', sans-serif",
    h6: {
      fontWeight: 500
    },
    body1: {
      fontSize: '0.9375rem'
    }
  },
  shape: {
    borderRadius: 8
  }
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <div style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
        <AppBar position="static" elevation={0} sx={{ backgroundColor: '#1976d2' }}>
          <Toolbar>
            <Box sx={{ display: 'flex', alignItems: 'center', flex: 1 }}>
              <Typography variant="h6" component="div" sx={{ 
                flexGrow: 1, 
                fontWeight: 600,
                fontSize: '1.2rem',
                color: '#fff',
                display: 'flex',
                alignItems: 'center',
                gap: 1
              }}>
                🏠 AI Real Estate Assistant
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Typography variant="subtitle1" sx={{ 
                  fontWeight: 500,
                  color: '#fff'
                }}>
                  Your Intelligent Property Search Companion
                </Typography>
              </Box>
            </Box>
          </Toolbar>
        </AppBar>
        <Box sx={{ flex: 1, display: 'flex', bgcolor: '#f5f5f5' }}>
          <ChatInterface />
        </Box>
      </div>
    </ThemeProvider>
  );
}

export default App;
