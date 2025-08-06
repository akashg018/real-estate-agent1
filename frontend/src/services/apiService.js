// src/services/apiService.js

class ApiService {
  constructor() {
    // HARDCODED API URL - No environment variables needed
    this.baseURL = 'https://real-estate-agent1-2.onrender.com/api';
    this.timeout = 15000;
    this.headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    };
    
    console.log('🔧 API Service configured with hardcoded URL:', this.baseURL);
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
    return this.makeRequest('/health', {
      method: 'GET',
    });
  }

  // Send chat message
  async sendMessage(message) {
    return this.makeRequest('/chat', {
      method: 'POST',
      body: JSON.stringify({ message }),
    });
  }

  // Get property details
  async getPropertyDetails(propertyId) {
    return this.makeRequest(`/property/${propertyId}`, {
      method: 'GET',
    });
  }

  // Get property amenities
  async getPropertyAmenities(propertyId) {
    return this.makeRequest(`/property/${propertyId}/amenities`, {
      method: 'GET',
    });
  }

  // Handle property negotiation
  async negotiateProperty(propertyId, offerAmount) {
    return this.makeRequest(`/property/${propertyId}/negotiate`, {
      method: 'POST',
      body: JSON.stringify({ offer: offerAmount }),
    });
  }

  // Close property deal
  async closeDeal(propertyId, dealData = {}) {
    return this.makeRequest(`/property/${propertyId}/close-deal`, {
      method: 'POST',
      body: JSON.stringify(dealData),
    });
  }
}

export default new ApiService();
