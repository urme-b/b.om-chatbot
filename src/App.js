import React, { useState, useRef, useEffect } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { 
  Box, IconButton, TextField, Avatar, Paper, Button, 
  Slide, Fade, Typography, Badge
} from '@mui/material';
import {
  Send as SendIcon,
  Close as CloseIcon,
  Chat as ChatIcon
} from '@mui/icons-material';
import { chatWithBackend } from './knowledgeBase';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Chip } from '@mui/material';

// Theme configuration
const theme = createTheme({
  palette: {
    primary: { main: '#1976d2' },
    secondary: { main: '#f50057' },
    background: { default: '#f5f5f5' },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: '20px',
        },
      },
    },
  },
});

function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [messages, setMessages] = useState([
    { 
      id: Date.now(), 
      text: '👋 Welcome to b.om Institute! How can I help you today?', 
      sender: 'bot',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Handle sending a new message
  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;
  
    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  
    const userMessage = {
      id: Date.now(),
      text: input,
      sender: 'user',
      timestamp: now
    };
    const nextUiMessages = [...messages, userMessage];
    setMessages(nextUiMessages);
    setInput('');
    setIsTyping(true);
  
    try {
      const wire = nextUiMessages.map(m => ({
        role: m.sender === 'user' ? 'user' : 'assistant',
        content: m.text
      }));
  
      const { content, sources } = await chatWithBackend(wire);
  
      const botMessage = {
        id: Date.now() + 1,
        text: content,          // markdown string
        sources,                // optional array
        sender: 'bot',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, botMessage]);
    } catch (err) {
      setMessages(prev => [
        ...prev,
        { id: Date.now() + 2, text: `Error: ${err.message}`, sender: 'bot', timestamp: now }
      ]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <Box sx={{ position: 'fixed', bottom: 24, right: 24, zIndex: 9999 }}>
      <Fade in={!open}>
        <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
          <Badge color="error" variant="dot" overlap="circular">
            <Button
              variant="contained"
              color="primary"
              onClick={() => setOpen(true)}
              sx={{
                borderRadius: '50%',
                minWidth: '60px',
                height: '60px',
                boxShadow: 3,
                '&:hover': {
                  transform: 'scale(1.05)',
                  transition: 'transform 0.2s',
                },
              }}
            >
              <ChatIcon sx={{ fontSize: 28 }} />
            </Button>
          </Badge>
        </Box>
      </Fade>

      <Slide direction="up" in={open} mountOnEnter unmountOnExit>
        <Paper
          elevation={6}
          sx={{
            width: 350,
            maxWidth: '90vw',
            height: 500,
            maxHeight: '80vh',
            display: 'flex',
            flexDirection: 'column',
            borderRadius: 2,
            overflow: 'hidden',
            bgcolor: 'background.paper',
          }}
        >
          {/* Header */}
          <Box
            sx={{
              bgcolor: 'primary.main',
              color: 'white',
              p: 2,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Avatar sx={{ bgcolor: 'white', color: 'primary.main', width: 32, height: 32 }}>
                <ChatIcon fontSize="small" />
              </Avatar>
              <Typography variant="subtitle1" fontWeight="medium">
                b.om Assistant
              </Typography>
            </Box>
            <IconButton
              size="small"
              onClick={() => setOpen(false)}
              sx={{ color: 'white' }}
            >
              <CloseIcon />
            </IconButton>
          </Box>

          {/* Messages */}
          <Box
            sx={{
              flex: 1,
              p: 2,
              overflowY: 'auto',
              display: 'flex',
              flexDirection: 'column',
              gap: 1,
              '&::-webkit-scrollbar': {
                width: '6px',
              },
              '&::-webkit-scrollbar-thumb': {
                backgroundColor: 'rgba(0,0,0,0.2)',
                borderRadius: '3px',
              },
            }}
          >
            {messages.map((message) => (
              <Box
                key={message.id}
                sx={{
                  alignSelf: message.sender === 'user' ? 'flex-end' : 'flex-start',
                  maxWidth: '80%',
                }}
              >
                <Paper
                  elevation={0}
                  sx={{
                    p: 1.5,
                    borderRadius: 2,
                    bgcolor: message.sender === 'user' ? 'primary.main' : 'grey.100',
                    color: message.sender === 'user' ? 'white' : 'text.primary',
                    whiteSpace: 'pre-line',
                    lineHeight: 1.4,
                  }}
                >
                  <Typography variant="body2" component="div" sx={{ '& p': { m: 0 }, '& ul, & ol': { pl: 2, my: 0.5 } }}>
                   <ReactMarkdown remarkPlugins={[remarkGfm]}>
                     {message.text}
                   </ReactMarkdown>
                 </Typography>
                 {message.sender === 'bot' && Array.isArray(message.sources) && message.sources.length > 0 && (
                   <Box sx={{ mt: 1, display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                     {message.sources.map((s, i) => (
                       <Chip key={i} label={s} size="small" variant="outlined" />
                     ))}
                   </Box>
                 )}
                  <Typography
                    variant="caption"
                    sx={{
                      display: 'block',
                      mt: 0.5,
                      textAlign: 'right',
                      opacity: 0.7,
                      fontSize: '0.65rem',
                      color: message.sender === 'user' ? 'rgba(255,255,255,0.8)' : 'text.secondary',
                    }}
                  >
                    {message.timestamp}
                  </Typography>
                </Paper>
              </Box>
            ))}
            {isTyping && (
              <Box
                sx={{
                  alignSelf: 'flex-start',
                  p: 1.5,
                  bgcolor: 'grey.100',
                  borderRadius: 2,
                  display: 'flex',
                  gap: 0.5,
                }}
              >
                {[1, 2, 3].map((dot) => (
                  <Box
                    key={dot}
                    sx={{
                      width: 8,
                      height: 8,
                      borderRadius: '50%',
                      bgcolor: 'text.secondary',
                      opacity: 0.6,
                      animation: 'pulse 1.4s infinite',
                      animationDelay: `${dot * 0.2}s`,
                      '@keyframes pulse': {
                        '0%, 100%': { opacity: 0.2 },
                        '50%': { opacity: 0.8 },
                      },
                    }}
                  />
                ))}
              </Box>
            )}
            <div ref={messagesEndRef} />
          </Box>

{/* Input Area */}
          <Box
            component="form"
            onSubmit={handleSendMessage}
            sx={{
              p: 2,
              borderTop: '1px solid',
              borderColor: 'divider',
              bgcolor: 'background.paper',
            }}
          >
            <Box sx={{ display: 'flex', gap: 1 }}>
              <TextField
                fullWidth
                variant="outlined"
                size="small"
                placeholder="Type your message..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={isTyping}
                sx={{
                  '& .MuiOutlinedInput-root': {
                    borderRadius: '20px',
                    bgcolor: 'background.paper',
                  },
                }}
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage(e);
                  }
                }}
              />
              <Button
                type="submit"
                variant="contained"
                color="primary"
                disabled={!input.trim() || isTyping}
                sx={{
                  minWidth: '40px',
                  width: '40px',
                  height: '40px',
                  borderRadius: '50%',
                }}
              >
                <SendIcon />
              </Button>
            </Box>

          </Box>
        </Paper>
      </Slide>
    </Box>
  );
}

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <ChatWidget />
    </ThemeProvider>
  );
}

export default App;
