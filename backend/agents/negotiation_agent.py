from .base_agent import BaseAgent
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class NegotiationAgent(BaseAgent):
    """
    Intelligent negotiation agent that handles property price negotiations
    with realistic market-based responses
    """
    
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager

    def negotiate(self, property_id: int, offer_amount: float) -> Dict[str, Any]:
        """Handle property price negotiation with intelligent responses"""
        try:
            logger.info(f"Processing negotiation for property {property_id}, offer: ${offer_amount:,.2f}")
            
            # Get property data
            property_data = self.db_manager.get_property(property_id)
            if not property_data:
                return self._standardize_response(
                    "error",
                    f"Property {property_id} not found",
                    {}
                )
            
            # Analyze the offer
            analysis = self._analyze_offer(property_data, offer_amount)
            
            # Generate negotiation response
            negotiation_response = self._generate_negotiation_response(property_data, offer_amount, analysis)
            
            # Determine next steps
            next_steps = self._determine_next_steps(analysis)
            
            return self._standardize_response(
                "success",
                negotiation_response['message'],
                {
                    "property_id": property_id,
                    "original_price": property_data['price'],
                    "offer_amount": offer_amount,
                    "offer_analysis": analysis,
                    "negotiation_status": negotiation_response['status'],
                    "counter_offer": negotiation_response.get('counter_offer'),
                    "next_steps": next_steps,
                    "market_insights": self._get_market_insights(property_data, analysis),
                    "timeline": self._get_negotiation_timeline(negotiation_response['status'])
                }
            )
            
        except Exception as e:
            logger.error(f"Error in negotiation for property {property_id}: {e}")
            return self._standardize_response(
                "error",
                f"Failed to process negotiation: {str(e)}",
                {}
            )

    def _analyze_offer(self, property_data: Dict[str, Any], offer_amount: float) -> Dict[str, Any]:
        """Analyze the offer against market conditions and property value"""
        list_price = property_data['price']
        difference = list_price - offer_amount
        percentage_below = (difference / list_price) * 100
        
        # Property characteristics for analysis
        bedrooms = property_data.get('bedrooms', 0)
        city = property_data.get('city', '')
        property_type = property_data.get('property_type', '')
        year_built = property_data.get('year_built', 2000)
        
        # Market factors (simulated - in real implementation, get from market data API)
        market_factors = self._get_market_factors(city, property_type)
        
        # Determine offer strength
        if percentage_below < 0:  # Offer above asking
            strength = "above_asking"
        elif percentage_below <= 2:
            strength = "very_strong"
        elif percentage_below <= 5:
            strength = "strong"
        elif percentage_below <= 10:
            strength = "reasonable"
        elif percentage_below <= 15:
            strength = "low"
        else:
            strength = "very_low"
        
        return {
            "list_price": list_price,
            "offer_amount": offer_amount,
            "difference": difference,
            "percentage_below": round(percentage_below, 2),
            "strength": strength,
            "market_factors": market_factors,
            "property_age": 2024 - year_built,
            "competition_level": self._assess_competition(city, property_type, list_price)
        }

    def _generate_negotiation_response(self, property_data: Dict[str, Any], 
                                     offer_amount: float, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate intelligent negotiation response using AI"""
        try:
            list_price = property_data['price']
            address = property_data['address']
            strength = analysis['strength']
            percentage_below = analysis['percentage_below']
            market_factors = analysis['market_factors']
            
            negotiation_prompt = f"""
            Generate a realistic seller response to this real estate offer:
            
            Property: {property_data['property_type']} at {address}
            List Price: ${list_price:,.2f}
            Offer: ${offer_amount:,.2f}
            Difference: {percentage_below:.1f}% below asking
            Offer Strength: {strength}
            Market Conditions: {market_factors['condition']}
            Days on Market: {market_factors['days_on_market']}
            Competition: {analysis['competition_level']}
            
            Return JSON with realistic seller response:
            {{
                "status": "accepted|counter_offered|rejected|under_review",
                "message": "detailed seller response message",
                "counter_offer": number or null,
                "reasoning": "explanation of decision",
                "urgency": "high|medium|low",
                "flexibility": "high|medium|low"
            }}
            
            Guidelines:
            - Above asking or <2% below: likely accepted
            - 2-5% below: strong offers, might accept or small counter
            - 5-10% below: reasonable, expect counter-offer
            - 10-15% below: low offers, significant counter or rejection
            - >15% below: very low, likely rejection
            - Consider market conditions and competition
            """
            
            default_response = self._get_default_negotiation_response(strength, list_price, offer_amount)
            
            ai_response = self.generate_structured_response_sync(negotiation_prompt, default_response)
            
            # Validate and adjust response
            return self._validate_negotiation_response(ai_response, analysis)
            
        except Exception as e:
            logger.error(f"Error generating negotiation response: {e}")
            return self._get_default_negotiation_response(analysis['strength'], list_price, offer_amount)

    def _get_market_factors(self, city: str, property_type: str) -> Dict[str, Any]:
        """Simulate market factors (in real implementation, fetch from market data API)"""
        # Market conditions by city (simulated)
        market_conditions = {
            'San Francisco': {'condition': 'hot', 'avg_days': 15, 'price_trend': 'rising'},
            'New York City': {'condition': 'competitive', 'avg_days': 25, 'price_trend': 'stable'},
            'Los Angeles': {'condition': 'warm', 'avg_days': 20, 'price_trend': 'rising'},
            'Chicago': {'condition': 'balanced', 'avg_days': 35, 'price_trend': 'stable'},
            'Miami': {'condition': 'hot', 'avg_days': 18, 'price_trend': 'rising'},
            'Austin': {'condition': 'warm', 'avg_days': 22, 'price_trend': 'rising'},
            'Houston': {'condition': 'balanced', 'avg_days': 30, 'price_trend': 'stable'}
        }
        
        default_market = {'condition': 'balanced', 'avg_days': 30, 'price_trend': 'stable'}
        market = market_conditions.get(city, default_market)
        
        return {
            'condition': market['condition'],
            'days_on_market': random.randint(max(1, market['avg_days'] - 10), market['avg_days'] + 10),
            'price_trend': market['price_trend'],
            'inventory_level': random.choice(['low', 'normal', 'high']),
            'season': self._get_market_season()
        }

    def _assess_competition(self, city: str, property_type: str, price: float) -> str:
        """Assess competition level for similar properties"""
        # In real implementation, query database for similar properties
        # For now, simulate based on city and price range
        
        if city in ['San Francisco', 'New York City'] and price > 1000000:
            return random.choice(['very_high', 'high'])
        elif city in ['San Francisco', 'New York City', 'Los Angeles']:
            return random.choice(['high', 'medium'])
        else:
            return random.choice(['medium', 'low'])

    def _get_market_season(self) -> str:
        """Get current market season"""
        month = datetime.now().month
        if month in [3, 4, 5]:
            return 'spring_peak'
        elif month in [6, 7, 8]:
            return 'summer_active'
        elif month in [9, 10]:
            return 'fall_moderate'
        else:
            return 'winter_slow'

    def _get_default_negotiation_response(self, strength: str, list_price: float, offer_amount: float) -> Dict[str, Any]:
        """Get default negotiation response based on offer strength"""
        responses = {
            "above_asking": {
                "status": "accepted",
                "message": "Excellent! Your above-asking offer has been accepted.",
                "counter_offer": None,
                "reasoning": "Strong offer above asking price",
                "urgency": "high",
                "flexibility": "low"
            },
            "very_strong": {
                "status": "accepted",
                "message": "Great offer! The seller has accepted your proposal.",
                "counter_offer": None,
                "reasoning": "Very competitive offer",
                "urgency": "high",
                "flexibility": "low"
            },
            "strong": {
                "status": "counter_offered",
                "message": "Strong offer! The seller would like to counter.",
                "counter_offer": round(list_price - (list_price - offer_amount) * 0.5, -3),
                "reasoning": "Good offer, minor adjustment requested",
                "urgency": "medium",
                "flexibility": "medium"
            },
            "reasonable": {
                "status": "counter_offered",
                "message": "Reasonable offer. The seller is interested but would like to negotiate.",
                "counter_offer": round(list_price * 0.95, -3),
                "reasoning": "Fair offer, counter-proposal made",
                "urgency": "medium",
                "flexibility": "medium"
            },
            "low": {
                "status": "counter_offered",
                "message": "The seller appreciates your interest but feels the offer is below market value.",
                "counter_offer": round(list_price * 0.92, -3),
                "reasoning": "Significant counter-offer due to low initial offer",
                "urgency": "low",
                "flexibility": "high"
            },
            "very_low": {
                "status": "rejected",
                "message": "Unfortunately, the seller cannot accept this offer as it's significantly below market value.",
                "counter_offer": None,
                "reasoning": "Offer too far below asking price",
                "urgency": "low",
                "flexibility": "low"
            }
        }
        
        return responses.get(strength, responses["reasonable"])

    def _validate_negotiation_response(self, response: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and adjust AI-generated negotiation response"""
        try:
            # Ensure required fields exist
            required_fields = ['status', 'message', 'reasoning', 'urgency', 'flexibility']
            for field in required_fields:
                if field not in response:
                    response[field] = "Not specified"
            
            # Validate status
            valid_statuses = ['accepted', 'counter_offered', 'rejected', 'under_review']
            if response['status'] not in valid_statuses:
                response['status'] = 'under_review'
            
            # Validate counter offer
            if response['status'] == 'counter_offered' and 'counter_offer' in response:
                counter_offer = response['counter_offer']
                if counter_offer and isinstance(counter_offer, (int, float)):
                    list_price = analysis['list_price']
                    offer_amount = analysis['offer_amount']
                    # Ensure counter offer is between offer and list price
                    response['counter_offer'] = max(offer_amount, min(counter_offer, list_price))
            
            return response
            
        except Exception as e:
            logger.error(f"Error validating negotiation response: {e}")
            return self._get_default_negotiation_response(analysis['strength'], 
                                                        analysis['list_price'], 
                                                        analysis['offer_amount'])

    def _determine_next_steps(self, analysis: Dict[str, Any]) -> list[str]:
        """Determine recommended next steps based on negotiation outcome"""
        strength = analysis['strength']
        
        if strength in ['above_asking', 'very_strong']:
            return [
                "Congratulations! Proceed with contract preparation",
                "Schedule property inspection within 7-10 days",
                "Begin mortgage/financing paperwork",
                "Review closing timeline with your agent"
            ]
        elif strength == 'strong':
            return [
                "Consider the counter-offer carefully",
                "Review your budget and financing options",
                "You may counter-offer again if needed",
                "Act quickly as this is a competitive offer"
            ]
        elif strength == 'reasonable':
            return [
                "Review the seller's counter-offer",
                "Consider market conditions in your response",
                "You have room to negotiate further",
                "Consult with your real estate agent"
            ]
        elif strength == 'low':
            return [
                "Consider increasing your offer significantly",
                "Review comparable sales in the area",
                "Assess if this property fits your budget",
                "Explore other similar properties"
            ]
        else:  # very_low or rejected
            return [
                "Consider a substantially higher offer",
                "Review your budget constraints", 
                "Look for similar properties in your price range",
                "Reassess your target criteria"
            ]

    def _get_market_insights(self, property_data: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Provide market insights to help buyer understand the negotiation"""
        return {
            "market_condition": analysis['market_factors']['condition'],
            "competition_level": analysis['competition_level'],
            "price_trend": analysis['market_factors']['price_trend'],
            "days_on_market": analysis['market_factors']['days_on_market'],
            "negotiation_tip": self._get_negotiation_tip(analysis),
            "comparable_sales": "Recent sales in this area range from $X to $Y"  # Would fetch real data
        }

    def _get_negotiation_tip(self, analysis: Dict[str, Any]) -> str:
        """Provide personalized negotiation tip"""
        strength = analysis['strength']
        market_condition = analysis['market_factors']['condition']
        
        if market_condition == 'hot' and strength in ['low', 'very_low']:
            return "In this hot market, consider a more competitive offer to avoid losing the property."
        elif market_condition == 'balanced' and strength == 'reasonable':
            return "This balanced market gives you some negotiating power. Your offer is fair."
        elif market_condition == 'slow' and strength in ['strong', 'very_strong']:
            return "Your strong offer in this slower market puts you in an excellent position."
        else:
            return "Consider market conditions and comparable sales when making your next move."

    def _get_negotiation_timeline(self, status: str) -> Dict[str, Any]:
        """Get expected timeline for negotiation process"""
        timelines = {
            "accepted": {
                "contract_preparation": "1-2 days",
                "inspection_period": "7-10 days", 
                "financing_approval": "14-21 days",
                "closing": "30-45 days"
            },
            "counter_offered": {
                "response_expected": "24-48 hours",
                "final_negotiation": "3-7 days",
                "contract_preparation": "1-2 days after acceptance"
            },
            "under_review": {
                "seller_response": "24-72 hours",
                "potential_counter": "3-5 days"
            },
            "rejected": {
                "new_offer_consideration": "Consider immediately",
                "alternative_properties": "Begin searching now"
            }
        }
        
        return timelines.get(status, {"next_step": "24-48 hours"})
