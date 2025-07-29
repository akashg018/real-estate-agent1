from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import logging
from datetime import datetime
from database.db import init_db
from agents.orchestrator import OrchestratorAgent

# Load environment variables
load_dotenv()

# Configure logging for production
log_level = logging.INFO if os.getenv('FLASK_ENV') == 'production' else logging.DEBUG
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log', mode='a') if os.getenv('FLASK_ENV') == 'production' else logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Production-ready CORS configuration
    allowed_origins = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000').split(',')
    cors_config = {
        r"/api/*": {
            "origins": allowed_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "Accept"],
            "supports_credentials": True
        }
    }
    
    CORS(app, resources=cors_config)
    logger.info(f"CORS configured for origins: {allowed_origins}")
    
    # Global orchestrator instance
    orchestrator = None
    
    def get_orchestrator():
        """Get or initialize orchestrator instance"""
        nonlocal orchestrator
        if orchestrator is None:
            try:
                orchestrator = OrchestratorAgent()
                logger.info("Orchestrator initialized successfully")
            except Exception as e:
                logger.error(f"Orchestrator initialization failed: {e}")
                raise
        return orchestrator
    
    # Initialize database on startup
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        # Don't raise here - let the app start and handle errors gracefully
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "status": "error",
            "message": "Endpoint not found",
            "timestamp": datetime.now().isoformat()
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return jsonify({
            "status": "error",
            "message": "Internal server error",
            "timestamp": datetime.now().isoformat()
        }), 500
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "status": "error",
            "message": "Bad request",
            "timestamp": datetime.now().isoformat()
        }), 400
    
    # Health check endpoint
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        try:
            # Test database connection
            init_db()
            db_status = "connected"
        except Exception as e:
            db_status = f"error: {str(e)}"
            logger.error(f"Database health check failed: {e}")
        
        try:
            # Test orchestrator
            orch = get_orchestrator()
            orchestrator_status = "initialized"
        except Exception as e:
            orchestrator_status = f"error: {str(e)}"
            logger.error(f"Orchestrator health check failed: {e}")
        
        return jsonify({
            "status": "success",
            "message": "Real Estate AI Agent is running",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "database": db_status,
            "orchestrator": orchestrator_status,
            "environment": os.getenv('FLASK_ENV', 'development')
        })
    
    @app.route('/api/chat', methods=['POST'])
    def chat():
        try:
            # Production logging (less verbose)
            if os.getenv('FLASK_ENV') != 'production':
                logger.info("Chat request received")
            
            data = request.get_json()
            if not data or 'query' not in data:
                logger.warning("Chat request missing query parameter")
                return jsonify({
                    "status": "error",
                    "message": "Query is required",
                    "timestamp": datetime.now().isoformat()
                }), 400
            
            user_query = data['query'].strip()
            if not user_query:
                return jsonify({
                    "status": "error",
                    "message": "Query cannot be empty",
                    "timestamp": datetime.now().isoformat()
                }), 400
            
            if len(user_query) > 1000:  # Reasonable limit
                return jsonify({
                    "status": "error",
                    "message": "Query too long (max 1000 characters)",
                    "timestamp": datetime.now().isoformat()
                }), 400
            
            logger.info(f"Processing query: {user_query[:50]}...")
            
            try:
                orch = get_orchestrator()
                
                if not hasattr(orch, 'handle_query'):
                    logger.error("Orchestrator missing handle_query method")
                    return jsonify({
                        "status": "error",
                        "message": "Service temporarily unavailable",
                        "timestamp": datetime.now().isoformat()
                    }), 503
                
                response = orch.handle_query(user_query)
                
                # Validate and standardize response
                if not isinstance(response, dict):
                    logger.error(f"Invalid response type from orchestrator: {type(response)}")
                    response = {
                        "status": "error",
                        "message": "Invalid response format",
                        "data": {},
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    # Ensure required fields
                    response.setdefault('status', 'success')
                    response.setdefault('message', 'Query processed successfully')
                    response.setdefault('data', {})
                    response.setdefault('timestamp', datetime.now().isoformat())
                
                logger.info("Query processed successfully")
                return jsonify(response)
                
            except Exception as orchestrator_error:
                logger.error(f"Orchestrator error: {str(orchestrator_error)}")
                return jsonify({
                    "status": "error",
                    "message": "Failed to process your request. Please try again.",
                    "timestamp": datetime.now().isoformat()
                }), 500
            
        except Exception as e:
            logger.error(f"Chat endpoint error: {str(e)}")
            return jsonify({
                "status": "error",
                "message": "Server error occurred",
                "timestamp": datetime.now().isoformat()
            }), 500
    
    @app.route('/api/property/<int:property_id>', methods=['GET'])
    def get_property_details(property_id):
        """Get detailed information about a specific property"""
        try:
            if property_id <= 0:
                return jsonify({
                    "status": "error",
                    "message": "Invalid property ID",
                    "timestamp": datetime.now().isoformat()
                }), 400
            
            orch = get_orchestrator()
            property_data = orch.db_manager.get_property(property_id)
            
            if not property_data:
                return jsonify({
                    "status": "error",
                    "message": f"Property {property_id} not found",
                    "timestamp": datetime.now().isoformat()
                }), 404
            
            return jsonify({
                "status": "success",
                "message": "Property details retrieved",
                "data": property_data,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Property details error: {str(e)}")
            return jsonify({
                "status": "error",
                "message": "Failed to retrieve property details",
                "timestamp": datetime.now().isoformat()
            }), 500
    
    @app.route('/api/property/<int:property_id>/amenities', methods=['GET'])
    def get_property_amenities(property_id):
        """Get amenities for a specific property"""
        try:
            if property_id <= 0:
                return jsonify({
                    "status": "error",
                    "message": "Invalid property ID",
                    "timestamp": datetime.now().isoformat()
                }), 400
            
            orch = get_orchestrator()
            response = orch.get_property_amenities(property_id)
            return jsonify(response)
            
        except Exception as e:
            logger.error(f"Amenities error: {str(e)}")
            return jsonify({
                "status": "error",
                "message": "Failed to retrieve amenities",
                "timestamp": datetime.now().isoformat()
            }), 500
    
    @app.route('/api/property/<int:property_id>/negotiate', methods=['POST'])
    def negotiate_property(property_id):
        """Handle property price negotiation"""
        try:
            if property_id <= 0:
                return jsonify({
                    "status": "error",
                    "message": "Invalid property ID",
                    "timestamp": datetime.now().isoformat()
                }), 400
            
            data = request.get_json()
            if not data or 'offer' not in data:
                return jsonify({
                    "status": "error",
                    "message": "Offer amount is required",
                    "timestamp": datetime.now().isoformat()
                }), 400
            
            try:
                offer_amount = float(data['offer'])
                if offer_amount <= 0:
                    raise ValueError("Offer must be positive")
            except (ValueError, TypeError):
                return jsonify({
                    "status": "error",
                    "message": "Invalid offer amount",
                    "timestamp": datetime.now().isoformat()
                }), 400
            
            orch = get_orchestrator()
            response = orch.handle_negotiation(property_id, offer_amount)
            return jsonify(response)
            
        except Exception as e:
            logger.error(f"Negotiation error: {str(e)}")
            return jsonify({
                "status": "error",
                "message": "Failed to process negotiation",
                "timestamp": datetime.now().isoformat()
            }), 500
    
    @app.route('/api/property/<int:property_id>/close-deal', methods=['POST'])
    def close_deal(property_id):
        """Finalize property deal and update database"""
        try:
            if property_id <= 0:
                return jsonify({
                    "status": "error",
                    "message": "Invalid property ID",
                    "timestamp": datetime.now().isoformat()
                }), 400
            
            data = request.get_json() or {}
            orch = get_orchestrator()
            response = orch.close_deal(property_id, data)
            return jsonify(response)
            
        except Exception as e:
            logger.error(f"Deal closing error: {str(e)}")
            return jsonify({
                "status": "error",
                "message": "Failed to close deal",
                "timestamp": datetime.now().isoformat()
            }), 500
    
    return app

# Create app instance
app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    
    logger.info(f"Starting Real Estate AI Agent on port {port}")
    logger.info(f"Environment: {os.getenv('FLASK_ENV', 'development')}")
    logger.info(f"Debug mode: {debug_mode}")
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
