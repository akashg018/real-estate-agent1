// src/services/apiService.js
import API_CONFIG from '../config/api';

class ApiService {
  constructor() {
    this.baseURL = API_CONFIG.baseURL;
    this.timeout = API_CONFIG.timeout;
    this.headers = API_CONFIG.headers;
  }

  async makeRequest(url, options = {}) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      console.log(`🌐 Making request to: ${this.baseURL}${url}`);
      
      const response = await fetch(`${this.baseURL}${url}`, {
        ...options,
        headers: {
          ...this.headers,
          ...options.headers,
        },
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      console.log(`📡 Response status: ${response.status}`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('✅ Response received:', data);
      return data;
      
    } catch (error) {
      clearTimeout(timeoutId);
      console.error('❌ API Request failed:', error);
      
      if (error.name === 'AbortError') {
        throw new Error('Request timeout - please try again');
      }
      
      if (error.message.includes('Failed to fetch')) {
        throw new Error('Unable to connect to server. Please check your internet connection.');
      }
      
      throw error;
    }
  }

  // Health check endpoint
  async checkHealth() {
    return this.makeRequest(API_CONFIG.endpoints.health, {
      method: 'GET',
    });
  }

  // Send chat message - This matches your backend's expected format
  async sendMessage(query) {
    return this.makeRequest(API_CONFIG.endpoints.chat, {
      method: 'POST',
      body: JSON.stringify({ query }), // Your backend expects 'query', not 'message'
    });
  }

  // Get property details
  async getPropertyDetails(propertyId) {
    return this.makeRequest(`${API_CONFIG.endpoints.property}/${propertyId}`, {
      method: 'GET',
    });
  }

  // Get property amenities
  async getPropertyAmenities(propertyId) {
    const url = API_CONFIG.endpoints.propertyAmenities.replace('{id}', propertyId);
    return this.makeRequest(url, {
      method: 'GET',
    });
  }

  // Handle property negotiation
  async negotiateProperty(propertyId, offerAmount) {
    const url = API_CONFIG.endpoints.negotiate.replace('{id}', propertyId);
    return this.makeRequest(url, {
      method: 'POST',
      body: JSON.stringify({ offer: offerAmount }),
    });
  }

  // Close property deal
  async closeDeal(propertyId, dealData = {}) {
    const url = API_CONFIG.endpoints.closeDeal.replace('{id}', propertyId);
    return this.makeRequest(url, {
      method: 'POST',
      body: JSON.stringify(dealData),
    });
  }
}

export default new ApiService();
