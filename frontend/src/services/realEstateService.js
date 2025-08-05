import axios from 'axios';

// Configure base URL with fallback
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:4000/api';

// Configure axios defaults
axios.defaults.timeout = 30000; // 30 seconds
axios.defaults.headers.common['Content-Type'] = 'application/json';

class RealEstateService {
  constructor() {
    this.axios = axios.create({
      baseURL: API_BASE_URL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
    });
    
    // Request interceptor
    axios.interceptors.request.use(
      (config) => {
        // Minimal request logging
        console.log(`📤 Request: [${config.method?.toUpperCase()}] ${config.url}`);
        return config;
      },
      (error) => {
        console.error('❌ Request error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor
    axios.interceptors.response.use(
      (response) => {
        // Minimal response logging
        console.log(`📥 Response: [${response.status}] ${response.config.url}`);
        return response;
      },
      (error) => {
        console.error('❌ Response error:', error);
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

  async checkHealth() {
    try {
      const response = await axios.get(`${API_BASE_URL}/health`);
      return response.data;
    } catch (error) {
      console.error('Health check failed:', error);
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
        
        const response = await axios.post(`${API_BASE_URL}/chat`, 
          { query },
          {
            timeout: 10000,
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
        console.log(`❌ Attempt ${retryCount} failed:`, error.message);
        
        if (retryCount < maxRetries) {
          const delay = Math.min(1000 * Math.pow(2, retryCount), 5000);
          console.log(`⏳ Retry after ${delay}ms...`);
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
    }

    console.log('💥 All retry attempts failed');
    return this.handleError(lastError, 'Failed after multiple attempts');
  }

  async getPropertyAmenities(propertyId) {
    console.log('🏢 Fetching amenities for property ID:', propertyId);
    
    try {
      const url = `${API_BASE_URL}/property/${propertyId}/amenities`;
      const response = await axios.get(url);
      const data = response.data;

      // Add debug logging
      console.log('Amenities response:', data);

      // Check if we need to extract amenities from nested data structure
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

      const url = `${API_BASE_URL}/property/${propertyId}/negotiate`;
      const payload = { offer: parseFloat(offer) };
      
      const response = await axios.post(url, payload);
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

      const url = `${API_BASE_URL}/property/${propertyId}/close-deal`;
      const response = await axios.post(url, dealDetails);
      return this.standardizeResponse(response.data);
    } catch (error) {
      console.error('💥 Deal finalization error:', error);
      return this.handleError(error, 'Failed to finalize deal');
    }
  }

  // Utility methods
  standardizeResponse(data) {
    // No logging needed here for normal operation
    return {
      status: data.status || 'success',
      message: data.message || 'Success',
      data: data.data || data,
      timestamp: data.timestamp || new Date().toISOString()
    };
  }

  handleError(error, defaultMessage) {
    console.error('🚨 Handling error:', error);

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
