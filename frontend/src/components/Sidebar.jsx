// src/components/Sidebar.jsx — Clean modern sidebar
import React, { useState, useEffect } from 'react';
import { Box, Typography, Tooltip } from '@mui/material';
import SmartToyOutlinedIcon from '@mui/icons-material/SmartToyOutlined';
import CodeOutlinedIcon from '@mui/icons-material/CodeOutlined';
import SecurityOutlinedIcon from '@mui/icons-material/SecurityOutlined';
import SearchOutlinedIcon from '@mui/icons-material/SearchOutlined';
import AutoFixHighOutlinedIcon from '@mui/icons-material/AutoFixHighOutlined';

// ── Agents ──────────────────────────────────────────────────────────────────
const AGENTS = [
  { id: 'development',   label: 'Developer',      icon: <CodeOutlinedIcon fontSize="small" />,     color: '#60a5fa' },
  { id: 'cybersecurity', label: 'Cybersecurity',  icon: <SecurityOutlinedIcon fontSize="small" />, color: '#f87272' },
  { id: 'research',      label: 'Research',       icon: <SearchOutlinedIcon fontSize="small" />,   color: '#37d399' },
];

// ── Models ───────────────────────────────────────────────────────────────────
const MODELS = [
  { id: 'api:hf',           label: 'HuggingFace',          sub: 'Qwen-2.5 72B',         dot: '#37d399' },
  { id: 'api:nvidia',       label: 'NVIDIA NIM',           sub: 'Gemma-4 31B',          dot: '#76b900' },
  { id: 'api:nvidia-mistral',label: 'NVIDIA Mistral',       sub: 'Mistral Large',        dot: '#76b900' },
  { id: 'api:grok',         label: 'Grok 3',               sub: 'xAI · Fast',           dot: '#e879f9' },
  { id: 'api:gpt-oss',      label: 'GPT-OSS 120B',         sub: 'HuggingFace · OpenAI', dot: '#38bdf8' },
  { id: 'api:together',     label: 'DeepSeek Coder',       sub: 'Together · 33B',       dot: '#fb923c' },
  { id: 'api:cerebras',     label: 'Cerebras',             sub: 'Llama-3.3 70B · Fast', dot: '#f43f5e' },
  { id: 'local:qwen3-cyber',label: 'Qwen3-14B Cyber',      sub: 'LoRA · Local',         dot: '#bf5fff' },
  { id: 'local:dan-qwen',   label: 'DAN-Qwen3',            sub: '1.7B · Unfiltered',    dot: '#f87272' },
  { id: 'local:ollama',     label: 'Ollama',               sub: 'Local',                dot: '#fbbf24' },
  { id: 'api:gpt',          label: 'OpenAI',               sub: 'GPT-4o-mini',          dot: '#60a5fa' },
  { id: 'api:gemini',       label: 'Gemini',               sub: 'Google 2.0 Flash',     dot: '#60a5fa' },
];

// ── Pill component ───────────────────────────────────────────────────────────
function Pill({ active, onClick, children }) {
  return (
    <Box
      onClick={onClick}
      sx={{
        px: 1.5, py: 1,
        borderRadius: '8px',
        cursor: 'pointer',
        display: 'flex', alignItems: 'center', gap: 1.2,
        bgcolor: active ? 'rgba(124,92,252,0.15)' : 'transparent',
        border: active ? '1px solid rgba(124,92,252,0.4)' : '1px solid transparent',
        transition: 'all 0.15s ease',
        '&:hover': { bgcolor: active ? 'rgba(124,92,252,0.2)' : 'rgba(255,255,255,0.04)' },
      }}
    >
      {children}
    </Box>
  );
}

// ── Section label ────────────────────────────────────────────────────────────
function SectionLabel({ children }) {
  return (
    <Typography sx={{ fontSize: '10px', fontWeight: 600, color: 'var(--text-3)', letterSpacing: '0.1em', textTransform: 'uppercase', px: 1.5, mb: 0.5, mt: 2 }}>
      {children}
    </Typography>
  );
}

export default function Sidebar({ onSelect }) {
  const [agent, setAgent] = useState('development');
  const [model, setModel] = useState('api:hf');

  useEffect(() => {
    localStorage.setItem('selectedAgent', 'development');
    localStorage.setItem('selectedModel', 'api:hf');
  }, []);

  const selectAgent = (id) => { setAgent(id); localStorage.setItem('selectedAgent', id); if (onSelect) onSelect(); };
  const selectModel = (id) => { setModel(id); localStorage.setItem('selectedModel', id); if (onSelect) onSelect(); };

  return (
    <Box sx={{
      width: 220,
      flexShrink: 0,
      bgcolor: 'var(--bg-sidebar)',
      borderRight: '1px solid var(--border)',
      display: 'flex',
      flexDirection: 'column',
      py: 2,
      px: 1,
      overflowY: 'auto',
    }}>
      {/* Logo */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.2, px: 1.5, mb: 2 }}>
        <Box sx={{
          width: 30, height: 30, borderRadius: '8px',
          background: 'linear-gradient(135deg, #7c5cfc, #5eead4)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <SmartToyOutlinedIcon sx={{ fontSize: 18, color: '#fff' }} />
        </Box>
        <Typography sx={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-1)' }}>
          MultiModelAI
        </Typography>
      </Box>

      {/* Agents */}
      <SectionLabel>Agent</SectionLabel>
      {AGENTS.map(a => (
        <Pill key={a.id} active={agent === a.id} onClick={() => selectAgent(a.id)}>
          <Box sx={{ color: agent === a.id ? a.color : 'var(--text-3)', display: 'flex' }}>{a.icon}</Box>
          <Typography sx={{ fontSize: '13.5px', fontWeight: agent === a.id ? 600 : 400, color: agent === a.id ? 'var(--text-1)' : 'var(--text-2)' }}>
            {a.label}
          </Typography>
        </Pill>
      ))}

      {/* Models */}
      <SectionLabel>Model</SectionLabel>
      {MODELS.map(m => (
        <Pill key={m.id} active={model === m.id} onClick={() => selectModel(m.id)}>
          <Box sx={{ width: 7, height: 7, borderRadius: '50%', bgcolor: m.dot, flexShrink: 0 }} />
          <Box>
            <Typography sx={{ fontSize: '13px', fontWeight: model === m.id ? 600 : 400, color: model === m.id ? 'var(--text-1)' : 'var(--text-2)', lineHeight: 1.2 }}>
              {m.label}
            </Typography>
            <Typography sx={{ fontSize: '10.5px', color: 'var(--text-3)', lineHeight: 1 }}>
              {m.sub}
            </Typography>
          </Box>
        </Pill>
      ))}

      {/* Agentic badge */}
      <Box sx={{ mt: 'auto', mx: 1.5, mb: 1 }}>
        <Box sx={{
          display: 'flex', alignItems: 'center', gap: 1,
          bgcolor: 'rgba(124,92,252,0.1)', borderRadius: '8px',
          border: '1px solid rgba(124,92,252,0.25)', px: 1.5, py: 1,
        }}>
          <AutoFixHighOutlinedIcon sx={{ fontSize: 14, color: '#7c5cfc' }} />
          <Box>
            <Typography sx={{ fontSize: '11px', fontWeight: 600, color: '#7c5cfc', lineHeight: 1.2 }}>Agentic Mode</Typography>
            <Typography sx={{ fontSize: '10px', color: 'var(--text-3)' }}>Tools · Code · Files</Typography>
          </Box>
        </Box>
      </Box>
    </Box>
  );
}
