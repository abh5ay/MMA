// src/components/ModelSelector.jsx
import React, { useState, useEffect } from 'react';
import { List, ListItemButton, ListItemText, Typography, Box } from '@mui/material';

const defaultModels = [
  { id: 'api:hf',          label: 'HuggingFace (Free)',        badge: 'DEFAULT', color: '#00ff66' },
  { id: 'api:nvidia',      label: 'Gemma-4 31B · NVIDIA NIM',  badge: 'NIM',     color: '#76b900' },
  { id: 'local:qwen3-cyber', label: 'Qwen3-14B Cyber LoRA',   badge: 'LOCAL',   color: '#bf5fff' }, // purple = cyber specialist
  { id: 'local:dan-qwen',  label: 'DAN-Qwen3 1.7B',           badge: 'LOCAL',   color: '#ff4444' },
  { id: 'local:ollama',    label: 'Ollama (Local)',            badge: 'LOCAL',   color: '#ffbd2e' },
  { id: 'api:gpt',         label: 'OpenAI GPT-4o-mini',       badge: 'API',     color: '#00f0ff' },
  { id: 'api:gemini',      label: 'Google Gemini 2.0',        badge: 'API',     color: '#00f0ff' },
];

const ModelSelector = ({ onModelChange }) => {
  const [selected, setSelected] = useState('api:hf');

  useEffect(() => {
    localStorage.setItem('selectedModel', 'api:hf');
  }, []);

  const handleSelect = (id) => {
    setSelected(id);
    localStorage.setItem('selectedModel', id);
    if (onModelChange) onModelChange(id);
  };

  return (
    <List sx={{ p: 0 }}>
      {defaultModels.map((model) => {
        const isSelected = selected === model.id;
        return (
          <ListItemButton
            key={model.id}
            selected={isSelected}
            onClick={() => handleSelect(model.id)}
            sx={{ py: 0.5, alignItems: 'flex-start' }}
          >
            <Typography sx={{ color: isSelected ? model.color : '#8b949e', mr: 1, minWidth: 28, mt: 0.2 }}>
              {isSelected ? '[X]' : '[ ]'}
            </Typography>
            <Box flexGrow={1}>
              <ListItemText
                primary={model.label}
                primaryTypographyProps={{
                  style: {
                    color: isSelected ? model.color : '#e6edf3',
                    fontFamily: "'Fira Code', monospace",
                    fontSize: '12.5px',
                    lineHeight: 1.3,
                  }
                }}
              />
            </Box>
            <Typography sx={{
              fontSize: '10px',
              color: isSelected ? model.color : '#444',
              fontFamily: "'Fira Code', monospace",
              alignSelf: 'center',
              ml: 0.5,
            }}>
              {model.badge}
            </Typography>
          </ListItemButton>
        );
      })}
    </List>
  );
};

export default ModelSelector;
