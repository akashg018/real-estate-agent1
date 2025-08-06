from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import os
import logging
from datetime import datetime
from database.db import init_db
from agents.orchestrator import OrchestratorAgent

# Load environment variables
load_dotenv()

# Configure logging
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

app = Flask(__name__, static_folder='build', static_url_path='/')  # Serve React static files

# CORS (adjust as needed)
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
logger.info("CORS configured for API endpoints")

orchestrator = None

def get_orchestrator():
    global orchestrator
    if orchestrator is None:
        try:
            orchestrator = OrchestratorAgent()
            logger.info("Orchestrator initialized successfully")
        except Exception as e:
            logger.error(f"Orchestrator initialization failed: {e}")
            raise
    return orchestrator

# Initialize DB
try:
    init_db()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Database initialization failed: {e}")

# API ROUTES

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        init_db()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
        logger.error(f"Database health check failed: {e}")

    try:
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

@app.route('/api/chat', methods=['POST', 'OPTIONS'])
def chat():
    """Chat endpoint - handles both 'message' and 'query' parameters for compatibility"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    try:
        data = request.get_json()
        if not data:
            logger.warning("Chat request missing JSON data")
            return jsonify({
                "status": "error",
                "message": "JSON data is required",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        # Support both 'message' and 'query' for frontend compatibility
        user_query = data.get('message') or data.get('query', '').strip()
        
        if not user_query:
            logger.warning("Chat request missing message/query parameter")
            return jsonify({
                "status": "error",
                "message": "Message or query is required",
                "timestamp": datetime.now().isoformat()
            }), 400

        logger.info(f"Processing chat query: {user_query[:100]}...")
        
        orch = get_orchestrator()
        response = orch.handle_query(user_query)
        
        # Ensure response is properly formatted
        if not isinstance(response, dict):
            response = {
                "status": "success",
                "message": "Query processed successfully",
                "response": str(response),
                "timestamp": datetime.now().isoformat()
            }
        elif 'timestamp' not in response:
            response['timestamp'] = datetime.now().isoformat()
        
        logger.info("Chat query processed successfully")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": "Server error occurred while processing your request",
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
        
        logger.info(f"Fetching property details for ID: {property_id}")
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
            "message": "Property details retrieved successfully",
            "data": property_data,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Property details error: {str(e)}", exc_info=True)
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
        
        logger.info(f"Fetching amenities for property ID: {property_id}")
        orch = get_orchestrator()
        response = orch.get_property_amenities(property_id)
        
        if 'timestamp' not in response:
            response['timestamp'] = datetime.now().isoformat()
            
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Amenities error: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": "Failed to retrieve amenities",
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/property/<int:property_id>/negotiate', methods=['POST'])
def negotiate_property(property_id):
    """Handle price negotiations for a property"""
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
                "message": "Invalid offer amount - must be a positive number",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        logger.info(f"Processing negotiation for property {property_id} with offer: {offer_amount}")
        orch = get_orchestrator()
        response = orch.handle_negotiation(property_id, offer_amount)
        
        if 'timestamp' not in response:
            response['timestamp'] = datetime.now().isoformat()
            
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Negotiation error: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": "Failed to process negotiation",
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/property/<int:property_id>/close-deal', methods=['POST'])
def close_deal(property_id):
    """Close a deal for a property"""
    try:
        if property_id <= 0:
            return jsonify({
                "status": "error",
                "message": "Invalid property ID",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        data = request.get_json() or {}
        logger.info(f"Closing deal for property ID: {property_id}")
        
        orch = get_orchestrator()
        response = orch.close_deal(property_id, data)
        
        if 'timestamp' not in response:
            response['timestamp'] = datetime.now().isoformat()
            
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Deal closing error: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": "Failed to close deal",
            "timestamp": datetime.now().isoformat()
        }), 500

# Add a route to list all available endpoints for debugging
@app.route('/api/routes', methods=['GET'])
def list_routes():
    """List all available API routes for debugging"""
    try:
        routes = []
        for rule in app.url_map.iter_rules():
            if rule.endpoint != 'static':
                routes.append({
                    'endpoint': rule.endpoint,
                    'methods': list(rule.methods - {'HEAD', 'OPTIONS'}),
                    'rule': str(rule)
                })
        return jsonify({
            "status": "success",
            "routes": routes,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Routes listing error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Failed to list routes",
            "timestamp": datetime.now().isoformat()
        }), 500

# ---- Serve React static files ----
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react_app(path):
    """Serve React app and handle client-side routing"""
    # Handle API routes that don't exist
    if path.startswith('api/'):
        logger.warning(f"API endpoint not found: /{path}")
        return jsonify({
            "status": "error",
            "message": "API endpoint not found",
            "timestamp": datetime.now().isoformat()
        }), 404
    
    # Serve static files from React build directory
    react_build_dir = os.path.join(os.path.dirname(__file__), "build")
    
    # Check if specific file exists
    if path != "" and os.path.exists(os.path.join(react_build_dir, path)):
        return send_from_directory(react_build_dir, path)
    
    # Default to serving index.html for client-side routing
    try:
        return send_from_directory(react_build_dir, 'index.html')
    except Exception as e:
        logger.error(f"Error serving React app: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Frontend application not found",
            "timestamp": datetime.now().isoformat()
        }), 404

# ERROR HANDLERS
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    logger.warning(f"404 error: {request.url}")
    return jsonify({
        "status": "error",
        "message": "Endpoint not found",
        "timestamp": datetime.now().isoformat()
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}", exc_info=True)
    return jsonify({
        "status": "error",
        "message": "Internal server error",
        "timestamp": datetime.now().isoformat()
    }), 500

@app.errorhandler(400)
def bad_request(error):
    """Handle 400 errors"""
    logger.warning(f"Bad request: {error}")
    return jsonify({
        "status": "error",
        "message": "Bad request",
        "timestamp": datetime.now().isoformat()
    }), 400

@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors"""
    logger.warning(f"Method not allowed: {request.method} {request.url}")
    return jsonify({
        "status": "error",
        "message": "Method not allowed",
        "timestamp": datetime.now().isoformat()
    }), 405

if __name__ == '__main__':
    # Use PORT environment variable for deployment platforms
    port = int(os.getenv('PORT', 4000))
    debug_mode = os.getenv('FLASK_ENV') != 'production'
    host = '0.0.0.0' if os.getenv('FLASK_ENV') == 'production' else 'localhost'

    logger.info(f"Starting Real Estate AI Agent on {host}:{port}")
    logger.info(f"Environment: {os.getenv('FLASK_ENV', 'development')}")
    logger.info(f"Debug mode: {debug_mode}")
    logger.info(f"Static folder: {app.static_folder}")

    app.run(host=host, port=port, debug=debug_mode)
