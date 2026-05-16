// src/components/ChatWindow.jsx — SSE streaming, tokens appear in real-time
import React, { useState, useEffect, useRef } from 'react';
import {
  Box, TextField, IconButton, Typography, CircularProgress, Chip,
  Button, Collapse,
} from '@mui/material';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import AutoFixHighOutlinedIcon from '@mui/icons-material/AutoFixHighOutlined';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ArticleOutlinedIcon from '@mui/icons-material/ArticleOutlined';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import CheckIcon from '@mui/icons-material/Check';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import ChatMessage from './ChatMessage';

const STREAM_URL = `${import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'}/chat/stream`;

// ── Inline Plan Card ─────────────────────────────────────────────────────────
const planMd = {
  h1: ({ children }) => <Typography sx={{ fontSize: '20px', fontWeight: 700, color: '#fff', mt: 2, mb: 1, pb: 0.5, borderBottom: '1px solid rgba(124,92,252,0.3)' }}>{children}</Typography>,
  h2: ({ children }) => <Typography sx={{ fontSize: '16px', fontWeight: 700, color: '#a78bfa', mt: 1.5, mb: 0.4 }}>{children}</Typography>,
  h3: ({ children }) => <Typography sx={{ fontSize: '15px', fontWeight: 600, color: '#c4b5fd', mt: 1, mb: 0.3 }}>{children}</Typography>,
  p:  ({ children }) => <Typography sx={{ fontSize: '15px', color: '#e8e9ee', lineHeight: 1.7, mb: 0.8 }}>{children}</Typography>,
  strong: ({ children }) => <Box component="strong" sx={{ color: '#fff', fontWeight: 700 }}>{children}</Box>,
  ul: ({ children }) => <Box component="ul" sx={{ pl: 2.5, mb: 0.8 }}>{children}</Box>,
  ol: ({ children }) => <Box component="ol" sx={{ pl: 2.5, mb: 0.8 }}>{children}</Box>,
  li: ({ children }) => <Box component="li" sx={{ fontSize: '15px', color: '#e8e9ee', lineHeight: 1.65, mb: 0.3 }}>{children}</Box>,
  code({ inline, children }) {
    if (inline) return <Box component="code" sx={{ px: '5px', bgcolor: 'rgba(124,92,252,0.15)', borderRadius: '4px', fontFamily: "'JetBrains Mono'", fontSize: '13px', color: '#c4b5fd' }}>{children}</Box>;
    return <Box component="pre" sx={{ my: 1, p: 1.5, bgcolor: 'rgba(0,0,0,0.3)', borderRadius: '8px', fontFamily: "'JetBrains Mono'", fontSize: '13px', color: '#9395a5', overflowX: 'auto', whiteSpace: 'pre', lineHeight: 1.6 }}><Box component="code">{children}</Box></Box>;
  },
  hr: () => <Box sx={{ borderBottom: '1px solid rgba(255,255,255,0.07)', my: 1.5 }} />,
};

function PlanCard({ planContent, planReady, onApprove, loading }) {
  const [open, setOpen]     = useState(true);
  const [copied, setCopied] = useState(false);
  const text       = planContent || '';
  const lineCount  = text ? text.split('\n').length : 0;
  const isBuilding = !!text && !planReady;  // streaming in but not yet complete

  const handleCopy = async () => {
    try { await navigator.clipboard.writeText(text); } catch {}
    setCopied(true); setTimeout(() => setCopied(false), 2000);
  };

  if (!text && !planReady && !onApprove) return null;

  return (
    <Box sx={{ mx: 2, mb: 2, border: '1px solid rgba(124,92,252,0.4)', borderRadius: '12px', overflow: 'hidden', bgcolor: 'rgba(124,92,252,0.06)' }}>
      {/* Header */}
      <Box onClick={() => setOpen(v => !v)} sx={{ display: 'flex', alignItems: 'center', gap: 1.2, px: 2, py: 1.2, bgcolor: 'rgba(124,92,252,0.14)', cursor: 'pointer', borderBottom: open ? '1px solid rgba(124,92,252,0.2)' : 'none', '&:hover': { bgcolor: 'rgba(124,92,252,0.2)' } }}>
        <ArticleOutlinedIcon sx={{ color: '#a78bfa', fontSize: 18 }} />
        <Typography sx={{ fontSize: '13.5px', fontWeight: 600, color: '#a78bfa', flexGrow: 1 }}>
          implementation.md {isBuilding && <Box component="span" sx={{ fontSize: '11px', color: '#7c5cfc', ml: 1 }}>● writing…</Box>}
        </Typography>
        <Chip label={`${lineCount} lines`} size="small" sx={{ height: 20, fontSize: '10px', bgcolor: 'rgba(124,92,252,0.2)', color: '#c4b5fd' }} />
        <IconButton size="small" onClick={e => { e.stopPropagation(); handleCopy(); }} sx={{ color: copied ? '#37d399' : '#5c5f6e', p: 0.4 }}>
          {copied ? <CheckIcon sx={{ fontSize: 14 }} /> : <ContentCopyIcon sx={{ fontSize: 14 }} />}
        </IconButton>
        {open ? <KeyboardArrowUpIcon sx={{ fontSize: 18, color: '#5c5f6e' }} /> : <KeyboardArrowDownIcon sx={{ fontSize: 18, color: '#5c5f6e' }} />}
      </Box>

      {/* Scrollable plan content */}
      <Collapse in={open}>
        <Box sx={{ px: 2.5, py: 2, maxHeight: 500, overflowY: 'auto' }}>
          <ReactMarkdown remarkPlugins={[remarkGfm]} components={planMd}>{text}</ReactMarkdown>
          {isBuilding && (
            <Box component="span" sx={{ display: 'inline-block', width: '2px', height: '16px', bgcolor: '#7c5cfc', ml: 0.3, verticalAlign: 'middle', animation: 'blink 0.7s step-end infinite' }} />
          )}
        </Box>
      </Collapse>

      {/* ── Approve bar — ALWAYS visible at the bottom, outside Collapse ── */}
      {onApprove && (
        <Box sx={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          flexWrap: 'wrap', gap: 1, px: 2, py: 1.5,
          borderTop: '1px solid rgba(124,92,252,0.3)',
          bgcolor: 'rgba(124,92,252,0.1)',
        }}>
          <Box>
            <Typography sx={{ fontSize: '13px', fontWeight: 600, color: '#a78bfa', lineHeight: 1.2 }}>
              Plan ready — waiting for your approval
            </Typography>
            <Typography sx={{ fontSize: '11.5px', color: '#5c5f6e', mt: 0.2 }}>
              Scroll up to review, then click to start execution.
            </Typography>
          </Box>
          <Button
            variant="contained"
            startIcon={<CheckCircleIcon sx={{ fontSize: 15 }} />}
            onClick={onApprove}
            disabled={loading}
            sx={{
              bgcolor: '#7c5cfc', color: '#fff', textTransform: 'none',
              fontWeight: 700, fontSize: '13.5px', borderRadius: '8px',
              px: 3, py: 0.9, flexShrink: 0,
              boxShadow: '0 0 20px rgba(124,92,252,0.4)',
              '&:hover': { bgcolor: '#6d4fe8', boxShadow: '0 0 24px rgba(124,92,252,0.6)' },
            }}
          >
            Approve &amp; Execute
          </Button>
        </Box>
      )}
    </Box>
  );
}


// ── Welcome ───────────────────────────────────────────────────────────────────
const WELCOME = `Hello! I'm **MultiModelAI**, your agentic AI assistant.

**Developer** workflow: ask me to build something → I write a plan → you approve → I build it step by step.

Select an agent and model from the sidebar, then ask me anything!`;

let _id = 1;
const newId = () => _id++;

// ── Main Component ────────────────────────────────────────────────────────────
export default function ChatWindow() {
  const [messages,        setMessages]        = useState([{ id: newId(), role: 'assistant', content: WELCOME }]);
  const [input,           setInput]           = useState('');
  const [loading,         setLoading]         = useState(false);
  const [agentLabel,      setAgentLabel]      = useState('Developer');
  const [modelLabel,      setModelLabel]      = useState('HuggingFace');
  const [pendingApproval, setPendingApproval] = useState(null);
  const endRef       = useRef(null);
  const readerRef    = useRef(null); // track active stream reader

  // Sync sidebar labels
  useEffect(() => {
    const AL = { development: 'Developer', cybersecurity: 'Cybersecurity', research: 'Research' };
    const ML = { 'api:hf': 'HuggingFace · Qwen-72B', 'api:nvidia': 'NVIDIA NIM · Gemma-4 31B', 'api:nvidia-mistral': 'NVIDIA Mistral 3.5', 'api:grok': 'Grok 3 · xAI', 'api:gpt-oss': 'GPT-OSS 120B', 'api:together': 'DeepSeek Coder 33B', 'api:cerebras': 'Cerebras · Llama-3.3-70B', 'local:qwen3-cyber': 'Qwen3-14B Cyber', 'local:dan-qwen': 'DAN-Qwen3 1.7B', 'local:ollama': 'Ollama', 'api:gpt': 'OpenAI GPT-4o-mini', 'api:gemini': 'Google Gemini 2.0' };
    const sync = () => {
      setAgentLabel(AL[localStorage.getItem('selectedAgent') || 'development'] || 'Developer');
      setModelLabel(ML[localStorage.getItem('selectedModel') || 'api:hf'] || 'HuggingFace');
    };
    sync();
    const iv = setInterval(sync, 400);
    return () => clearInterval(iv);
  }, []);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, loading]);

  // ── SSE stream reader ───────────────────────────────────────────────────────
  const streamRequest = async ({ prompt, phase = 'auto', original_prompt = null }) => {
    const agent = localStorage.getItem('selectedAgent') || 'development';
    const model = localStorage.getItem('selectedModel') || 'api:hf';

    // Create placeholder bot message
    const botId = newId();
    setMessages(prev => [...prev, {
      id:          botId,
      role:        'assistant',
      content:     '',
      steps:       [],
      planContent: '',       // accumulates plan_token directly
      planReady:   false,    // true once plan_ready event fires
      needsApproval: false,
    }]);
    setLoading(true);

    try {
      const resp = await fetch(STREAM_URL, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ agent, model, prompt, phase, original_prompt }),
      });

      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);

      const reader  = resp.body.getReader();
      readerRef.current = reader;
      const decoder = new TextDecoder();
      let   buffer  = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop(); // keep partial line

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const raw = line.slice(6).trim();
          if (!raw) continue;
          try {
            const event = JSON.parse(raw);
            handleEvent(event, botId, prompt);
          } catch {}
        }
      }
    } catch (e) {
      setMessages(prev => prev.map(m => m.id === botId ? { ...m, content: `**Error:** ${e.message}` } : m));
    } finally {
      setLoading(false);
      readerRef.current = null;
    }
  };

  // ── Handle individual SSE events ────────────────────────────────────────────
  const handleEvent = (event, botId, originalPrompt) => {
    switch (event.type) {

      case 'plan_token':
        // Accumulate tokens DIRECTLY into planContent — no intermediate planBuilding
        setMessages(prev => prev.map(m =>
          m.id === botId ? { ...m, planContent: (m.planContent || '') + event.content } : m
        ));
        break;

      case 'plan_ready':
        // Combined event: plan is done AND needs approval
        // Set planReady + needsApproval in ONE state update to avoid race conditions
        setMessages(prev => prev.map(m =>
          m.id === botId
            ? { ...m, planReady: true, needsApproval: true, content: '✅ Implementation plan ready. Review and approve below.' }
            : m
        ));
        // Also set pendingApproval so the approve button appears
        if (event.needs_approval) {
          setPendingApproval({ prompt: originalPrompt, msgId: botId });
        }
        break;

      // Keep needs_approval as fallback for older backend versions
      case 'needs_approval':
        setMessages(prev => prev.map(m =>
          m.id === botId ? { ...m, needsApproval: true } : m
        ));
        setPendingApproval({ prompt: originalPrompt, msgId: botId });
        break;

      case 'token':
        // Regular response / execution tokens
        setMessages(prev => prev.map(m =>
          m.id === botId ? { ...m, content: (m.content || '') + event.content } : m
        ));
        break;

      case 'tool_call':
        setMessages(prev => prev.map(m =>
          m.id === botId
            ? { ...m, steps: [...(m.steps || []), { type: 'tool', tool: event.tool, content: event.content }] }
            : m
        ));
        break;

      case 'tool_result':
        setMessages(prev => prev.map(m =>
          m.id === botId
            ? { ...m, steps: [...(m.steps || []), { type: 'result', tool: event.tool, content: event.content }] }
            : m
        ));
        break;

      case 'done':
        setLoading(false);
        break;

      case 'error':
        setMessages(prev => prev.map(m =>
          m.id === botId ? { ...m, content: `**Error:** ${event.content}` } : m
        ));
        setLoading(false);
        break;
    }
  };

  const handleSend = async () => {
    const text = input.trim();
    if (!text || loading) return;
    setMessages(prev => [...prev, { id: newId(), role: 'user', content: text }]);
    setInput('');
    await streamRequest({ prompt: text, phase: 'auto' });
  };

  const handleApprove = async () => {
    if (!pendingApproval || loading) return;
    const { prompt, msgId } = pendingApproval;
    setPendingApproval(null);
    // Mark plan as approved (hide approve button)
    setMessages(prev => prev.map(m => m.id === msgId ? { ...m, needsApproval: false } : m));
    setMessages(prev => [...prev, { id: newId(), role: 'user', content: '✅ Approved — please execute the plan.' }]);
    await streamRequest({ prompt: 'execute', phase: 'execute', original_prompt: prompt });
  };

  const handleKey = e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  return (
    <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', bgcolor: '#1a1b1e' }}>

      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, px: 3, py: 1.5, borderBottom: '1px solid rgba(255,255,255,0.07)', flexShrink: 0 }}>
        <Typography sx={{ fontSize: '14px', fontWeight: 600, color: '#e8e9ee', mr: 1 }}>{agentLabel}</Typography>
        <Chip label={modelLabel} size="small" sx={{ fontSize: '11px', height: 22, bgcolor: 'rgba(124,92,252,0.1)', color: '#a78bfa', border: '1px solid rgba(124,92,252,0.25)' }} />
        <Box sx={{ flexGrow: 1 }} />
        <Chip icon={<AutoFixHighOutlinedIcon sx={{ fontSize: '13px !important', color: '#7c5cfc !important' }} />} label="Agentic · Streaming" size="small" sx={{ fontSize: '11px', height: 22, bgcolor: 'rgba(124,92,252,0.1)', color: '#a78bfa', border: '1px solid rgba(124,92,252,0.25)' }} />
      </Box>

      {/* Messages */}
      <Box sx={{ flex: 1, overflowY: 'auto', py: 1, display: 'flex', flexDirection: 'column' }}>
        {messages.map(msg => (
          <React.Fragment key={msg.id}>
            <ChatMessage
              role={msg.role}
              content={msg.content}
              steps={msg.steps}
              animate={false}   // no fake typewriter — streaming IS the animation
            />

            {/* Plan card — shows as soon as first plan_token arrives */}
            {(msg.planContent || msg.planReady) && (
              <PlanCard
                planContent={msg.planContent}
                planReady={msg.planReady}
                onApprove={msg.needsApproval && pendingApproval?.msgId === msg.id ? handleApprove : null}
                loading={loading}
              />
            )}
          </React.Fragment>
        ))}

        {/* Thinking indicator — only shown before any token arrives */}
        {loading && messages[messages.length - 1]?.role !== 'user' && !messages[messages.length - 1]?.content && !messages[messages.length - 1]?.planContent && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, px: 3, py: 1 }}>
            <Box sx={{ width: 30, height: 30, borderRadius: '50%', bgcolor: 'rgba(124,92,252,0.2)', border: '1px solid rgba(124,92,252,0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <CircularProgress size={14} thickness={5} sx={{ color: '#7c5cfc' }} />
            </Box>
            <Typography sx={{ fontSize: '13px', color: '#5c5f6e', fontStyle: 'italic' }}>Connecting…</Typography>
          </Box>
        )}
        <div ref={endRef} />
      </Box>

      {/* Input */}
      <Box sx={{ px: 3, pb: 3, pt: 1, flexShrink: 0 }}>
        <Box sx={{
          display: 'flex', alignItems: 'flex-end', gap: 1,
          bgcolor: '#2c2d33', borderRadius: '12px',
          border: '1px solid rgba(255,255,255,0.07)', px: 2, py: 1,
          '&:focus-within': { borderColor: 'rgba(124,92,252,0.5)' },
        }}>
          <TextField
            fullWidth multiline maxRows={8} variant="standard"
            placeholder="Ask anything… (Shift+Enter for new line)"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKey}
            disabled={loading}
            InputProps={{ disableUnderline: true, style: { color: '#e8e9ee', fontFamily: "'Inter'", fontSize: '14.5px', lineHeight: 1.6 } }}
            inputProps={{ style: { padding: '4px 0' } }}
          />
          <IconButton onClick={handleSend} disabled={loading || !input.trim()}
            sx={{ mb: 0.5, flexShrink: 0, width: 34, height: 34, bgcolor: input.trim() && !loading ? '#7c5cfc' : 'rgba(255,255,255,0.06)', borderRadius: '8px', transition: 'all 0.15s', '&:hover': { bgcolor: input.trim() && !loading ? '#6d4fe8' : 'rgba(255,255,255,0.08)' }, '&.Mui-disabled': { bgcolor: 'rgba(255,255,255,0.04)' } }}>
            <ArrowUpwardIcon sx={{ fontSize: 18, color: input.trim() && !loading ? '#fff' : '#5c5f6e' }} />
          </IconButton>
        </Box>
        <Typography sx={{ fontSize: '11px', color: '#5c5f6e', textAlign: 'center', mt: 1 }}>
          MultiModelAI may make mistakes. Review important outputs.
        </Typography>
      </Box>
    </Box>
  );
}
