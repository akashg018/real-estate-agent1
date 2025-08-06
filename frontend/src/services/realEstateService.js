import axios from 'axios';

// Configure base URL to use deployed backend
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'https://real-estate-agent1-2.onrender.com/api';

console.log('🔧 API Base URL configured:', API_BASE_URL);

// Configure axios defaults
axios.defaults.timeout = 15000; // 15 seconds
axios.defaults.headers.common['Content-Type'] = 'application/json';

class RealEstateService {
  constructor() {
    this.axios = axios.create({
      baseURL: API_BASE_URL,
      timeout: 15000,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
    });
    
    // Request interceptor
    this.axios.interceptors.request.use(
      (config) => {
        console.log(`📤 Request: [${config.method?.toUpperCase()}] ${config.baseURL}${config.url}`);
        return config;
      },
      (error) => {
        console.error('❌ Request error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.axios.interceptors.response.use(
      (response) => {
        console.log(`📥 Response: [${response.status}] Success`);
        return response;
      },
      (error) => {
        console.error('❌ Response error:', error.message);
        
        // Return standardized error response
        const errorResponse = {
          data: {
            status: 'error',
            message: this.getErrorMessage(error),
            timestamp: new Date().toISOString()
          }
        };
        
        return Promise.resolve(errorResponse);
      }
    );
  }

  getErrorMessage(error) {
    if (error.code === 'ERR_NETWORK') {
      return 'Unable to connect to the server. Please check your internet connection.';
    }
    if (error.code === 'ECONNABORTED') {
      return 'Request timeout. Please try again.';
    }
    if (error.response?.data?.message) {
      return error.response.data.message;
    }
    return error.message || 'An unexpected error occurred';
  }

  async checkHealth() {
    try {
      console.log('🏥 Checking health...');
      const response = await this.axios.get('/health');
      return response.data;
    } catch (error) {
      console.error('💔 Health check failed:', error);
      throw error;
    }
  }

  async chatQuery(query) {
    console.log('🚀 CHAT QUERY STARTED');

    const maxRetries = 3;
    let retryCount = 0;
    let lastError = null;

    while (retryCount < maxRetries) {
      try {
        console.log(`⏳ Attempt ${retryCount + 1} of ${maxRetries}`);
        const startTime = Date.now();
        
        // Use 'message' to match your updated backend
        const response = await this.axios.post('/chat', 
          { message: query }, // Fixed: use 'message' instead of 'query'
          {
            timeout: 15000,
            headers: {
              'Content-Type': 'application/json',
              'Accept': 'application/json'
            }
          }
        );

        const endTime = Date.now();
        console.log(`⏱️ Completed in ${endTime - startTime}ms`);
        return this.standardizeResponse(response.data);

      } catch (error) {
        lastError = error;
        retryCount++;
        console.log(`❌ Attempt ${retryCount} failed:`, this.getErrorMessage(error));
        
        if (retryCount < maxRetries) {
          const delay = Math.min(1000 * Math.pow(2, retryCount), 5000);
          console.log(`⏳ Retrying after ${delay}ms...`);
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
    }

    console.log('💥 All retry attempts failed');
    return this.handleError(lastError, 'Failed to connect after multiple attempts');
  }

  async getPropertyAmenities(propertyId) {
    console.log('🏢 Fetching amenities for property ID:', propertyId);
    
    try {
      const response = await this.axios.get(`/property/${propertyId}/amenities`);
      const data = response.data;

      console.log('✅ Amenities response received');

      const amenitiesData = data.data && data.data.amenities ? data.data.amenities : data.amenities;
      
      return this.standardizeResponse({
        status: data.status || 'success',
        message: data.message || 'Amenities retrieved successfully',
        data: {
          amenities: amenitiesData || [],
          property_info: data.data?.property_info || {},
          amenity_score: data.data?.amenity_score || {}
        },
        timestamp: data.timestamp || new Date().toISOString()
      });
    } catch (error) {
      console.error('💥 Amenities error:', error);
      return this.handleError(error, 'Failed to retrieve amenities');
    }
  }

  async negotiatePrice(propertyId, offer) {
    console.log('💰 Negotiating price for property ID:', propertyId);
    
    try {
      if (!propertyId || !offer || offer <= 0) {
        throw new Error('Invalid property ID or offer amount');
      }

      const payload = { offer: parseFloat(offer) };
      const response = await this.axios.post(`/property/${propertyId}/negotiate`, payload);
      return this.standardizeResponse(response.data);
    } catch (error) {
      console.error('💥 Negotiation error:', error);
      return this.handleError(error, 'Failed to process negotiation');
    }
  }

  async finalizeDeal(propertyId, dealDetails = {}) {
    console.log('🤝 Finalizing deal for property ID:', propertyId);
    
    try {
      if (!propertyId) {
        throw new Error('Invalid property ID');
      }

      const response = await this.axios.post(`/property/${propertyId}/close-deal`, dealDetails);
      return this.standardizeResponse(response.data);
    } catch (error) {
      console.error('💥 Deal finalization error:', error);
      return this.handleError(error, 'Failed to finalize deal');
    }
  }

  // Utility methods
  standardizeResponse(data) {
    return {
      status: data.status || 'success',
      message: data.message || 'Success',
      data: data.data || data,
      timestamp: data.timestamp || new Date().toISOString()
    };
  }

  handleError(error, defaultMessage) {
    let errorMessage = defaultMessage;
    
    if (error.response?.data?.message) {
      errorMessage = error.response.data.message;
    } else if (error.message) {
      errorMessage = error.message;
    }

    return {
      status: 'error',
      message: errorMessage,
      data: {},
      timestamp: new Date().toISOString()
    };
  }
}

// Create and export singleton instance
const realEstateService = new RealEstateService();

export default realEstateService;
