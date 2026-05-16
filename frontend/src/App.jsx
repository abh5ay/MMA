// src/App.jsx
import React, { useState, useEffect } from 'react';
import { ThemeProvider, createTheme, CssBaseline, Box, Tabs, Tab } from '@mui/material';
import ChatIcon          from '@mui/icons-material/Chat';
import ModelTrainingIcon from '@mui/icons-material/ModelTraining';
import Sidebar    from './components/Sidebar';
import ChatWindow from './components/ChatWindow';
import TrainPanel from './components/TrainPanel';

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary:    { main: '#7c5cfc' },
    secondary:  { main: '#37d399' },
    background: { default: '#1a1b1e', paper: '#25262b' },
    text:       { primary: '#e8e9ee', secondary: '#9395a5' },
  },
  typography: {
    fontFamily: "'Inter', system-ui, sans-serif",
  },
  components: {
    MuiCssBaseline: { styleOverrides: { body: { scrollbarWidth: 'thin' } } },
    MuiPaper: { styleOverrides: { root: { backgroundImage: 'none' } } },
  },
});

export default function App() {
  const [tab, setTab] = useState(0);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ display: 'flex', height: '100vh', overflow: 'hidden', bgcolor: 'background.default' }}>
        <Sidebar />

        {/* Main panel */}
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>

          {/* Top tab bar */}
          <Tabs
            value={tab} onChange={(_, v) => setTab(v)}
            sx={{
              minHeight: 40, borderBottom: '1px solid var(--border)',
              bgcolor: 'var(--bg-sidebar)',
              '& .MuiTab-root': { minHeight: 40, fontSize: '12px', textTransform: 'none', color: 'var(--text-3)', fontWeight: 500, gap: 0.5 },
              '& .Mui-selected': { color: '#7c5cfc !important' },
              '& .MuiTabs-indicator': { bgcolor: '#7c5cfc', height: '2px' },
            }}
          >
            <Tab icon={<ChatIcon sx={{ fontSize: 15 }} />} iconPosition="start" label="Chat / Developer" />
            <Tab icon={<ModelTrainingIcon sx={{ fontSize: 15 }} />} iconPosition="start" label="Train Model" />
          </Tabs>

          {/* Panel content */}
          <Box sx={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
            {tab === 0 && <ChatWindow />}
            {tab === 1 && <TrainPanel />}
          </Box>
        </Box>
      </Box>
    </ThemeProvider>
  );
}
