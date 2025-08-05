import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  TextField,
  Button,
  Paper,
  Typography,
  CircularProgress,
  Card,
  CardContent,
  CardActions,
  Chip,
  Divider,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  Avatar,
  List,
  ListItem,
  ListItemText,
  Snackbar
} from '@mui/material';
import RealEstateService from '../services/realEstateService';

// === YOUR AGENT IMAGE URL HERE ===
const agentImageUrl = "https://i.postimg.cc/NGP1fMxM/logo.jpg";

const ChatInterface = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [setProperties] = useState([]);
  const [selectedProperty, setSelectedProperty] = useState(null);
  const [showPropertyDetails, setShowPropertyDetails] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });
  const [searchSuggestions, setSearchSuggestions] = useState([]);
  const [actionLoading, setActionLoading] = useState({});
  const [connectionStatus, setConnectionStatus] = useState('checking');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    const checkConnection = async () => {
      try {
        await RealEstateService.checkHealth();
        setConnectionStatus('connected');
      } catch (error) {
        setConnectionStatus('disconnected');
      }
    };

    checkConnection();
    
    const welcomeMessage = {
      id: 1,
      text: "👋 Welcome to AI Real Estate Assistant! I'm here to help you find your perfect home.\n\n🏠 I can help you with:\n• Property searches with smart filtering\n• Detailed amenities information\n• Price negotiations\n• Deal closing process\n\nTry asking: 'Find 2BHK apartments in Dallas under $500K'",
      sender: 'agent',
      timestamp: new Date().toISOString(),
      type: 'welcome'
    };
    
    setMessages([welcomeMessage]);
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = {
      id: Date.now(),
      text: input,
      sender: 'user',
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await RealEstateService.chatQuery(input);
      
      const agentMessage = {
        id: Date.now() + 1,
        text: response.message || 'I received your message',
        sender: 'agent',
        timestamp: response.timestamp || new Date().toISOString(),
        properties: response.data?.properties || [],
        type: response.data?.type || 'text'
      };

      setMessages(prev => [...prev, agentMessage]);
      
      if (response.data?.properties && response.data.properties.length > 0) {
        setProperties(response.data.properties);
      }

      if (response.data?.suggestions) {
        setSearchSuggestions(response.data.suggestions);
      }

    } catch (error) {
      const errorMessage = {
        id: Date.now() + 1,
        text: 'Sorry, I encountered an error. Please try again.',
        sender: 'agent',
        timestamp: new Date().toISOString(),
        type: 'error'
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handlePropertyAction = async (action, propertyId, data = {}) => {
    const actionKey = `${action}_${propertyId}`;
    setActionLoading(prev => ({ ...prev, [actionKey]: true }));

    try {
      let response;
      switch (action) {
        case 'amenities':
          response = await RealEstateService.getPropertyAmenities(propertyId);
          break;
        case 'negotiate':
          response = await RealEstateService.negotiatePrice(propertyId, data.offer);
          break;
        case 'finalize':
          response = await RealEstateService.finalizeDeal(propertyId, data);
          break;
        default:
          throw new Error(`Unknown action: ${action}`);
      }

      const agentMessage = {
        id: Date.now(),
        text: response.message || `${action} action completed`,
        sender: 'agent',
        timestamp: response.timestamp || new Date().toISOString(),
        type: action,
        data: response.data || {}
      };

      setMessages(prev => [...prev, agentMessage]);
      setSnackbar({ 
        open: true, 
        message: response.message || `${action} completed successfully`, 
        severity: 'success' 
      });

    } catch (error) {
      const errorMessage = {
        id: Date.now(),
        text: `Sorry, I couldn't complete the ${action} action. Please try again.`,
        sender: 'agent',
        timestamp: new Date().toISOString(),
        type: 'error'
      };
      setMessages(prev => [...prev, errorMessage]);
      setSnackbar({ 
        open: true, 
        message: `Failed to ${action}. Please try again.`, 
        severity: 'error' 
      });
    } finally {
      setActionLoading(prev => ({ ...prev, [actionKey]: false }));
    }
  };

  const handleViewDetails = (property) => {
    setSelectedProperty(property);
    setShowPropertyDetails(true);
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatText = (text) => {
    return text.split('\n').map((line, index) => (
      <React.Fragment key={index}>
        {line}
        {index < text.split('\n').length - 1 && <br />}
      </React.Fragment>
    ));
  };

  const renderMessage = (message) => {
    const isUser = message.sender === 'user';
    
    return (
      <Box
        key={message.id}
        sx={{
          display: 'flex',
          justifyContent: isUser ? 'flex-end' : 'flex-start',
          mb: 2,
          alignItems: 'flex-start'
        }}
      >
        {/* AGENT AVATAR with IMAGE */}
        {!isUser && (
          <Avatar
            src={agentImageUrl}
            alt="Real Estate Agent"
            sx={{
              width: 32,
              height: 32,
              mr: 1,
              fontSize: '0.8rem',
              bgcolor: '#1976d2'
            }}
          />
        )}
          
        <Box sx={{ maxWidth: '70%', minWidth: '200px' }}>
          <Paper
            elevation={0}
            sx={{
              p: 2,
              bgcolor: isUser ? '#0066FF' : '#F8F9FA',
              color: isUser ? 'white' : '#1A1D1F',
              borderRadius: '12px',
              border: isUser ? 'none' : '1px solid #E9ECEF'
            }}
          >
            <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
              {formatText(message.text)}
            </Typography>
            
            <Typography
              variant="caption"
              sx={{
                mt: 1,
                display: 'block',
                opacity: 0.7,
                fontSize: '0.7rem'
              }}
            >
              {new Date(message.timestamp).toLocaleTimeString()}
            </Typography>
          </Paper>

          {message.properties && message.properties.length > 0 && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="h6" gutterBottom>
                Found Properties ({message.properties.length})
              </Typography>
              
              <Grid container spacing={2}>
                {message.properties.map((property) => (
                  <Grid item xs={12} key={property.id}>
                    <Card 
                      elevation={2}
                      sx={{ 
                        transition: 'all 0.2s',
                        '&:hover': { 
                          elevation: 4,
                          transform: 'translateY(-2px)'
                        }
                      }}
                    >
                      <CardContent>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                          <Typography variant="h6" component="h3">
                            {property.title || `${property.bedrooms}BR ${property.property_type}`}
                          </Typography>
                          <Chip 
                            label={formatCurrency(property.price)} 
                            color="primary" 
                            variant="filled"
                            sx={{ fontWeight: 'bold' }}
                          />
                        </Box>

                        <Typography color="text.secondary" gutterBottom>
                          📍 {property.location || property.address}
                        </Typography>

                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                          <Chip size="small" label={`${property.bedrooms} bed`} />
                          <Chip size="small" label={`${property.bathrooms} bath`} />
                          <Chip size="small" label={`${property.area || property.sqft} sqft`} />
                          <Chip size="small" label={property.property_type} />
                        </Box>

                        {property.description && (
                          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                            {property.description.length > 150 
                              ? `${property.description.substring(0, 150)}...` 
                              : property.description
                            }
                          </Typography>
                        )}
                      </CardContent>

                      <Divider />

                      <CardActions sx={{ p: 2, justifyContent: 'space-between', flexWrap: 'wrap', gap: 1 }}>
                        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                          <Button
                            size="small"
                            variant="outlined"
                            onClick={() => handleViewDetails(property)}
                          >
                            View Details
                          </Button>
                          
                          <Button
                            size="small"
                            variant="outlined"
                            onClick={() => handlePropertyAction('amenities', property.id)}
                            disabled={actionLoading[`amenities_${property.id}`]}
                          >
                            {actionLoading[`amenities_${property.id}`] ? (
                              <CircularProgress size={16} />
                            ) : (
                              '🏢 View Amenities'
                            )}
                          </Button>
                        </Box>

                        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                          <Button
                            size="small"
                            variant="contained"
                            color="secondary"
                            onClick={() => {
                              const offer = prompt(`Enter your offer for ${formatCurrency(property.price)}:`);
                              if (offer && !isNaN(offer)) {
                                handlePropertyAction('negotiate', property.id, { offer: parseInt(offer) });
                              }
                            }}
                            disabled={actionLoading[`negotiate_${property.id}`]}
                          >
                            {actionLoading[`negotiate_${property.id}`] ? (
                              <CircularProgress size={16} />
                            ) : (
                              'Negotiate'
                            )}
                          </Button>
                          
                          <Button
                            size="small"
                            variant="contained"
                            color="success"
                            onClick={() => handlePropertyAction('finalize', property.id)}
                            disabled={actionLoading[`finalize_${property.id}`]}
                          >
                            {actionLoading[`finalize_${property.id}`] ? (
                              <CircularProgress size={16} />
                            ) : (
                              'Finalize Deal'
                            )}
                          </Button>
                        </Box>
                      </CardActions>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </Box>
          )}

          {searchSuggestions.length > 0 && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                💡 Try these searches:
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {searchSuggestions.map((suggestion, index) => (
                  <Chip
                    key={index}
                    label={suggestion}
                    variant="outlined"
                    size="small"
                    onClick={() => setInput(suggestion)}
                    sx={{ cursor: 'pointer' }}
                  />
                ))}
              </Box>
            </Box>
          )}
        </Box>

        {/* USER AVATAR */}
        {isUser && (
          <Avatar
            sx={{
              bgcolor: '#4caf50',
              width: 32,
              height: 32,
              ml: 1,
              fontSize: '0.8rem'
            }}
          >
            U
          </Avatar>
        )}
      </Box>
    );
  };

  return (
    <Box sx={{ 
        width: '100%', 
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        bgcolor: '#F8F9FA'
      }}>
      {/* Connection Status */}
      <Box sx={{ 
        p: 2, 
        textAlign: 'right',
        borderBottom: '1px solid #E9ECEF'
      }}>
        <Chip 
          label={
            connectionStatus === 'connected' ? '🟢 Connected to AI Assistant' :
            connectionStatus === 'disconnected' ? '🔴 Connection Error' :
            '🟡 Connecting...'
          }
          color={
            connectionStatus === 'connected' ? 'success' :
            connectionStatus === 'disconnected' ? 'error' :
            'warning'
          }
          variant="outlined"
          size="small"
          sx={{ 
            bgcolor: '#fff',
            '& .MuiChip-label': { 
              fontWeight: 500,
              fontSize: '0.75rem'
            }
          }}
        />
      </Box>

      <Paper 
        elevation={0} 
        sx={{ 
          flex: 1,
          display: 'flex', 
          flexDirection: 'column',
          bgcolor: '#fff',
          borderRadius: 0
        }}>
        {/* Chat Header */}
        <Box sx={{ 
          p: 2, 
          bgcolor: '#fff', 
          borderBottom: '1px solid rgba(0, 0, 0, 0.12)',
          display: 'flex',
          alignItems: 'center',
          gap: 2
        }}>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h6" sx={{
              fontSize: '1rem',
              fontWeight: 500,
              color: '#1A1D1F',
              mb: 0.5
            }}>
              Quick Tips:
            </Typography>
            <Typography variant="body2" sx={{ 
              color: '#666',
              fontSize: '0.875rem'
            }}>
              Try "Find 3BHK apartments in downtown" or "Show amenities for property #123"
            </Typography>
          </Box>
          <Chip 
            icon={<span>🎯</span>}
            label="Start Property Search"
            color="primary"
            onClick={() => setInput('Help me find a property')}
            sx={{ 
              '& .MuiChip-label': { 
                fontWeight: 500 
              }
            }}
          />
        </Box>

        {/* Messages Area */}
        <Box
          sx={{
            flex: 1,
            overflow: 'auto',
            p: 3,
            bgcolor: '#fff',
            '&::-webkit-scrollbar': {
              width: '6px',
            },
            '&::-webkit-scrollbar-track': {
              background: '#F8F9FA',
              borderRadius: '3px',
            },
            '&::-webkit-scrollbar-thumb': {
              background: '#E9ECEF',
              borderRadius: '3px',
            },
            '&::-webkit-scrollbar-thumb:hover': {
              background: '#DEE2E6',
            },
          }}
        >
          {messages.map(renderMessage)}
          
          {loading && (
            <Box sx={{ display: 'flex', justifyContent: 'flex-start', mb: 2 }}>
              {/* AGENT AVATAR with IMAGE during "thinking" */}
              <Avatar
                src={agentImageUrl}
                alt="Real Estate Agent"
                sx={{ bgcolor: '#1976d2', width: 32, height: 32, mr: 1 }}
              />
              <Paper
                elevation={1}
                sx={{
                  p: 2,
                  bgcolor: '#f5f5f5',
                  borderRadius: '18px 18px 18px 4px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1
                }}
              >
                <CircularProgress size={16} />
                <Typography variant="body2">
                  AI is thinking...
                </Typography>
              </Paper>
            </Box>
          )}
          
          <div ref={messagesEndRef} />
        </Box>

        {/* Input Area */}
        <Divider />
        <Box 
          component="form" 
          onSubmit={handleSubmit} 
          sx={{ 
            p: 3,
            borderTop: '1px solid #E9ECEF',
            bgcolor: '#fff'
          }}
        >
          <Box sx={{ display: 'flex', gap: 2 }}>
            <TextField
              fullWidth
              variant="outlined"
              placeholder="Ask me about properties, neighborhoods, prices..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={loading || connectionStatus !== 'connected'}
              size="small"
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: '8px',
                  backgroundColor: '#F8F9FA',
                  '& fieldset': {
                    borderColor: '#E9ECEF',
                  },
                  '&:hover fieldset': {
                    borderColor: '#DEE2E6',
                  },
                  '&.Mui-focused fieldset': {
                    borderColor: '#0066FF',
                  }
                },
                '& .MuiInputBase-input': {
                  color: '#1A1D1F',
                }
              }}
            />
            <Button
              type="submit"
              variant="contained"
              disabled={loading || !input.trim() || connectionStatus !== 'connected'}
              sx={{
                borderRadius: '8px',
                minWidth: '100px',
                px: 3,
                bgcolor: '#0066FF',
                '&:hover': {
                  bgcolor: '#0055CC',
                },
                '&.Mui-disabled': {
                  bgcolor: '#E9ECEF',
                }
              }}
            >
              {loading ? <CircularProgress size={20} sx={{ color: '#fff' }} /> : 'Send'}
            </Button>
          </Box>
        </Box>
      </Paper>

      {/* Property Details Dialog */}
      <Dialog
        open={showPropertyDetails}
        onClose={() => setShowPropertyDetails(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Property Details
          {selectedProperty && (
            <Typography variant="body2" color="text.secondary">
              {selectedProperty.location || selectedProperty.address}
            </Typography>
          )}
        </DialogTitle>
        <DialogContent>
          {selectedProperty && (
            <Box>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Typography variant="h6" gutterBottom>
                    {selectedProperty.title || `${selectedProperty.bedrooms}BR ${selectedProperty.property_type}`}
                  </Typography>
                  <Typography variant="h5" color="primary" gutterBottom>
                    {formatCurrency(selectedProperty.price)}
                  </Typography>
                  <Typography variant="body1" paragraph>
                    {selectedProperty.description}
                  </Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <List dense>
                    <ListItem>
                      <ListItemText 
                        primary="Bedrooms" 
                        secondary={selectedProperty.bedrooms} 
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText 
                        primary="Bathrooms" 
                        secondary={selectedProperty.bathrooms} 
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText 
                        primary="Area" 
                        secondary={`${selectedProperty.area || selectedProperty.sqft} sqft`} 
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText 
                        primary="Type" 
                        secondary={selectedProperty.property_type} 
                      />
                    </ListItem>
                  </List>
                </Grid>
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowPropertyDetails(false)}>
            Close
          </Button>
          {selectedProperty && (
            <>
              <Button
                onClick={() => handlePropertyAction('amenities', selectedProperty.id)}
                disabled={actionLoading[`amenities_${selectedProperty.id}`]}
              >
                View Amenities
              </Button>
              <Button
                variant="contained" 
                onClick={() => {
                  const offer = prompt(`Enter your offer for ${formatCurrency(selectedProperty.price)}:`);
                  if (offer && !isNaN(offer)) {
                    handlePropertyAction('negotiate', selectedProperty.id, { offer: parseInt(offer) });
                  }
                }}
                disabled={actionLoading[`negotiate_${selectedProperty.id}`]}
              >
                Make Offer
              </Button>
            </>
          )}
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert 
          onClose={() => setSnackbar({ ...snackbar, open: false })} 
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default ChatInterface;
