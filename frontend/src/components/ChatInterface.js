import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  TextField,
  Button,
  Paper,
  Typography,
  Container,
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
  Snackbar,
  Badge,
  Tooltip,
  IconButton,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  LinearProgress,
  Stack
} from '@mui/material';
// Remove this line: import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import RealEstateService from '../services/realEstateService';

const ChatInterface = () => {
  console.log('🎨 =================================');
  console.log('🎨 CHAT INTERFACE COMPONENT LOADING');
  console.log('🎨 =================================');
  
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [properties, setProperties] = useState([]);
  const [selectedProperty, setSelectedProperty] = useState(null);
  const [showPropertyDetails, setShowPropertyDetails] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });
  const [searchSuggestions, setSearchSuggestions] = useState([]);
  const [actionLoading, setActionLoading] = useState({}); // Track loading state for each action
  const messagesEndRef = useRef(null);

  console.log('🎨 Component state initialized');
  console.log('🎨 RealEstateService available:', !!RealEstateService);

  const scrollToBottom = () => {
    console.log('📜 Scrolling to bottom');
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    console.log('📜 Messages updated, scrolling to bottom');
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    console.log('🎬 ChatInterface mounted, adding welcome message');
    const welcomeMessage = {
      id: 1,
      text: "👋 Welcome to AI Real Estate Assistant! I'm here to help you find your perfect home.\n\n🏠 I can help you with:\n• Property searches with smart filtering\n• Detailed amenities information\n• Price negotiations\n• Deal closing process\n\nTry asking: 'Find 2BHK apartments in Dallas under $500K'",
      sender: 'agent',
      timestamp: new Date().toISOString(),
      type: 'welcome'
    };
    
    console.log('🎬 Welcome message created:', welcomeMessage);
    setMessages([welcomeMessage]);
  }, []);

  const handleSubmit = async (e) => {
    console.log('📝 =================================');
    console.log('📝 FORM SUBMIT STARTED');
    console.log('📝 =================================');
    
    e.preventDefault();
    console.log('📝 Event prevented');
    console.log('📝 Current input value:', input);
    console.log('📝 Input trimmed:', input.trim());
    
    if (!input.trim()) {
      console.log('⚠️ Empty input, returning early');
      return;
    }

    console.log('📝 Creating user message...');
    const userMessage = {
      id: messages.length + 1,
      text: input,
      sender: 'user',
      timestamp: new Date().toISOString(),
    };
    console.log('📝 User message created:', userMessage);

    console.log('📝 Updating messages state...');
    setMessages((prev) => {
      console.log('📝 Previous messages:', prev);
      const newMessages = [...prev, userMessage];
      console.log('📝 New messages array:', newMessages);
      return newMessages;
    });
    
    const currentInput = input;
    console.log('📝 Saving current input:', currentInput);
    console.log('📝 Clearing input field...');
    setInput('');
    
    console.log('📝 Setting loading to true...');
    setLoading(true);

    try {
      console.log('🚀 Starting API call...');
      console.log('🚀 Calling RealEstateService.chatQuery with:', currentInput);
      
      // Call the service
      const response = await RealEstateService.chatQuery(currentInput);
      
      console.log('✅ API call completed');
      console.log('✅ Response received:', response);
      console.log('✅ Response status:', response.status);
      console.log('✅ Response message:', response.message);
      console.log('✅ Response data:', response.data);
      
      const agentMessage = {
        id: messages.length + 2,
        text: response.message || "I'm processing your request...",
        sender: 'agent',
        timestamp: new Date().toISOString(),
        data: response.data,
        status: response.status
      };
      console.log('🤖 Agent message created:', agentMessage);

      console.log('📝 Adding agent message to state...');
      setMessages((prev) => {
        console.log('📝 Previous messages before agent response:', prev);
        const newMessages = [...prev, agentMessage];
        console.log('📝 Messages after agent response:', newMessages);
        return newMessages;
      });

      // Enhanced property handling
      console.log('🏠 Checking for properties in response...');
      if (response.data?.properties && response.data.properties.length > 0) {
        console.log('🏠 Exact match properties found:', response.data.properties.length);
        console.log('🏠 First property:', response.data.properties[0]);
        
        const processedProperties = response.data.properties.map(p => ({ 
          ...p, 
          showAmenities: false,
          negotiationStatus: 'none',
          isExactMatch: true,
          amenitiesData: null,
          negotiationData: null,
          closingData: null
        }));
        console.log('🏠 Processed properties:', processedProperties);
        
        setProperties(processedProperties);
        setSearchSuggestions([]);
        console.log('🏠 Properties state updated');
        
      } else if (response.data?.alternative_count > 0) {
        // Handle alternative properties when no exact matches
        console.log('🏠 No exact matches, but alternatives available:', response.data.alternative_count);
        console.log('🏠 Suggestions:', response.data.suggestions);
        
        // Store suggestions for display
        setSearchSuggestions(response.data.suggestions || []);
        
        // Try to get some alternative properties automatically
        await fetchAlternativeProperties(currentInput, response.data);
        
      } else {
        console.log('🏠 No properties found in response');
        setProperties([]);
        setSearchSuggestions(response.data?.suggestions || []);
      }

      // Show success/error snackbar
      if (response.status === 'error') {
        console.log('⚠️ Error response detected, showing snackbar');
        setSnackbar({ 
          open: true, 
          message: 'Something went wrong. Please try again.', 
          severity: 'error' 
        });
      } else {
        console.log('✅ Success response detected');
      }

    } catch (error) {
      console.log('💥 =================================');
      console.log('💥 HANDLE SUBMIT ERROR');
      console.log('💥 =================================');
      console.error('💥 Caught error in handleSubmit:', error);
      console.error('💥 Error name:', error.name);
      console.error('💥 Error message:', error.message);
      console.error('💥 Error stack:', error.stack);
      
      const errorMessage = {
        id: messages.length + 2,
        text: '❌ Sorry, I encountered an error. Please try again or rephrase your question.',
        sender: 'agent',
        timestamp: new Date().toISOString(),
        status: 'error'
      };
      console.log('💥 Error message created:', errorMessage);
      
      setMessages((prev) => [...prev, errorMessage]);
      
      setSnackbar({ 
        open: true, 
        message: 'Connection error. Please check your internet and try again.', 
        severity: 'error' 
      });
    } finally {
      console.log('🏁 Setting loading to false...');
      setLoading(false);
      console.log('🏁 Handle submit completed');
    }
  };

  const fetchAlternativeProperties = async (originalQuery, responseData) => {
    try {
      console.log('🔄 Fetching alternative properties...');
      
      // Generate alternative queries based on the original
      const alternativeQueries = generateAlternativeQueries(originalQuery, responseData);
      
      for (const altQuery of alternativeQueries) {
        console.log('🔄 Trying alternative query:', altQuery);
        
        const altResponse = await RealEstateService.chatQuery(altQuery);
        
        if (altResponse.data?.properties && altResponse.data.properties.length > 0) {
          console.log('🏠 Alternative properties found:', altResponse.data.properties.length);
          
          const altProperties = altResponse.data.properties.map(p => ({ 
            ...p, 
            showAmenities: false,
            negotiationStatus: 'none',
            isAlternative: true,
            amenitiesData: null,
            negotiationData: null,
            closingData: null
          }));
          
          setProperties(altProperties);
          
          // Add an info message about alternatives
          const altMessage = {
            id: Date.now(), // Use timestamp for unique ID
            text: `💡 Since no exact matches were found, here are ${altProperties.length} similar properties that might interest you:`,
            sender: 'agent',
            timestamp: new Date().toISOString(),
            type: 'alternatives'
          };
          
          setMessages(prev => [...prev, altMessage]);
          break; // Stop after finding the first successful alternative
        }
      }
    } catch (error) {
      console.log('❌ Error fetching alternatives:', error);
    }
  };

  const generateAlternativeQueries = (originalQuery, responseData) => {
    const alternatives = [];
    
    // If San Francisco, try other CA cities
    if (originalQuery.toLowerCase().includes('san francisco')) {
      alternatives.push(originalQuery.replace(/san francisco/i, 'Los Angeles'));
      alternatives.push(originalQuery.replace(/san francisco/i, 'San Diego'));
    }
    
    // If under certain price, try higher prices
    if (originalQuery.includes('$500K') || originalQuery.includes('500K')) {
      alternatives.push(originalQuery.replace(/\$?500K|\$?500,000/i, '$600K'));
      alternatives.push(originalQuery.replace(/\$?500K|\$?500,000/i, '$700K'));
    }
    
    // Try different cities entirely
    alternatives.push(originalQuery.replace(/in \w+( \w+)?/, 'in Dallas'));
    alternatives.push(originalQuery.replace(/in \w+( \w+)?/, 'in Houston'));
    alternatives.push(originalQuery.replace(/under \$\d+K?/, 'under $600K'));
    
    // Generic fallback
    if (alternatives.length === 0) {
      alternatives.push('Show me 2 bedroom apartments under $600K');
      alternatives.push('Find available apartments with 2 bedrooms');
    }
    
    return alternatives.slice(0, 3); // Limit to 3 alternatives
  };

  // Enhanced handlePropertyAction with proper agent integration
  const handlePropertyAction = async (property, action, data = {}) => {
    console.log('🏠 =================================');
    console.log('🏠 PROPERTY ACTION STARTED');
    console.log('🏠 =================================');
    console.log('🏠 Property:', property);
    console.log('🏠 Action:', action);
    console.log('🏠 Data:', data);
    
    // Set loading state for this specific action
    const actionKey = `${property.id}-${action}`;
    setActionLoading(prev => ({ ...prev, [actionKey]: true }));
    
    try {
      let response;
      let agentMessage;
      
      switch (action) {
        case 'viewDetails':
          console.log('👀 Invoking Details Agent for property:', property.id);
          
          // Add immediate feedback message
          agentMessage = {
            id: Date.now(),
            text: `🔍 Let me get detailed information about the property at ${property.address}...`,
            sender: 'agent',
            timestamp: new Date().toISOString(),
            type: 'processing'
          };
          setMessages(prev => [...prev, agentMessage]);
          
          // Open modal and add detailed agent response
          setSelectedProperty(property);
          setShowPropertyDetails(true);
          
          // Generate intelligent property analysis
          const detailsResponse = await RealEstateService.chatQuery(
            `Provide detailed analysis and insights for this property: ${property.address}, ${property.city}, ${property.state}. Price: $${property.price}, ${property.bedrooms} bed, ${property.bathrooms} bath, ${property.square_feet} sqft, built in ${property.year_built}`
          );
          
          const detailsMessage = {
            id: Date.now() + 1,
            text: detailsResponse.message || `Here's what I found about ${property.address}: This ${property.property_type} offers great value in ${property.city}. Built in ${property.year_built}, it features ${property.bedrooms} bedrooms and ${property.bathrooms} bathrooms in ${property.square_feet} square feet.`,
            sender: 'agent',
            timestamp: new Date().toISOString(),
            type: 'property_details'
          };
          setMessages(prev => [...prev, detailsMessage]);
          break;

        case 'showAmenities':
          console.log('🏢 Invoking Amenities Agent for property:', property.id);
          
          // Add immediate feedback
          agentMessage = {
            id: Date.now(),
            text: `🏢 Analyzing amenities and nearby facilities for ${property.address}...`,
            sender: 'agent',
            timestamp: new Date().toISOString(),
            type: 'processing'
          };
          setMessages(prev => [...prev, agentMessage]);
          
          // Call amenities agent
          response = await RealEstateService.getPropertyAmenities(property.id);
          console.log('🏢 Amenities response:', response);
          
          if (response.status === 'success') {
            console.log('🏢 Updating property amenities in state');
            setProperties(prev => prev.map(p =>
              p.id === property.id
                ? { ...p, showAmenities: !p.showAmenities, amenitiesData: response.data }
                : p
            ));
            
            // Add detailed amenities message
            const amenitiesMessage = {
              id: Date.now() + 1,
              text: response.message || `🏢 Here are the amenities and nearby facilities for ${property.address}. This property offers excellent access to local services and recreational facilities.`,
              sender: 'agent',
              timestamp: new Date().toISOString(),
              type: 'amenities',
              data: response.data
            };
            setMessages(prev => [...prev, amenitiesMessage]);
          }
          break;
          
        case 'makeOffer':
          console.log('💰 Invoking Negotiation Agent for property:', property.id);
          
          const suggestedOffer = Math.round(property.price * 0.95);
          
          // Add immediate feedback
          agentMessage = {
            id: Date.now(),
            text: `💰 Preparing negotiation strategy for ${property.address}. Analyzing market conditions and suggesting competitive offer...`,
            sender: 'agent',
            timestamp: new Date().toISOString(),
            type: 'processing'
          };
          setMessages(prev => [...prev, agentMessage]);
          
          // Auto-populate input with suggested offer
          setInput(`I want to make an offer of $${suggestedOffer.toLocaleString()} for property ${property.id}`);
          
          // Call negotiation agent for market analysis
          response = await RealEstateService.negotiatePrice(property.id, suggestedOffer);
          console.log('💰 Negotiation response:', response);
          
          if (response.status === 'success') {
            setProperties(prev => prev.map(p =>
              p.id === property.id
                ? { ...p, negotiationStatus: response.data.negotiation_status, negotiationData: response.data }
                : p
            ));
            
            const negotiationMessage = {
              id: Date.now() + 1,
              text: response.message || `💰 I've analyzed the market for ${property.address}. Based on current conditions, here's my recommendation for your offer strategy.`,
              sender: 'agent',
              timestamp: new Date().toISOString(),
              data: response.data,
              type: 'negotiation'
            };
            setMessages(prev => [...prev, negotiationMessage]);
          }
          break;

        case 'negotiate':
          console.log('💰 Processing negotiation for property:', property.id);
          const offerAmount = data.offer || Math.round(property.price * 0.95);
          
          agentMessage = {
            id: Date.now(),
            text: `🤝 Submitting your offer of $${offerAmount.toLocaleString()} to the seller and analyzing their response...`,
            sender: 'agent',
            timestamp: new Date().toISOString(),
            type: 'processing'
          };
          setMessages(prev => [...prev, agentMessage]);
          
          response = await RealEstateService.negotiatePrice(property.id, offerAmount);
          console.log('💰 Negotiation response:', response);
          
          if (response.status === 'success') {
            console.log('💰 Updating negotiation status');
            setProperties(prev => prev.map(p =>
              p.id === property.id
                ? { ...p, negotiationStatus: response.data.negotiation_status, negotiationData: response.data }
                : p
            ));
            
            const negotiationMessage = {
              id: Date.now() + 1,
              text: response.message,
              sender: 'agent',
              timestamp: new Date().toISOString(),
              data: response.data,
              type: 'negotiation'
            };
            setMessages(prev => [...prev, negotiationMessage]);
          }
          break;
          
        case 'closeDeal':
          console.log('🤝 Invoking Deal Closing Agent for property:', property.id);
          
          agentMessage = {
            id: Date.now(),
            text: `🤝 Initiating deal closing process for ${property.address}. Preparing contracts and coordinating with all parties...`,
            sender: 'agent',
            timestamp: new Date().toISOString(),
            type: 'processing'
          };
          setMessages(prev => [...prev, agentMessage]);
          
          response = await RealEstateService.finalizeDeal(property.id);
          console.log('🤝 Deal response:', response);
          
          if (response.status === 'success') {
            console.log('🤝 Updating property deal status');
            setProperties(prev => prev.map(p =>
              p.id === property.id
                ? { ...p, dealStatus: 'closed', closingData: response.data }
                : p
            ));
            
            const closingMessage = {
              id: Date.now() + 1,
              text: response.message || `🎉 Congratulations! The deal for ${property.address} has been successfully closed. Welcome to your new home!`,
              sender: 'agent',
              timestamp: new Date().toISOString(),
              data: response.data,
              type: 'closing'
            };
            setMessages(prev => [...prev, closingMessage]);
            
            setSnackbar({ 
              open: true, 
              message: '🎉 Congratulations! Deal successfully closed!', 
              severity: 'success' 
            });
          }
          break;
          
        default:
          console.warn('❓ Unknown action:', action);
          break;
      }
    } catch (error) {
      console.error('💥 Property action error:', error);
      
      const errorMessage = {
        id: Date.now(),
        text: `❌ Sorry, I encountered an issue while processing your ${action} request. Please try again.`,
        sender: 'agent',
        timestamp: new Date().toISOString(),
        type: 'error'
      };
      setMessages(prev => [...prev, errorMessage]);
      
      setSnackbar({ 
        open: true, 
        message: 'Action failed. Please try again.', 
        severity: 'error' 
      });
    } finally {
      // Clear loading state
      setActionLoading(prev => {
        const newState = { ...prev };
        delete newState[actionKey];
        return newState;
      });
    }
  };

  const handleSuggestionClick = (suggestion) => {
    console.log('💡 Suggestion clicked:', suggestion);
    
    // Convert suggestion to a searchable query
    let query = '';
    if (suggestion.includes('budget')) {
      query = input.replace(/under \$\d+K?/i, 'under $600K');
    } else if (suggestion.includes('nearby')) {
      query = input.replace(/in \w+( \w+)?/i, 'in nearby areas');
    } else {
      query = suggestion;
    }
    
    setInput(query);
  };

  const PropertyCard = ({ property }) => {
    console.log('🎴 Rendering PropertyCard for:', property.id);
    
    const isActionLoading = (action) => actionLoading[`${property.id}-${action}`];
    
    return (
      <Card 
        sx={{ 
          mb: 2, 
          borderLeft: property.dealStatus === 'closed' 
            ? '4px solid #4caf50' 
            : property.isAlternative 
              ? '4px solid #ff9800' 
              : '4px solid #2196f3',
          opacity: property.dealStatus === 'closed' ? 0.8 : 1,
          position: 'relative'
        }}
      >
        {property.isAlternative && (
          <Chip 
            label="Similar Property" 
            size="small" 
            color="warning" 
            sx={{ position: 'absolute', top: 8, right: 8, zIndex: 1 }}
          />
        )}
        
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1, pr: 2 }}>
              🏠 {property.address}
            </Typography>
            {property.dealStatus === 'closed' && (
              <Chip label="SOLD" color="success" size="small" />
            )}
          </Box>
          
          <Typography color="text.secondary" sx={{ mb: 1 }}>
            📍 {property.city}, {property.state}
          </Typography>

          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={6} sm={3}>
              <Typography variant="h6" color="success.main">
                💰 ${property.price.toLocaleString()}
              </Typography>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Typography>🛏️ {property.bedrooms} bed</Typography>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Typography>🛁 {property.bathrooms} bath</Typography>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Typography>📐 {property.square_feet?.toLocaleString()} sqft</Typography>
            </Grid>
          </Grid>

          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
            <Chip label={property.property_type} variant="outlined" size="small" />
            {property.is_pet_friendly && (
              <Chip label="🐕 Pet Friendly" variant="outlined" size="small" color="secondary" />
            )}
            {property.year_built && (
              <Chip label={`Built ${property.year_built}`} variant="outlined" size="small" />
            )}
          </Box>

          {/* Enhanced Amenities Display */}
          {property.showAmenities && property.amenitiesData && (
            <Accordion sx={{ mt: 2 }}>
              <AccordionSummary expandIcon={<span>▼</span>}>
                <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
                  🏢 Property Amenities & Nearby Facilities
                </Typography>
              </AccordionSummary>
              <AccordionDetails>
                {property.amenitiesData.amenities && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" sx={{ mb: 1, fontWeight: 'bold' }}>Building Amenities:</Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {property.amenitiesData.amenities.slice(0, 8).map((amenity, index) => (
                        <Chip key={index} label={amenity} size="small" variant="outlined" />
                      ))}
                    </Box>
                  </Box>
                )}
                
                {property.nearby_amenities && (
                  <Box>
                    <Typography variant="body2" sx={{ mb: 1, fontWeight: 'bold' }}>Nearby Facilities:</Typography>
                    <Grid container spacing={1}>
                      {Object.entries(property.nearby_amenities).map(([category, info]) => (
                        <Grid item xs={12} sm={6} key={category}>
                          <Typography variant="caption">
                            <strong>{category.charAt(0).toUpperCase() + category.slice(1)}:</strong> {info.name} ({info.distance} mi)
                          </Typography>
                        </Grid>
                      ))}
                    </Grid>
                  </Box>
                )}
              </AccordionDetails>
            </Accordion>
          )}

          {/* Enhanced Negotiation Display */}
          {property.negotiationData && (
            <Alert 
              severity={property.negotiationData.negotiation_status === 'accepted' ? 'success' : 'info'}
              sx={{ mt: 2 }}
            >
              <strong>Negotiation Update:</strong> {property.negotiationData.message || 'Offer under review'}
              {property.negotiationData.counter_offer && (
                <Typography variant="body2" sx={{ mt: 1 }}>
                  Counter Offer: ${property.negotiationData.counter_offer.toLocaleString()}
                </Typography>
              )}
              {property.negotiationData.next_steps && (
                <Box sx={{ mt: 1 }}>
                  <Typography variant="body2" sx={{ fontWeight: 'bold' }}>Next Steps:</Typography>
                  <List dense>
                    {property.negotiationData.next_steps.slice(0, 3).map((step, index) => (
                      <ListItem key={index} sx={{ py: 0.5 }}>
                        <Typography variant="caption">• {step}</Typography>
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}
            </Alert>
          )}
        </CardContent>

        <CardActions sx={{ flexWrap: 'wrap', gap: 1 }}>
          <Button 
            size="small" 
            onClick={() => handlePropertyAction(property, 'viewDetails')}
            disabled={isActionLoading('viewDetails')}
            startIcon={isActionLoading('viewDetails') ? <CircularProgress size={16} /> : null}
          >
            {isActionLoading('viewDetails') ? 'Loading...' : 'ℹ️ View Details'}
          </Button>
          
          <Button 
            size="small" 
            onClick={() => handlePropertyAction(property, 'showAmenities')}
            disabled={isActionLoading('showAmenities')}
            startIcon={isActionLoading('showAmenities') ? <CircularProgress size={16} /> : null}
          >
            {isActionLoading('showAmenities') 
              ? 'Loading...' 
              : property.showAmenities 
                ? '🔽 Hide Amenities' 
                : '🔼 Show Amenities'}
          </Button>

          {property.dealStatus !== 'closed' && (
            <>
              <Button
                size="small"
                variant="contained"
                onClick={() => handlePropertyAction(property, 'makeOffer')}
                disabled={isActionLoading('makeOffer')}
                startIcon={isActionLoading('makeOffer') ? <CircularProgress size={16} /> : null}
              >
                {isActionLoading('makeOffer') ? 'Analyzing...' : '💰 Make Offer'}
              </Button>

              {property.negotiationStatus === 'accepted' && (
                <Button
                  size="small"
                  color="success"
                  variant="contained"
                  onClick={() => handlePropertyAction(property, 'closeDeal')}
                  disabled={isActionLoading('closeDeal')}
                  startIcon={isActionLoading('closeDeal') ? <CircularProgress size={16} /> : null}
                >
                  {isActionLoading('closeDeal') ? 'Processing...' : '✅ Close Deal'}
                </Button>
              )}
              
              {property.negotiationStatus === 'counter_offered' && (
                <Button
                  size="small"
                  color="warning"
                  variant="contained"
                  onClick={() => handlePropertyAction(property, 'negotiate', { 
                    offer: property.negotiationData?.counter_offer 
                  })}
                  disabled={isActionLoading('negotiate')}
                >
                  🤝 Accept Counter
                </Button>
              )}
            </>
          )}
        </CardActions>
      </Card>
    );
  };

  console.log('🎨 Rendering ChatInterface component');
  console.log('🎨 Current state - messages:', messages.length);
  console.log('🎨 Current state - properties:', properties.length);
  console.log('🎨 Current state - loading:', loading);

  return (
    <Container maxWidth="lg">
      <Box sx={{ height: '100vh', py: 2, display: 'flex', flexDirection: 'column' }}>
        <Paper elevation={3} sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', borderRadius: 2, overflow: 'hidden' }}>
          
          {/* Header */}
          <Box sx={{ p: 2, bgcolor: 'primary.main', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography variant="h6">🏠 AI Real Estate Assistant</Typography>
            {properties.length > 0 && (
              <Badge badgeContent={properties.length} color="secondary">
                <Typography variant="body2">Properties</Typography>
              </Badge>
            )}
          </Box>

          {/* Messages Area */}
          <Box sx={{ flexGrow: 1, overflow: 'auto', p: 2, display: 'flex', flexDirection: 'column' }}>
            {messages.map((message) => {
              console.log('💬 Rendering message:', message.id, message.sender);
              return (
                <Box
                  key={message.id}
                  sx={{
                    display: 'flex',
                    justifyContent: message.sender === 'user' ? 'flex-end' : 'flex-start',
                    mb: 2,
                    alignItems: 'flex-start'
                  }}
                >
                  {message.sender === 'agent' && (
                    <Avatar sx={{ 
                      bgcolor: message.type === 'processing' ? 'warning.main' : 'secondary.main', 
                      width: 32, 
                      height: 32, 
                      mr: 1, 
                      mt: 0.5 
                    }}>
                      {message.type === 'processing' ? '⚡' : 'AI'}
                    </Avatar>
                  )}
                  
                  <Paper
                    sx={{
                      p: 2,
                      backgroundColor: message.sender === 'user' 
                        ? 'primary.light' 
                        : message.status === 'error' 
                          ? 'error.light'
                          : message.type === 'alternatives'
                            ? 'warning.light'
                            : message.type === 'processing'
                              ? 'info.light'
                              : 'grey.100',
                      color: message.sender === 'user' ? 'white' : 'text.primary',
                      maxWidth: '80%',
                      borderRadius: 2,
                      whiteSpace: 'pre-line'
                    }}
                  >
                    <Typography variant="body1">{message.text}</Typography>
                    
                    {/* Enhanced message data display */}
                    {message.type === 'amenities' && message.data && (
                      <Box sx={{ mt: 1, p: 1, bgcolor: 'rgba(255,255,255,0.1)', borderRadius: 1 }}>
                        <Typography variant="caption">
                          ✨ Amenity Score: {message.data.amenity_score?.rating}/5.0
                        </Typography>
                      </Box>
                    )}
                    
                    {message.type === 'negotiation' && message.data && (
                      <Box sx={{ mt: 1, p: 1, bgcolor: 'rgba(255,255,255,0.1)', borderRadius: 1 }}>
                        <Typography variant="caption">
                          💰 Market Analysis: {message.data.market_insights?.price_trend} trend
                        </Typography>
                      </Box>
                    )}
                  </Paper>

                  {message.sender === 'user' && (
                    <Avatar sx={{ bgcolor: 'primary.main', width: 32, height: 32, ml: 1, mt: 0.5 }}>
                      U
                    </Avatar>
                  )}
                </Box>
              );
            })}
            <div ref={messagesEndRef} />
          </Box>

          {/* Search Suggestions */}
          {searchSuggestions.length > 0 && properties.length === 0 && (
            <Box sx={{ px: 2, pb: 1 }}>
              <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 'bold' }}>
                💡 Try these suggestions:
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {searchSuggestions.map((suggestion, index) => (
                  <Chip
                    key={index}
                    label={suggestion}
                    variant="outlined"
                    size="small"
                    clickable
                    onClick={() => handleSuggestionClick(suggestion)}
                    sx={{ cursor: 'pointer' }}
                  />
                ))}
              </Box>
            </Box>
          )}

          {/* Properties Display */}
          {properties.length > 0 && (
            <Box sx={{ maxHeight: '400px', overflow: 'auto', px: 2, pb: 2 }}>
              <Divider sx={{ mb: 2 }} />
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="h6">
                  🏠 {properties.some(p => p.isAlternative) ? 'Similar' : 'Found'} Properties ({properties.length}):
                </Typography>
                {properties.some(p => p.isAlternative) && (
                  <Chip label="Alternative Results" color="warning" size="small" />
                )}
              </Box>
              {properties.map((property) => {
                console.log('🏠 Rendering property card:', property.id);
                return <PropertyCard key={property.id} property={property} />;
              })}
            </Box>
          )}

          {/* Input Area */}
          <Box sx={{ p: 2, borderTop: '1px solid', borderColor: 'divider' }}>
            <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', gap: 1 }}>
              <TextField
                fullWidth
                value={input}
                onChange={(e) => {
                  console.log('✏️ Input changed:', e.target.value);
                  setInput(e.target.value);
                }}
                placeholder="Ask me about properties, amenities, negotiations, or closing deals..."
                disabled={loading}
                variant="outlined"
                size="small"
                multiline
                maxRows={3}
              />
              <Button 
                type="submit" 
                variant="contained" 
                disabled={loading || !input.trim()}
                sx={{ minWidth: 'auto', px: 2 }}
                onClick={() => console.log('🔘 Submit button clicked')}
              >
                {loading ? <CircularProgress size={24} /> : '📤'}
              </Button>
            </Box>
            
            <Box sx={{ mt: 1, display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              <Chip 
                label="🔍 Search Dallas Properties" 
                size="small" 
                clickable 
                onClick={() => {
                  console.log('🔍 Quick search clicked');
                  setInput("Find 2BHK apartments in Dallas under $500K");
                }}
              />
              <Chip 
                label="🐕 Pet-Friendly Options" 
                size="small" 
                clickable 
                onClick={() => {
                  console.log('🐕 Pet-friendly clicked');
                  setInput("Show pet-friendly properties");
                }}
              />
              <Chip 
                label="✨ Luxury Properties" 
                size="small" 
                clickable 
                onClick={() => {
                  console.log('✨ Luxury clicked');
                  setInput("Find luxury condos with amenities");
                }}
              />
              <Chip 
                label="🏠 General Search" 
                size="small" 
                clickable 
                onClick={() => {
                  console.log('🏠 General search clicked');
                  setInput("Show me available 2 bedroom apartments");
                }}
              />
            </Box>
          </Box>
        </Paper>

        {/* Enhanced Property Details Modal */}
        <Dialog open={showPropertyDetails} onClose={() => setShowPropertyDetails(false)} maxWidth="md" fullWidth>
          <DialogTitle>Property Details & Analysis</DialogTitle>
          <DialogContent>
            {selectedProperty && (
              <Box>
                <Typography variant="h6">{selectedProperty.address}</Typography>
                <Typography color="text.secondary" sx={{ mb: 2 }}>
                  {selectedProperty.city}, {selectedProperty.state}
                </Typography>
                
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6}>
                    <List dense>
                      <ListItem>
                        <ListItemText primary="💰 Price" secondary={`$${selectedProperty.price.toLocaleString()}`} />
                      </ListItem>
                      <ListItem>
                        <ListItemText primary="🛏️ Bedrooms" secondary={selectedProperty.bedrooms} />
                      </ListItem>
                      <ListItem>
                        <ListItemText primary="🛁 Bathrooms" secondary={selectedProperty.bathrooms} />
                      </ListItem>
                      <ListItem>
                        <ListItemText primary="📅 Year Built" secondary={selectedProperty.year_built} />
                      </ListItem>
                    </List>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <List dense>
                      <ListItem>
                        <ListItemText primary="📐 Square Feet" secondary={selectedProperty.square_feet?.toLocaleString()} />
                      </ListItem>
                      <ListItem>
                        <ListItemText primary="🏠 Property Type" secondary={selectedProperty.property_type} />
                      </ListItem>
                      <ListItem>
                        <ListItemText primary="🐕 Pet Friendly" secondary={selectedProperty.is_pet_friendly ? 'Yes' : 'No'} />
                      </ListItem>
                      <ListItem>
                        <ListItemText primary="📍 Lot Size" secondary={`${selectedProperty.lot_size} acres`} />
                      </ListItem>
                    </List>
                  </Grid>
                </Grid>

                {/* Nearby Amenities */}
                {selectedProperty.nearby_amenities && Object.keys(selectedProperty.nearby_amenities).length > 0 && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="h6" sx={{ mb: 1 }}>Nearby Amenities:</Typography>
                    <Grid container spacing={1}>
                      {Object.entries(selectedProperty.nearby_amenities).map(([category, info]) => (
                        <Grid item xs={12} sm={6} key={category}>
                          <Typography variant="body2">
                            <strong>{category.charAt(0).toUpperCase() + category.slice(1)}:</strong> {info.name} ({info.distance} mi)
                          </Typography>
                        </Grid>
                      ))}
                    </Grid>
                  </Box>
                )}
              </Box>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setShowPropertyDetails(false)}>Close</Button>
            {selectedProperty && (
              <Button 
                variant="contained" 
                onClick={() => {
                  setShowPropertyDetails(false);
                  handlePropertyAction(selectedProperty, 'makeOffer');
                }}
              >
                Make Offer
              </Button>
            )}
          </DialogActions>
        </Dialog>

        {/* Snackbar for notifications */}
        <Snackbar
          open={snackbar.open}
          autoHideDuration={6000}
          onClose={() => setSnackbar({ ...snackbar, open: false })}
        >
          <Alert onClose={() => setSnackbar({ ...snackbar, open: false })} severity={snackbar.severity} sx={{ width: '100%' }}>
            {snackbar.message}
          </Alert>
        </Snackbar>
      </Box>
    </Container>
  );
};

console.log('🎨 ChatInterface component defined, exporting...');
export default ChatInterface;
