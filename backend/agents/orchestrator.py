from .search_agent import PropertySearchAgent
from .amenities_agent import AmenitiesAgent
from .negotiation_agent import NegotiationAgent
from .closing_agent import DealClosingAgent
from database.database_manager import DatabaseManager
import re
import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class OrchestratorAgent:
    """
    Main orchestrator that intelligently routes user queries to specialized agents
    """
    
    def __init__(self):
        try:
            self.db_manager = DatabaseManager()
            self.search_agent = PropertySearchAgent(self.db_manager)
            self.amenities_agent = AmenitiesAgent(self.db_manager)
            self.negotiation_agent = NegotiationAgent(self.db_manager)
            self.closing_agent = DealClosingAgent(self.db_manager)
            
            # Query patterns for intelligent routing
            self.query_patterns = {
                'search': [
                    r'\b(find|search|looking|want|need|show)\b.*\b(property|properties|apartment|condo|house|home)\b',
                    r'\b\d+\s*(bhk|bedroom|br)\b',
                    r'\$\d+|budget.*\d+',
                    r'\b(rent|buy|purchase)\b'
                ],
                'amenities': [
                    r'\b(amenities|facilities|features)\b',
                    r'\bproperty\s+\d+.*\b(amenities|facilities)\b',
                    r'\b(gym|pool|parking|garden|security)\b'
                ],
                'negotiation': [
                    r'\b(offer|negotiate|bid|price)\b',
                    r'\$\d+.*\b(offer|bid)\b',
                    r'\b(counter|deal|bargain)\b'
                ],
                'closing': [
                    r'\b(close|finalize|complete|buy|purchase)\b.*\bdeal\b',
                    r'\b(closing|paperwork|contract|agreement)\b'
                ]
            }
            
            logger.info("Orchestrator initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}")
            raise

    def handle_query(self, user_query: str) -> Dict[str, Any]:
        """
        Main entry point - intelligently routes queries to appropriate agents
        """
        try:
            logger.info(f"Handling query: {user_query}")
            
            # Determine query intent
            intent = self._classify_query_intent(user_query)
            logger.info(f"Classified intent: {intent}")
            
            # Route to appropriate handler
            if intent == 'search':
                return self._handle_search_query(user_query)
            elif intent == 'amenities':
                return self._handle_amenities_query(user_query)
            elif intent == 'negotiation':
                return self._handle_negotiation_query(user_query)
            elif intent == 'closing':
                return self._handle_closing_query(user_query)
            else:
                return self._handle_general_query(user_query)
                
        except Exception as e:
            logger.error(f"Error handling query: {e}")
            return self._error_response(f"Failed to process your request: {str(e)}")

    def _classify_query_intent(self, query: str) -> str:
        """Classify user query intent using pattern matching"""
        query_lower = query.lower()
        
        # Check each pattern category
        for intent, patterns in self.query_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    return intent
        
        # Default to search if no specific pattern matches
        return 'search'

    def _handle_search_query(self, query: str) -> Dict[str, Any]:
        """Handle property search queries"""
        try:
            response = self.search_agent.process_query(query)
            
            # Enhance response with additional context
            if response.get('status') == 'success':
                properties = response.get('data', {}).get('properties', [])
                total = len(properties)
                
                if total > 0:
                    response['message'] = (
                        f"🏠 Found {total} properties matching your criteria! "
                        f"I've analyzed your requirements and here are the best matches. "
                        f"Would you like more details about any property or help with amenities/negotiations?"
                    )
                else:
                    response['message'] = (
                        "🔍 I couldn't find properties matching your exact criteria. "
                        "Let me suggest some alternatives or you can modify your search parameters. "
                        "What's most important to you - location, price, or specific features?"
                    )
            
            return response
            
        except Exception as e:
            logger.error(f"Search query error: {e}")
            return self._error_response("Failed to search properties")

    def _handle_amenities_query(self, query: str) -> Dict[str, Any]:
        """Handle amenities-related queries"""
        try:
            # Extract property ID if mentioned
            property_id = self._extract_property_id(query)
            
            if property_id:
                return self.get_property_amenities(property_id)
            else:
                return {
                    "status": "info",
                    "message": "🏢 I'd be happy to tell you about amenities! Please specify which property you're interested in by mentioning the property ID, or search for properties first.",
                    "data": {},
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Amenities query error: {e}")
            return self._error_response("Failed to retrieve amenities")

    def _handle_negotiation_query(self, query: str) -> Dict[str, Any]:
        """Handle negotiation-related queries"""
        try:
            property_id = self._extract_property_id(query)
            offer_amount = self._extract_offer_amount(query)
            
            if property_id and offer_amount:
                return self.handle_negotiation(property_id, offer_amount)
            else:
                return {
                    "status": "info",
                    "message": "💰 I can help you negotiate! Please specify the property ID and your offer amount. For example: 'I want to offer $450,000 for property 123'",
                    "data": {},
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Negotiation query error: {e}")
            return self._error_response("Failed to process negotiation")

    def _handle_closing_query(self, query: str) -> Dict[str, Any]:
        """Handle deal closing queries"""
        try:
            property_id = self._extract_property_id(query)
            
            if property_id:
                return self.close_deal(property_id, {})
            else:
                return {
                    "status": "info",
                    "message": "📋 Ready to close a deal? Please specify which property you'd like to finalize. For example: 'Close deal for property 123'",
                    "data": {},
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Closing query error: {e}")
            return self._error_response("Failed to process closing request")

    def _handle_general_query(self, query: str) -> Dict[str, Any]:
        """Handle general queries and provide guidance"""
        return {
            "status": "success",
            "message": (
                "👋 Hello! I'm your AI real estate assistant. I can help you with:\n\n"
                "🔍 **Property Search** - Find apartments, condos, and houses\n"
                "🏢 **Amenities Info** - Learn about property features and nearby facilities\n"
                "💰 **Price Negotiation** - Help you make competitive offers\n"
                "📋 **Deal Closing** - Guide you through the final steps\n\n"
                "Try asking something like:\n"
                "• 'Find 2BHK apartments in San Francisco under $500K'\n"
                "• 'Show amenities for property 123'\n"
                "• 'I want to offer $450K for property 123'"
            ),
            "data": {
                "suggestions": [
                    "Search for properties",
                    "View property amenities", 
                    "Make an offer",
                    "Get closing information"
                ]
            },
            "timestamp": datetime.now().isoformat()
        }

    def get_property_amenities(self, property_id: int) -> Dict[str, Any]:
        """Get amenities for a specific property"""
        try:
            response = self.amenities_agent.get_amenities(property_id)
            
            # Enhance with personalized message
            if response.get('status') == 'success':
                property_data = self.db_manager.get_property(property_id)
                if property_data:
                    response['message'] = (
                        f"🏢 Here are the amenities for the {property_data['property_type']} "
                        f"at {property_data['address']}. This property offers excellent "
                        f"value with these features!"
                    )
            
            return response
            
        except Exception as e:
            logger.error(f"Get amenities error: {e}")
            return self._error_response("Failed to retrieve amenities")

    def handle_negotiation(self, property_id: int, offer_amount: float) -> Dict[str, Any]:
        """Handle property negotiation"""
        try:
            response = self.negotiation_agent.negotiate(property_id, offer_amount)
            
            # Enhance with market context
            if response.get('status') == 'success':
                property_data = self.db_manager.get_property(property_id)
                if property_data:
                    list_price = property_data['price']
                    difference = ((list_price - offer_amount) / list_price) * 100
                    
                    if difference > 10:
                        response['message'] += f" Your offer is {difference:.1f}% below asking price. Consider a competitive offer to increase acceptance chances."
                    elif difference < 5:
                        response['message'] += f" Your offer is very competitive! You have a great chance of acceptance."
            
            return response
            
        except Exception as e:
            logger.error(f"Negotiation error: {e}")
            return self._error_response("Failed to process negotiation")

    def close_deal(self, property_id: int, deal_details: Dict[str, Any]) -> Dict[str, Any]:
        """Handle deal closing and update database"""
        try:
            # First, process the closing through the agent
            response = self.closing_agent.process_deal(property_id, deal_details)
            
            # If successful, update the database to mark property as unavailable
            if response.get('status') == 'success':
                success = self.db_manager.update_property_availability(property_id, False)
                
                if success:
                    response['message'] = (
                        "🎉 Congratulations! Your deal has been successfully closed. "
                        "The property is now marked as sold and removed from available listings. "
                        "You'll receive closing documents and next steps via email."
                    )
                    response['data']['database_updated'] = True
                else:
                    response['data']['database_updated'] = False
                    response['message'] += " (Note: Property status update pending)"
            
            return response
            
        except Exception as e:
            logger.error(f"Deal closing error: {e}")
            return self._error_response("Failed to close deal")

    def _extract_property_id(self, text: str) -> Optional[int]:
        """Extract property ID from text"""
        patterns = [
            r'property\s+(\d+)',
            r'property\s+id\s+(\d+)',
            r'#(\d+)',
            r'\bid\s+(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return int(match.group(1))
        return None

    def _extract_offer_amount(self, text: str) -> Optional[float]:
        """Extract offer amount from text"""
        patterns = [
            r'\$([0-9,]+(?:\.[0-9]{2})?)',
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:dollars?|usd|\$)',
            r'offer\s+(\d+(?:,\d{3})*)',
            r'bid\s+(\d+(?:,\d{3})*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    return float(amount_str)
                except ValueError:
                    continue
        return None

    def _error_response(self, message: str) -> Dict[str, Any]:
        """Generate standardized error response"""
        return {
            "status": "error",
            "message": f"❌ {message}",
            "data": {},
            "timestamp": datetime.now().isoformat()
        }

    def _success_response(self, message: str, data: Any = None) -> Dict[str, Any]:
        """Generate standardized success response"""
        return {
            "status": "success", 
            "message": f"✅ {message}",
            "data": data or {},
            "timestamp": datetime.now().isoformat()
        }
