// src/components/PlanViewer.jsx
// Displays implementation.md inline with clean markdown rendering
import React, { useState } from 'react';
import { Box, Typography, Collapse, IconButton, Button, Chip } from '@mui/material';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import ArticleOutlinedIcon from '@mui/icons-material/ArticleOutlined';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import CheckIcon from '@mui/icons-material/Check';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Box as MuiBox } from '@mui/material';

// Minimal markdown components for the plan viewer
const planMd = {
  h1: ({ children }) => (
    <Typography sx={{ fontSize: '18px', fontWeight: 700, color: '#fff', mt: 2, mb: 1, pb: 0.5, borderBottom: '1px solid rgba(124,92,252,0.3)' }}>
      {children}
    </Typography>
  ),
  h2: ({ children }) => (
    <Typography sx={{ fontSize: '14px', fontWeight: 700, color: '#a78bfa', mt: 2, mb: 0.5, display: 'flex', alignItems: 'center', gap: 0.5 }}>
      {children}
    </Typography>
  ),
  h3: ({ children }) => (
    <Typography sx={{ fontSize: '13px', fontWeight: 600, color: '#c4b5fd', mt: 1.5, mb: 0.3 }}>
      {children}
    </Typography>
  ),
  p: ({ children }) => (
    <Typography sx={{ fontSize: '13.5px', color: 'var(--text-1)', lineHeight: 1.7, mb: 0.8, fontFamily: "'Inter'" }}>
      {children}
    </Typography>
  ),
  strong: ({ children }) => <Box component="strong" sx={{ color: '#fff', fontWeight: 700 }}>{children}</Box>,
  ul: ({ children }) => <Box component="ul" sx={{ pl: 2.5, mb: 0.8, '& li': { mb: 0.3 } }}>{children}</Box>,
  ol: ({ children }) => <Box component="ol" sx={{ pl: 2.5, mb: 0.8, '& li': { mb: 0.3 } }}>{children}</Box>,
  li: ({ children }) => (
    <Box component="li" sx={{ fontSize: '13.5px', color: 'var(--text-1)', lineHeight: 1.65, fontFamily: "'Inter'" }}>
      {children}
    </Box>
  ),
  code({ inline, className, children }) {
    if (inline) return (
      <Box component="code" sx={{ px: '5px', bgcolor: 'rgba(124,92,252,0.15)', borderRadius: '4px', fontFamily: "'JetBrains Mono'", fontSize: '12px', color: '#c4b5fd' }}>
        {children}
      </Box>
    );
    return (
      <Box component="pre" sx={{
        my: 1, p: 1.5, bgcolor: 'rgba(0,0,0,0.3)', borderRadius: '8px',
        fontFamily: "'JetBrains Mono', monospace", fontSize: '12px',
        color: 'var(--text-2)', overflowX: 'auto', lineHeight: 1.6,
        border: '1px solid rgba(255,255,255,0.06)',
        whiteSpace: 'pre',
      }}>
        <Box component="code">{children}</Box>
      </Box>
    );
  },
  blockquote: ({ children }) => (
    <Box sx={{ borderLeft: '3px solid #7c5cfc', pl: 1.5, my: 1, color: 'var(--text-2)', fontStyle: 'italic' }}>
      {children}
    </Box>
  ),
  hr: () => <Box sx={{ borderBottom: '1px solid rgba(255,255,255,0.07)', my: 1.5 }} />,
};

export default function PlanViewer({ planContent, onApprove, loading, needsApproval }) {
  const [open,   setOpen]   = useState(true);
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try { await navigator.clipboard.writeText(planContent || ''); }
    catch { /* ignore */ }
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Always render if needsApproval is true, even without plan text
  const hasContent = planContent && planContent.length > 0;
  const lineCount  = hasContent ? planContent.split('\n').length : 0;


  return (
    <Box sx={{
      mx: 3, mb: 2,
      border: '1px solid rgba(124,92,252,0.35)',
      borderRadius: '12px',
      overflow: 'hidden',
      bgcolor: 'rgba(124,92,252,0.05)',
    }}>
      {/* Header bar */}
      <Box sx={{
        display: 'flex', alignItems: 'center', gap: 1.2,
        px: 2, py: 1.2,
        bgcolor: 'rgba(124,92,252,0.12)',
        borderBottom: open ? '1px solid rgba(124,92,252,0.2)' : 'none',
        cursor: 'pointer',
      }}
        onClick={() => setOpen(v => !v)}
      >
        <ArticleOutlinedIcon sx={{ color: '#a78bfa', fontSize: 18 }} />
        <Typography sx={{ fontSize: '13.5px', fontWeight: 600, color: '#a78bfa', flexGrow: 1 }}>
          implementation.md
        </Typography>
        <Chip
          label={hasContent ? `${lineCount} lines` : 'Loading...'}
          size="small"
          sx={{ height: 20, fontSize: '10px', bgcolor: 'rgba(124,92,252,0.15)', color: '#c4b5fd', border: 'none' }}
        />
        <IconButton size="small" onClick={e => { e.stopPropagation(); handleCopy(); }}
          sx={{ color: copied ? 'var(--green)' : 'var(--text-3)', p: 0.4, '&:hover': { color: 'var(--text-1)' } }}>
          {copied ? <CheckIcon sx={{ fontSize: 14 }} /> : <ContentCopyIcon sx={{ fontSize: 14 }} />}
        </IconButton>
        {open ? <KeyboardArrowUpIcon sx={{ fontSize: 18, color: 'var(--text-3)' }} />
               : <KeyboardArrowDownIcon sx={{ fontSize: 18, color: 'var(--text-3)' }} />}
      </Box>

      {/* Plan content */}
      <Collapse in={open}>
        <Box sx={{ px: 2.5, py: 2, maxHeight: 480, overflowY: 'auto' }}>
          {hasContent ? (
            <ReactMarkdown remarkPlugins={[remarkGfm]} components={planMd}>
              {planContent}
            </ReactMarkdown>
          ) : (
            <Typography sx={{ fontSize: '13.5px', color: 'var(--text-2)', fontStyle: 'italic' }}>
              Plan content unavailable — the model may not have returned it. You can still approve to proceed.
            </Typography>
          )}
        </Box>

        {/* Approve bar */}
        <Box sx={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          px: 2, py: 1.5,
          borderTop: '1px solid rgba(124,92,252,0.2)',
          bgcolor: 'rgba(0,0,0,0.15)',
          gap: 2,
        }}>
          <Typography sx={{ fontSize: '12.5px', color: 'var(--text-2)' }}>
            Review the plan above, then approve to start execution.
          </Typography>
          <Button
            variant="contained"
            startIcon={<CheckCircleIcon sx={{ fontSize: 16 }} />}
            onClick={onApprove}
            disabled={loading}
            sx={{
              bgcolor: '#7c5cfc', color: '#fff', textTransform: 'none',
              fontWeight: 600, fontSize: '13px', borderRadius: '8px',
              px: 2.5, py: 0.7, flexShrink: 0,
              '&:hover': { bgcolor: '#6d4fe8' },
              '&.Mui-disabled': { bgcolor: 'rgba(124,92,252,0.3)', color: 'rgba(255,255,255,0.4)' },
            }}
          >
            Approve & Execute
          </Button>
        </Box>
      </Collapse>
    </Box>
  );
}
