// src/utils/errorHandler.js
export const handleApiError = (error) => {
  console.error('API Error:', error);
  
  // Create a standardized error response matching your backend format
  const createErrorResponse = (message) => ({
    status: "error",
    message: message,
    data: {},
    timestamp: new Date().toISOString()
  });
  
  if (error.message.includes('timeout')) {
    return createErrorResponse("The request timed out. Please check your connection and try again.");
  }
  
  if (error.message.includes('Failed to fetch') || error.message.includes('connect')) {
    return createErrorResponse("Unable to connect to the server. Please check if the server is running.");
  }
  
  if (error.message.includes('500')) {
    return createErrorResponse("Server error occurred. Please try again later.");
  }
  
  if (error.message.includes('404')) {
    return createErrorResponse("The requested resource was not found.");
  }
  
  return createErrorResponse("An unexpected error occurred. Please try again later.");
};
