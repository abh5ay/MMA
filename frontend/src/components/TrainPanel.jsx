// src/components/TrainPanel.jsx
// Model Training UI — paste dataset URL, pick target column, watch live training log
import React, { useState, useRef, useEffect } from 'react';
import {
  Box, Typography, TextField, Button, LinearProgress,
  Chip, Divider, Alert, Paper, MenuItem, Select,
  FormControl, InputLabel, CircularProgress,
} from '@mui/material';
import PlayArrowIcon     from '@mui/icons-material/PlayArrow';
import ModelTrainingIcon from '@mui/icons-material/ModelTraining';
import MemoryIcon        from '@mui/icons-material/Memory';
import CheckCircleIcon   from '@mui/icons-material/CheckCircle';
import ErrorIcon         from '@mui/icons-material/Error';

const API = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

const STATUS_COLOR = {
  queued:        '#fbbf24',
  downloading:   '#38bdf8',
  loading:       '#38bdf8',
  preprocessing: '#a78bfa',
  training:      '#7c5cfc',
  done:          '#37d399',
  error:         '#f87272',
};

export default function TrainPanel() {
  const [datasetUrl,    setDatasetUrl]    = useState('');
  const [targetCol,     setTargetCol]     = useState('');
  const [modelName,     setModelName]     = useState('my_model');
  const [taskType,      setTaskType]      = useState('auto');
  const [jobId,         setJobId]         = useState(null);
  const [job,           setJob]           = useState(null);
  const [loading,       setLoading]       = useState(false);
  const [models,        setModels]        = useState([]);
  const [predFeatures,  setPredFeatures]  = useState({});
  const [predResult,    setPredResult]    = useState(null);
  const [selectedModel, setSelectedModel] = useState('');
  const pollRef = useRef(null);
  const logRef  = useRef(null);

  // Poll training status
  useEffect(() => {
    if (!jobId) return;
    pollRef.current = setInterval(async () => {
      try {
        const r = await fetch(`${API}/api/train/status/${jobId}`);
        const data = await r.json();
        setJob(data);
        if (data.status === 'done' || data.status === 'error') {
          clearInterval(pollRef.current);
          setLoading(false);
          fetchModels();
        }
      } catch {}
    }, 1500);
    return () => clearInterval(pollRef.current);
  }, [jobId]);

  // Auto-scroll log
  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [job?.log]);

  const fetchModels = async () => {
    try {
      const r = await fetch(`${API}/api/train/list`);
      const d = await r.json();
      setModels(d.models || []);
    } catch {}
  };

  useEffect(() => { fetchModels(); }, []);

  const startTraining = async () => {
    if (!datasetUrl.trim()) return;
    setLoading(true);
    setJob(null);
    setPredResult(null);
    try {
      const r = await fetch(`${API}/api/train`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dataset_url:   datasetUrl.trim(),
          target_column: targetCol.trim() || null,
          model_type:    taskType,
          model_name:    modelName.trim() || 'my_model',
        }),
      });
      const d = await r.json();
      setJobId(d.job_id);
    } catch (e) {
      setLoading(false);
      alert('Failed to start training: ' + e.message);
    }
  };

  const runPredict = async () => {
    if (!selectedModel) return;
    try {
      const r = await fetch(`${API}/api/train/predict/${selectedModel}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_name: selectedModel, input_data: predFeatures }),
      });
      const d = await r.json();
      setPredResult(d);
    } catch (e) {
      alert('Prediction failed: ' + e.message);
    }
  };

  const selectedMeta = models.find(m => m.model_name === selectedModel);

  return (
    <Box sx={{ flex: 1, overflowY: 'auto', p: 3, bgcolor: 'var(--bg-main)' }}>

      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 3 }}>
        <ModelTrainingIcon sx={{ color: '#7c5cfc', fontSize: 28 }} />
        <Box>
          <Typography sx={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-1)' }}>
            ML Model Trainer
          </Typography>
          <Typography sx={{ fontSize: '12px', color: 'var(--text-3)' }}>
            Paste a dataset URL → auto-train → get a live prediction API
          </Typography>
        </Box>
      </Box>

      {/* Training Form */}
      <Paper sx={{ p: 2.5, bgcolor: 'rgba(124,92,252,0.06)', border: '1px solid rgba(124,92,252,0.2)', borderRadius: '12px', mb: 3 }}>
        <Typography sx={{ fontSize: '13px', fontWeight: 600, color: '#a78bfa', mb: 2 }}>
          🗂️ Dataset Configuration
        </Typography>

        <TextField
          fullWidth label="Dataset URL (CSV / JSON)" variant="outlined" size="small"
          value={datasetUrl} onChange={e => setDatasetUrl(e.target.value)}
          placeholder="https://example.com/iris.csv"
          sx={{ mb: 2, '& .MuiOutlinedInput-root': { color: 'var(--text-1)', '& fieldset': { borderColor: 'rgba(255,255,255,0.15)' } }, '& label': { color: 'var(--text-3)' } }}
        />

        <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap' }}>
          <TextField
            label="Target Column (optional)" variant="outlined" size="small"
            value={targetCol} onChange={e => setTargetCol(e.target.value)}
            placeholder="auto-detect"
            sx={{ flex: 1, minWidth: 160, '& .MuiOutlinedInput-root': { color: 'var(--text-1)', '& fieldset': { borderColor: 'rgba(255,255,255,0.15)' } }, '& label': { color: 'var(--text-3)' } }}
          />
          <TextField
            label="Model Name" variant="outlined" size="small"
            value={modelName} onChange={e => setModelName(e.target.value)}
            sx={{ flex: 1, minWidth: 140, '& .MuiOutlinedInput-root': { color: 'var(--text-1)', '& fieldset': { borderColor: 'rgba(255,255,255,0.15)' } }, '& label': { color: 'var(--text-3)' } }}
          />
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel sx={{ color: 'var(--text-3)' }}>Task Type</InputLabel>
            <Select value={taskType} label="Task Type" onChange={e => setTaskType(e.target.value)}
              sx={{ color: 'var(--text-1)', '& .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(255,255,255,0.15)' } }}>
              <MenuItem value="auto">Auto Detect</MenuItem>
              <MenuItem value="classification">Classification</MenuItem>
              <MenuItem value="regression">Regression</MenuItem>
            </Select>
          </FormControl>
        </Box>

        <Button
          variant="contained" startIcon={loading ? <CircularProgress size={14} sx={{ color: '#fff' }} /> : <PlayArrowIcon />}
          onClick={startTraining} disabled={loading || !datasetUrl.trim()}
          sx={{ bgcolor: '#7c5cfc', '&:hover': { bgcolor: '#6d4fe8' }, textTransform: 'none', fontWeight: 700, borderRadius: '8px', px: 3 }}
        >
          {loading ? 'Training…' : 'Start Training'}
        </Button>

        {/* Quick dataset examples */}
        <Box sx={{ mt: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          <Typography sx={{ fontSize: '11px', color: 'var(--text-3)', alignSelf: 'center' }}>Quick:</Typography>
          {[
            { label: 'Iris', url: 'https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv' },
            { label: 'Titanic', url: 'https://raw.githubusercontent.com/datasciencedojo/datasets/master/titanic.csv' },
            { label: 'Boston Housing', url: 'https://raw.githubusercontent.com/selva86/datasets/master/BostonHousing.csv' },
          ].map(d => (
            <Chip key={d.label} label={d.label} size="small" onClick={() => setDatasetUrl(d.url)}
              sx={{ fontSize: '10px', cursor: 'pointer', bgcolor: 'rgba(124,92,252,0.15)', color: '#c4b5fd',
                '&:hover': { bgcolor: 'rgba(124,92,252,0.3)' } }} />
          ))}
        </Box>
      </Paper>

      {/* Training Log */}
      {job && (
        <Paper sx={{ p: 2, bgcolor: 'rgba(0,0,0,0.3)', border: `1px solid ${STATUS_COLOR[job.status] || '#444'}`, borderRadius: '12px', mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1.5 }}>
            {job.status === 'done'  && <CheckCircleIcon sx={{ color: '#37d399', fontSize: 18 }} />}
            {job.status === 'error' && <ErrorIcon sx={{ color: '#f87272', fontSize: 18 }} />}
            {!['done','error'].includes(job.status) && <CircularProgress size={16} sx={{ color: STATUS_COLOR[job.status] }} />}
            <Typography sx={{ fontSize: '13px', fontWeight: 600, color: STATUS_COLOR[job.status] }}>
              {job.status.toUpperCase()}
            </Typography>
          </Box>

          {!['done','error'].includes(job.status) && (
            <LinearProgress variant="indeterminate"
              sx={{ mb: 1.5, borderRadius: '4px', bgcolor: 'rgba(255,255,255,0.07)',
                '& .MuiLinearProgress-bar': { bgcolor: STATUS_COLOR[job.status] } }} />
          )}

          <Box ref={logRef} sx={{ maxHeight: 200, overflowY: 'auto', fontFamily: 'monospace', fontSize: '12px', color: '#ccc' }}>
            {(job.log || []).map((line, i) => (
              <Box key={i} sx={{ py: 0.3, borderBottom: '1px solid rgba(255,255,255,0.04)' }}>{line}</Box>
            ))}
          </Box>

          {job.status === 'done' && job.metrics && (
            <Box sx={{ mt: 2 }}>
              <Typography sx={{ fontSize: '12px', fontWeight: 600, color: '#37d399', mb: 1 }}>
                🏆 Best: {job.best}
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                {Object.entries(job.metrics || {}).map(([name, score]) => (
                  <Chip key={name} size="small"
                    label={`${name}: ${Object.values(score)[0]}`}
                    sx={{ fontSize: '10px', bgcolor: 'rgba(55,211,153,0.1)', color: '#37d399' }} />
                ))}
              </Box>
            </Box>
          )}

          {job.status === 'error' && (
            <Alert severity="error" sx={{ mt: 1, fontSize: '12px' }}>{job.error}</Alert>
          )}
        </Paper>
      )}

      {/* Prediction Panel */}
      {models.length > 0 && (
        <Paper sx={{ p: 2.5, bgcolor: 'rgba(55,211,153,0.04)', border: '1px solid rgba(55,211,153,0.2)', borderRadius: '12px' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
            <MemoryIcon sx={{ color: '#37d399', fontSize: 18 }} />
            <Typography sx={{ fontSize: '13px', fontWeight: 600, color: '#37d399' }}>
              Trained Models — Live Prediction
            </Typography>
          </Box>

          <FormControl size="small" fullWidth sx={{ mb: 2 }}>
            <InputLabel sx={{ color: 'var(--text-3)' }}>Select Model</InputLabel>
            <Select value={selectedModel} label="Select Model" onChange={e => { setSelectedModel(e.target.value); setPredResult(null); setPredFeatures({}); }}
              sx={{ color: 'var(--text-1)', '& .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(255,255,255,0.15)' } }}>
              {models.map(m => (
                <MenuItem key={m.model_name} value={m.model_name}>
                  {m.model_name} ({m.task} · {m.best_model})
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {selectedMeta && (
            <>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
                {selectedMeta.features.map(feat => (
                  <TextField key={feat} label={feat} variant="outlined" size="small"
                    value={predFeatures[feat] || ''}
                    onChange={e => setPredFeatures(p => ({ ...p, [feat]: e.target.value }))}
                    sx={{ width: 130, '& .MuiOutlinedInput-root': { color: 'var(--text-1)', '& fieldset': { borderColor: 'rgba(255,255,255,0.15)' } }, '& label': { color: 'var(--text-3)', fontSize: '11px' } }}
                  />
                ))}
              </Box>

              <Button variant="outlined" onClick={runPredict} size="small"
                sx={{ borderColor: '#37d399', color: '#37d399', textTransform: 'none', '&:hover': { borderColor: '#37d399', bgcolor: 'rgba(55,211,153,0.08)' } }}>
                Run Prediction
              </Button>

              {predResult && (
                <Box sx={{ mt: 2, p: 2, bgcolor: 'rgba(55,211,153,0.08)', borderRadius: '8px', border: '1px solid rgba(55,211,153,0.2)' }}>
                  <Typography sx={{ fontSize: '13px', color: '#37d399', fontWeight: 700 }}>
                    Prediction: <span style={{ fontSize: '16px' }}>{String(predResult.prediction)}</span>
                  </Typography>
                  {predResult.probabilities && (
                    <Box sx={{ mt: 1 }}>
                      {Object.entries(predResult.probabilities).map(([cls, prob]) => (
                        <Box key={cls} sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                          <Typography sx={{ fontSize: '11px', color: '#ccc', width: 100, flexShrink: 0 }}>{cls}</Typography>
                          <LinearProgress variant="determinate" value={prob * 100}
                            sx={{ flex: 1, borderRadius: '4px', bgcolor: 'rgba(255,255,255,0.07)',
                              '& .MuiLinearProgress-bar': { bgcolor: '#7c5cfc' } }} />
                          <Typography sx={{ fontSize: '11px', color: '#ccc', width: 42, textAlign: 'right' }}>
                            {(prob * 100).toFixed(1)}%
                          </Typography>
                        </Box>
                      ))}
                    </Box>
                  )}
                </Box>
              )}
            </>
          )}
        </Paper>
      )}
    </Box>
  );
}
