// src/components/ToolStep.jsx — Shows agentic tool calls with collapsible output
import React, { useState } from 'react';
import { Box, Typography, Collapse, IconButton } from '@mui/material';
import TerminalIcon from '@mui/icons-material/Terminal';
import CodeIcon from '@mui/icons-material/Code';
import FolderOpenIcon from '@mui/icons-material/FolderOpen';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowRightIcon from '@mui/icons-material/KeyboardArrowRight';

const TOOL_META = {
  run_python: { label: 'Run Python',    icon: <CodeIcon sx={{ fontSize: 14 }} />,         color: '#60a5fa' },
  run_bash:   { label: 'Run Bash',      icon: <TerminalIcon sx={{ fontSize: 14 }} />,      color: '#fbbf24' },
  read_file:  { label: 'Read File',     icon: <FolderOpenIcon sx={{ fontSize: 14 }} />,    color: '#37d399' },
  write_file: { label: 'Write File',    icon: <FolderOpenIcon sx={{ fontSize: 14 }} />,    color: '#37d399' },
  list_dir:   { label: 'List Directory',icon: <FolderOpenIcon sx={{ fontSize: 14 }} />,    color: '#37d399' },
};

export function ToolCall({ tool, input }) {
  const [open, setOpen] = useState(false);
  const meta = TOOL_META[tool] || { label: tool, icon: <CodeIcon sx={{ fontSize: 14 }} />, color: '#9395a5' };

  return (
    <Box sx={{
      my: 0.5,
      border: '1px solid rgba(255,255,255,0.07)',
      borderRadius: '8px',
      overflow: 'hidden',
      animation: 'toolPulse 1.5s ease',
    }}>
      <Box
        onClick={() => setOpen(v => !v)}
        sx={{
          display: 'flex', alignItems: 'center', gap: 1,
          px: 1.5, py: 0.8, cursor: 'pointer',
          bgcolor: 'rgba(255,255,255,0.03)',
          '&:hover': { bgcolor: 'rgba(255,255,255,0.06)' },
        }}
      >
        <Box sx={{ color: meta.color, display: 'flex' }}>{meta.icon}</Box>
        <Typography sx={{ fontSize: '12.5px', fontWeight: 500, color: meta.color, fontFamily: "'Inter'" }}>
          {meta.label}
        </Typography>
        <Box sx={{ flexGrow: 1 }} />
        {open ? <KeyboardArrowDownIcon sx={{ fontSize: 16, color: 'var(--text-3)' }} />
               : <KeyboardArrowRightIcon sx={{ fontSize: 16, color: 'var(--text-3)' }} />}
      </Box>
      <Collapse in={open}>
        <Box sx={{
          px: 1.5, py: 1,
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: '12px',
          color: 'var(--text-2)',
          bgcolor: 'rgba(0,0,0,0.2)',
          whiteSpace: 'pre-wrap',
          borderTop: '1px solid rgba(255,255,255,0.04)',
        }}>
          {input}
        </Box>
      </Collapse>
    </Box>
  );
}

export function ToolResult({ tool, content }) {
  const [open, setOpen] = useState(false);
  const meta = TOOL_META[tool] || { label: tool, color: '#9395a5' };
  const isError = content.startsWith('ERROR');

  return (
    <Box sx={{
      my: 0.5,
      border: `1px solid ${isError ? 'rgba(248,114,114,0.2)' : 'rgba(55,211,153,0.15)'}`,
      borderRadius: '8px',
      overflow: 'hidden',
    }}>
      <Box
        onClick={() => setOpen(v => !v)}
        sx={{
          display: 'flex', alignItems: 'center', gap: 1,
          px: 1.5, py: 0.8, cursor: 'pointer',
          bgcolor: isError ? 'rgba(248,114,114,0.05)' : 'rgba(55,211,153,0.04)',
          '&:hover': { bgcolor: isError ? 'rgba(248,114,114,0.08)' : 'rgba(55,211,153,0.07)' },
        }}
      >
        <CheckCircleOutlineIcon sx={{ fontSize: 14, color: isError ? 'var(--red)' : 'var(--green)' }} />
        <Typography sx={{ fontSize: '12.5px', fontWeight: 500, color: isError ? 'var(--red)' : 'var(--green)' }}>
          {isError ? 'Error' : 'Output'} · {meta.label}
        </Typography>
        <Box sx={{ flexGrow: 1 }} />
        {open ? <KeyboardArrowDownIcon sx={{ fontSize: 16, color: 'var(--text-3)' }} />
               : <KeyboardArrowRightIcon sx={{ fontSize: 16, color: 'var(--text-3)' }} />}
      </Box>
      <Collapse in={open}>
        <Box sx={{
          px: 1.5, py: 1,
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: '12px',
          color: isError ? 'var(--red)' : 'var(--text-2)',
          bgcolor: 'rgba(0,0,0,0.2)',
          whiteSpace: 'pre-wrap',
          maxHeight: 300,
          overflowY: 'auto',
          borderTop: '1px solid rgba(255,255,255,0.04)',
        }}>
          {content}
        </Box>
      </Collapse>
    </Box>
  );
}
