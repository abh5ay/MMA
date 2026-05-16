// src/components/CodeBlock.jsx — Clean syntax-highlighted block with copy
import React, { useState } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Box, IconButton, Typography, Tooltip } from '@mui/material';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import CheckIcon from '@mui/icons-material/Check';

export default function CodeBlock({ language, children }) {
  const [copied, setCopied] = useState(false);
  const [preview, setPreview] = useState(false);
  const code = String(children).replace(/\n$/, '');

  const handleCopy = async () => {
    try { await navigator.clipboard.writeText(code); }
    catch {
      const el = document.createElement('textarea');
      el.value = code; document.body.appendChild(el); el.select();
      document.execCommand('copy'); document.body.removeChild(el);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Box sx={{ my: 1.5, borderRadius: '10px', overflow: 'hidden', border: '1px solid rgba(255,255,255,0.08)' }}>
      {/* Header */}
      <Box sx={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        px: 1.5, py: 0.6,
        bgcolor: 'rgba(0,0,0,0.3)',
        borderBottom: '1px solid rgba(255,255,255,0.06)',
      }}>
        <Typography sx={{ fontSize: '11px', color: 'var(--text-3)', fontFamily: "'JetBrains Mono'", fontWeight: 500 }}>
          {language || 'code'}
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          {language === 'html' && (
            <Tooltip title={preview ? "Hide Preview" : "Live Preview"} placement="top">
              <IconButton size="small" onClick={() => setPreview(!preview)} sx={{ p: 0.5, color: preview ? '#7c5cfc' : 'var(--text-3)', '&:hover': { color: 'var(--text-1)' } }}>
                <span style={{ fontSize: '11px', fontWeight: 600, padding: '0 4px' }}>{preview ? 'Code' : 'Preview'}</span>
              </IconButton>
            </Tooltip>
          )}
          <Tooltip title={copied ? 'Copied!' : 'Copy'} placement="left">
            <IconButton size="small" onClick={handleCopy} sx={{ p: 0.5, color: copied ? 'var(--green)' : 'var(--text-3)', '&:hover': { color: 'var(--text-1)' } }}>
              {copied ? <CheckIcon sx={{ fontSize: 14 }} /> : <ContentCopyIcon sx={{ fontSize: 14 }} />}
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Content */}
      {preview && language === 'html' ? (
        <Box sx={{ width: '100%', height: '400px', bgcolor: '#fff', position: 'relative' }}>
          <iframe
            title="preview"
            srcDoc={code}
            style={{ width: '100%', height: '100%', border: 'none', background: '#fff' }}
            sandbox="allow-scripts"
          />
        </Box>
      ) : (
        <SyntaxHighlighter
          language={language || 'text'}
          style={vscDarkPlus}
          customStyle={{ margin: 0, padding: '12px 16px', background: '#1e1f23', fontSize: '13px', fontFamily: "'JetBrains Mono', monospace", lineHeight: 1.65 }}
          showLineNumbers={code.split('\n').length > 5}
          lineNumberStyle={{ color: 'var(--text-3)', minWidth: '2.5em', paddingRight: '1em', fontSize: '11px' }}
        >
          {code}
        </SyntaxHighlighter>
      )}
    </Box>
  );
}
