// src/components/TypingMessage.jsx — Typewriter + Markdown with Inter font
import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Box, Typography } from '@mui/material';
import CodeBlock from './CodeBlock';

const mdComponents = {
  code({ inline, className, children }) {
    const lang = /language-(\w+)/.exec(className || '')?.[1];
    return !inline
      ? <CodeBlock language={lang}>{children}</CodeBlock>
      : (
        <Box component="code" sx={{
          px: '5px', py: '1px', mx: '1px',
          bgcolor: 'rgba(255,255,255,0.07)',
          border: '1px solid rgba(255,255,255,0.1)',
          borderRadius: '4px',
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: '12.5px',
          color: '#c4b5fd',
        }}>
          {children}
        </Box>
      );
  },
  h1: ({ children }) => (
    <Typography variant="h6" sx={{ fontWeight: 700, color: 'var(--text-1)', mt: 2, mb: 0.5, fontFamily: "'Inter'" }}>{children}</Typography>
  ),
  h2: ({ children }) => (
    <Typography sx={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-1)', mt: 1.5, mb: 0.5, fontFamily: "'Inter'" }}>{children}</Typography>
  ),
  h3: ({ children }) => (
    <Typography sx={{ fontSize: '14.5px', fontWeight: 600, color: 'var(--text-1)', mt: 1, mb: 0.3, fontFamily: "'Inter'" }}>{children}</Typography>
  ),
  p: ({ children }) => (
    <Typography component="p" sx={{ fontSize: '14.5px', color: 'var(--text-1)', lineHeight: 1.75, mb: 1, fontFamily: "'Inter'", whiteSpace: 'pre-wrap' }}>
      {children}
    </Typography>
  ),
  strong: ({ children }) => <Box component="strong" sx={{ fontWeight: 700, color: '#fff' }}>{children}</Box>,
  em:     ({ children }) => <Box component="em"     sx={{ color: 'var(--text-2)', fontStyle: 'italic' }}>{children}</Box>,
  ul: ({ children }) => (
    <Box component="ul" sx={{ pl: 2.5, mb: 1, '& li': { mb: 0.4 } }}>{children}</Box>
  ),
  ol: ({ children }) => (
    <Box component="ol" sx={{ pl: 2.5, mb: 1, '& li': { mb: 0.4 } }}>{children}</Box>
  ),
  li: ({ children }) => (
    <Box component="li" sx={{ fontSize: '14.5px', color: 'var(--text-1)', lineHeight: 1.7, fontFamily: "'Inter'" }}>{children}</Box>
  ),
  blockquote: ({ children }) => (
    <Box sx={{ borderLeft: '3px solid rgba(124,92,252,0.5)', pl: 1.5, ml: 0, my: 1, color: 'var(--text-2)', fontStyle: 'italic' }}>{children}</Box>
  ),
  hr: () => <Box sx={{ borderBottom: '1px solid var(--border)', my: 2 }} />,
  table: ({ children }) => (
    <Box sx={{ overflowX: 'auto', mb: 1 }}>
      <Box component="table" sx={{ borderCollapse: 'collapse', width: '100%', fontSize: '13.5px' }}>{children}</Box>
    </Box>
  ),
  th: ({ children }) => (
    <Box component="th" sx={{ px: 1.5, py: 0.7, textAlign: 'left', bgcolor: 'rgba(255,255,255,0.05)', borderBottom: '1px solid var(--border)', color: 'var(--text-2)', fontWeight: 600, fontSize: '12px' }}>{children}</Box>
  ),
  td: ({ children }) => (
    <Box component="td" sx={{ px: 1.5, py: 0.7, borderBottom: '1px solid var(--border)', color: 'var(--text-1)' }}>{children}</Box>
  ),
};

const TYPING_SPEED = 6; // ms per char

export default function TypingMessage({ content, animate = false }) {
  const [displayed, setDisplayed] = useState(animate ? '' : content);
  const [isTyping,  setIsTyping]  = useState(animate);
  const indexRef    = useRef(0);
  const rafRef      = useRef(null);
  const lastTimeRef = useRef(null);

  useEffect(() => {
    if (!animate) { setDisplayed(content); setIsTyping(false); return; }
    const tick = (ts) => {
      if (!lastTimeRef.current) lastTimeRef.current = ts;
      const elapsed = ts - lastTimeRef.current;
      if (elapsed >= TYPING_SPEED) {
        const add = Math.max(1, Math.floor(elapsed / TYPING_SPEED));
        indexRef.current = Math.min(indexRef.current + add, content.length);
        setDisplayed(content.slice(0, indexRef.current));
        lastTimeRef.current = ts;
      }
      if (indexRef.current < content.length) rafRef.current = requestAnimationFrame(tick);
      else setIsTyping(false);
    };
    rafRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafRef.current);
  }, [content, animate]);

  return (
    <Box>
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={mdComponents}>
        {displayed}
      </ReactMarkdown>
      {isTyping && (
        <Box component="span" sx={{
          display: 'inline-block', width: '2px', height: '16px',
          bgcolor: '#7c5cfc', ml: 0.3, verticalAlign: 'middle',
          animation: 'blink 0.7s step-end infinite',
        }} />
      )}
    </Box>
  );
}
