// src/config/api.js
const API_CONFIG = {
  baseURL: process.env.REACT_APP_API_BASE_URL || 'https://real-estate-agent1-2.onrender.com',
  timeout: parseInt(process.env.REACT_APP_API_TIMEOUT) || 15000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
  endpoints: {
    health: '/api/health',
    chat: '/api/chat',
    property: '/api/property',
    propertyAmenities: '/api/property/{id}/amenities',
    negotiate: '/api/property/{id}/negotiate',
    closeDeal: '/api/property/{id}/close-deal',
  }
};

export default API_CONFIG;
