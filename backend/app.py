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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Configure CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    
    # Initialize orchestrator
    try:
        orchestrator = OrchestratorAgent()
        logger.info("Orchestrator initialized successfully")
    except Exception as e:
        logger.error(f"Orchestrator initialization failed: {e}")
        raise
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "status": "error",
            "message": "Endpoint not found",
            "timestamp": datetime.now().isoformat()
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            "status": "error",
            "message": "Internal server error",
            "timestamp": datetime.now().isoformat()
        }), 500
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        return jsonify({
            "status": "success",
            "message": "Real Estate AI Agent is running",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        })
    
    @app.route('/api/chat', methods=['POST'])
    def chat():
        try:
            print("🚀" + "="*50)
            print("🚀 FRONTEND REQUEST RECEIVED")
            print("🚀" + "="*50)
            
            # Log request details
            print(f"📍 Request method: {request.method}")
            print(f"📍 Request headers: {dict(request.headers)}")
            print(f"📍 Request origin: {request.headers.get('Origin', 'Not specified')}")
            print(f"📍 Content-Type: {request.headers.get('Content-Type', 'Not specified')}")
            
            data = request.get_json()
            print(f"📍 Raw request data: {data}")
            print(f"📍 Data type: {type(data)}")
            
            if not data or 'query' not in data:
                print("❌ No query in request")
                return jsonify({
                    "status": "error",
                    "message": "Query is required",
                    "timestamp": datetime.now().isoformat()
                }), 400
            
            user_query = data['query'].strip()
            print(f"📝 Processing query: '{user_query}'")
            print(f"📝 Query type: {type(user_query)}")
            print(f"📝 Query length: {len(user_query)}")
            
            # Test orchestrator existence
            print(f"🔧 Orchestrator type: {type(orchestrator)}")
            print(f"🔧 Orchestrator methods: {dir(orchestrator)}")
            
            if not hasattr(orchestrator, 'handle_query'):
                print("❌ ERROR: Orchestrator missing handle_query method")
                return jsonify({
                    "status": "error",
                    "message": "Orchestrator not properly configured",
                    "timestamp": datetime.now().isoformat()
                }), 500
            
            # Call orchestrator with detailed logging
            print("⚡ Calling orchestrator.handle_query()...")
            try:
                response = orchestrator.handle_query(user_query)
                print(f"✅ Orchestrator response type: {type(response)}")
                print(f"✅ Orchestrator response: {response}")
                
                # Validate response structure
                if not isinstance(response, dict):
                    print(f"❌ Invalid response type: {type(response)}")
                    return jsonify({
                        "status": "error",
                        "message": "Invalid response format",
                        "timestamp": datetime.now().isoformat()
                    }), 500
                
                # Ensure response has required fields
                if 'status' not in response:
                    response['status'] = 'error'
                if 'message' not in response:
                    response['message'] = 'No message provided'
                if 'data' not in response:
                    response['data'] = {}
                if 'timestamp' not in response:
                    response['timestamp'] = datetime.now().isoformat()
                
                print(f"🎉 Sending response to frontend: {response}")
                return jsonify(response)
                
            except Exception as orchestrator_error:
                print(f"💥 ORCHESTRATOR ERROR: {str(orchestrator_error)}")
                print(f"💥 Error type: {type(orchestrator_error)}")
                import traceback
                traceback.print_exc()
                
                return jsonify({
                    "status": "error",
                    "message": f"Orchestrator failed: {str(orchestrator_error)}",
                    "timestamp": datetime.now().isoformat()
                }), 500
            
        except Exception as e:
            print(f"💥 CRITICAL ERROR: {str(e)}")
            print(f"💥 Error type: {type(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                "status": "error",
                "message": f"Server error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }), 500

    
    @app.route('/api/property/<int:property_id>', methods=['GET'])
    def get_property_details(property_id):
        """Get detailed information about a specific property"""
        try:
            property_data = orchestrator.db_manager.get_property(property_id)
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
            response = orchestrator.get_property_amenities(property_id)
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
            data = request.get_json()
            if not data or 'offer' not in data:
                return jsonify({
                    "status": "error",
                    "message": "Offer amount is required",
                    "timestamp": datetime.now().isoformat()
                }), 400
            
            offer_amount = float(data['offer'])
            response = orchestrator.handle_negotiation(property_id, offer_amount)
            return jsonify(response)
            
        except ValueError:
            return jsonify({
                "status": "error",
                "message": "Invalid offer amount",
                "timestamp": datetime.now().isoformat()
            }), 400
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
            data = request.get_json() or {}
            response = orchestrator.close_deal(property_id, data)
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
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
