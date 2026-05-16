// src/components/AgentSelector.jsx
import React, { useState, useEffect } from 'react';
import { List, ListItemButton, ListItemText, Typography } from '@mui/material';

const agents = [
  { id: 'development',   label: 'Development Agent'   },
  { id: 'cybersecurity', label: 'Cybersecurity Agent' },
  { id: 'research',      label: 'Research Agent'      },
];

const AgentSelector = ({ onAgentChange }) => {
  const [selected, setSelected] = useState('development');

  useEffect(() => {
    localStorage.setItem('selectedAgent', 'development');
  }, []);

  const handleSelect = (id) => {
    setSelected(id);
    localStorage.setItem('selectedAgent', id);
    if (onAgentChange) onAgentChange(id);
  };

  return (
    <List sx={{ p: 0 }}>
      {agents.map((agent) => {
        const isSelected = selected === agent.id;
        return (
          <ListItemButton
            key={agent.id}
            selected={isSelected}
            onClick={() => handleSelect(agent.id)}
            sx={{ py: 0.5 }}
          >
            <Typography sx={{ color: isSelected ? '#00ff66' : '#8b949e', mr: 1, minWidth: 28 }}>
              {isSelected ? '[X]' : '[ ]'}
            </Typography>
            <ListItemText
              primary={agent.label}
              primaryTypographyProps={{
                style: {
                  color: isSelected ? '#00ff66' : '#e6edf3',
                  fontFamily: "'Fira Code', monospace",
                  fontSize: '13px',
                }
              }}
            />
          </ListItemButton>
        );
      })}
    </List>
  );
};

export default AgentSelector;
