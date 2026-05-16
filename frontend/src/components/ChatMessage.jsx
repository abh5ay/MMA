// src/components/ChatMessage.jsx — Clean message bubbles with agentic steps
import React from 'react';
import { Box, Typography, Avatar } from '@mui/material';
import SmartToyOutlinedIcon from '@mui/icons-material/SmartToyOutlined';
import PersonOutlineIcon from '@mui/icons-material/PersonOutline';
import TypingMessage from './TypingMessage';
import { ToolCall, ToolResult } from './ToolStep';

export default function ChatMessage({ role, content, steps, animate }) {
  const isUser = role === 'user';

  return (
    <Box sx={{
      display: 'flex',
      gap: 1.5,
      px: { xs: 1, sm: 2 },
      py: 1.5,
      animation: 'fadeSlideUp 0.25s ease',
      alignItems: 'flex-start',
    }}>
      {/* Avatar */}
      <Avatar sx={{
        width: 30, height: 30, flexShrink: 0, mt: 0.3,
        bgcolor: isUser ? 'rgba(255,255,255,0.08)' : 'rgba(124,92,252,0.2)',
        border: isUser ? '1px solid rgba(255,255,255,0.1)' : '1px solid rgba(124,92,252,0.3)',
      }}>
        {isUser
          ? <PersonOutlineIcon sx={{ fontSize: 16, color: 'var(--text-2)' }} />
          : <SmartToyOutlinedIcon sx={{ fontSize: 16, color: '#7c5cfc' }} />
        }
      </Avatar>

      {/* Content */}
      <Box sx={{ flex: 1, minWidth: 0, maxWidth: '100%' }}>
        {/* Role label */}
        <Typography sx={{ fontSize: '12px', fontWeight: 600, color: isUser ? 'var(--text-2)' : '#7c5cfc', mb: 0.5 }}>
          {isUser ? 'You' : 'MultiModelAI'}
        </Typography>

        {/* Agentic steps (tool calls / results) */}
        {steps && steps.length > 0 && (
          <Box sx={{ mb: 1 }}>
            {steps.map((step, i) => {
              if (step.type === 'tool')
                return <ToolCall key={i} tool={step.tool} input={step.content} />;
              if (step.type === 'result')
                return <ToolResult key={i} tool={step.tool} content={step.content} />;
              return null;
            })}
          </Box>
        )}

        {/* Message text */}
        {isUser ? (
          <Typography sx={{
            color: 'var(--text-1)', fontSize: '14.5px', lineHeight: 1.7,
            whiteSpace: 'pre-wrap', fontFamily: "'Inter'",
          }}>
            {content}
          </Typography>
        ) : (
          <TypingMessage content={content} animate={animate} />
        )}
      </Box>
    </Box>
  );
}
