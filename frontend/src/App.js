import React from 'react';
import { ThemeProvider, createTheme } from '@mui/material';
import ChatInterface from './components/ChatInterface';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <ChatInterface />
    </ThemeProvider>
  );
}

export default App;
