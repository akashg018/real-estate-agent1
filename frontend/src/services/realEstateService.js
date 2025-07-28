// Enhanced realEstateService.js with comprehensive debugging
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

// Configure axios defaults
axios.defaults.timeout = 30000; // 30 seconds
axios.defaults.headers.common['Content-Type'] = 'application/json';

class RealEstateService {
  constructor() {
    console.log('🔧 RealEstateService: Constructor called');
    console.log('🔧 API_BASE_URL:', API_BASE_URL);
    this.setupInterceptors();
  }

  setupInterceptors() {
    console.log('🔧 Setting up axios interceptors');
    
    // Request interceptor
    axios.interceptors.request.use(
      (config) => {
        console.log('📤 AXIOS REQUEST INTERCEPTOR:');
        console.log('  📍 Method:', config.method?.toUpperCase());
        console.log('  📍 URL:', config.url);
        console.log('  📍 Headers:', config.headers);
        console.log('  📍 Data:', config.data);
        console.log('  📍 Timeout:', config.timeout);
        return config;
      },
      (error) => {
        console.error('❌ AXIOS REQUEST ERROR:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor
    axios.interceptors.response.use(
      (response) => {
        console.log('📥 AXIOS RESPONSE INTERCEPTOR:');
        console.log('  ✅ Status:', response.status);
        console.log('  ✅ Status Text:', response.statusText);
        console.log('  ✅ Headers:', response.headers);
        console.log('  ✅ Data:', response.data);
        return response;
      },
      (error) => {
        console.error('❌ AXIOS RESPONSE ERROR INTERCEPTOR:');
        console.error('  💥 Error object:', error);
        console.error('  💥 Error message:', error.message);
        console.error('  💥 Error code:', error.code);
        
        if (error.response) {
          console.error('  💥 Response status:', error.response.status);
          console.error('  💥 Response data:', error.response.data);
          console.error('  💥 Response headers:', error.response.headers);
        } else if (error.request) {
          console.error('  💥 Request made but no response:', error.request);
        }
        
        return Promise.resolve({
          data: {
            status: 'error',
            message: error.response?.data?.message || error.message || 'Network error occurred',
            timestamp: new Date().toISOString()
          }
        });
      }
    );
  }

  async chatQuery(query) {
    console.log('🚀 =================================');
    console.log('🚀 CHAT QUERY STARTED');
    console.log('🚀 =================================');
    console.log('📝 Query received:', query);
    console.log('📝 Query type:', typeof query);
    console.log('📝 Query length:', query?.length);
    console.log('🌐 Target URL:', `${API_BASE_URL}/chat`);
    
    try {
      console.log('⏳ Making POST request...');
      
      const requestPayload = { query };
      console.log('📦 Request payload:', requestPayload);
      console.log('📦 Payload stringified:', JSON.stringify(requestPayload));
      
      const startTime = Date.now();
      
      const response = await axios.post(`${API_BASE_URL}/chat`, requestPayload, {
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        timeout: 30000
      });
      
      const endTime = Date.now();
      console.log(`⏱️ Request completed in ${endTime - startTime}ms`);
      
      console.log('✅ Raw response received:', response);
      console.log('✅ Response data:', response.data);
      console.log('✅ Response status:', response.status);
      
      const standardizedResponse = this.standardizeResponse(response.data);
      console.log('✅ Standardized response:', standardizedResponse);
      
      console.log('🎉 =================================');
      console.log('🎉 CHAT QUERY COMPLETED SUCCESSFULLY');
      console.log('🎉 =================================');
      
      return standardizedResponse;
      
    } catch (error) {
      console.log('💥 =================================');
      console.log('💥 CHAT QUERY FAILED');
      console.log('💥 =================================');
      console.error('💥 Caught error:', error);
      console.error('💥 Error name:', error.name);
      console.error('💥 Error message:', error.message);
      console.error('💥 Error stack:', error.stack);
      
      if (error.response) {
        console.error('💥 Error response status:', error.response.status);
        console.error('💥 Error response data:', error.response.data);
        console.error('💥 Error response headers:', error.response.headers);
      } else if (error.request) {
        console.error('💥 Error request (no response received):', error.request);
      }
      
      const errorResponse = this.handleError(error, 'Failed to process your request');
      console.error('💥 Final error response:', errorResponse);
      
      return errorResponse;
    }
  }

  async getPropertyAmenities(propertyId) {
    console.log('🏢 =================================');
    console.log('🏢 GET PROPERTY AMENITIES STARTED');
    console.log('🏢 =================================');
    console.log('🏢 Property ID:', propertyId);
    
    try {
      const url = `${API_BASE_URL}/property/${propertyId}/amenities`;
      console.log('🏢 Request URL:', url);
      
      const response = await axios.get(url);
      console.log('🏢 Amenities response:', response.data);
      
      return this.standardizeResponse(response.data);
    } catch (error) {
      console.error('💥 Amenities error:', error);
      return this.handleError(error, 'Failed to retrieve amenities');
    }
  }

  async negotiatePrice(propertyId, offer) {
    console.log('💰 =================================');
    console.log('💰 NEGOTIATE PRICE STARTED');
    console.log('💰 =================================');
    console.log('💰 Property ID:', propertyId);
    console.log('💰 Offer amount:', offer);
    
    try {
      if (!propertyId || !offer || offer <= 0) {
        throw new Error('Invalid property ID or offer amount');
      }

      const url = `${API_BASE_URL}/property/${propertyId}/negotiate`;
      const payload = { offer: parseFloat(offer) };
      
      console.log('💰 Request URL:', url);
      console.log('💰 Request payload:', payload);
      
      const response = await axios.post(url, payload);
      console.log('💰 Negotiation response:', response.data);
      
      return this.standardizeResponse(response.data);
    } catch (error) {
      console.error('💥 Negotiation error:', error);
      return this.handleError(error, 'Failed to process negotiation');
    }
  }

  async finalizeDeal(propertyId, dealDetails = {}) {
    console.log('🤝 =================================');
    console.log('🤝 FINALIZE DEAL STARTED');
    console.log('🤝 =================================');
    console.log('🤝 Property ID:', propertyId);
    console.log('🤝 Deal details:', dealDetails);
    
    try {
      if (!propertyId) {
        throw new Error('Invalid property ID');
      }

      const url = `${API_BASE_URL}/property/${propertyId}/close-deal`;
      console.log('🤝 Request URL:', url);
      
      const response = await axios.post(url, dealDetails);
      console.log('🤝 Deal finalization response:', response.data);
      
      return this.standardizeResponse(response.data);
    } catch (error) {
      console.error('💥 Deal finalization error:', error);
      return this.handleError(error, 'Failed to finalize deal');
    }
  }

  // Utility methods
  standardizeResponse(data) {
    console.log('🔄 Standardizing response:', data);
    
    const standardized = {
      status: data.status || 'success',
      message: data.message || 'Success',
      data: data.data || data,
      timestamp: data.timestamp || new Date().toISOString()
    };
    
    console.log('🔄 Standardized result:', standardized);
    return standardized;
  }

  handleError(error, defaultMessage) {
    console.log('🚨 Handling error:', error);
    console.log('🚨 Default message:', defaultMessage);
    
    let errorMessage = defaultMessage;
    
    if (error.response?.data?.message) {
      errorMessage = error.response.data.message;
    } else if (error.message) {
      errorMessage = error.message;
    }

    const errorResponse = {
      status: 'error',
      message: errorMessage,
      data: {},
      timestamp: new Date().toISOString()
    };
    
    console.log('🚨 Final error response:', errorResponse);
    return errorResponse;
  }
}

// Create and export singleton instance
console.log('🏗️ Creating RealEstateService instance...');
const realEstateService = new RealEstateService();
console.log('🏗️ RealEstateService instance created:', realEstateService);

export default realEstateService;
