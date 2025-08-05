from .base_agent import BaseAgent
import json
import re
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class PropertySearchAgent(BaseAgent):
    """
    Intelligent property search agent that processes natural language queries
    and returns relevant properties from the database
    """
    
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager

    def process_query(self, user_query: str) -> Dict[str, Any]:
        """Process natural language search query and return matching properties"""
        try:
            logger.info(f"Processing search query: {user_query}")
            
            # Step 1: Extract and validate search criteria
            search_criteria = self._extract_search_criteria(user_query)
            logger.info(f"Extracted criteria: {search_criteria}")
            
            # Add default property type if none specified
            if 'property_type' not in search_criteria:
                search_criteria['property_type'] = ['Apartment']
            
            # Ensure city is properly capitalized
            if 'city' in search_criteria:
                search_criteria['city'] = search_criteria['city'].title()
                logger.info(f"Searching for city: {search_criteria['city']}")
            
            # Step 2: Search database for matching properties
            properties = self.db_manager.search_properties(search_criteria)
            
            # Step 3: Generate intelligent response
            if not properties:
                return self._generate_no_results_response(search_criteria, user_query)
            
            # Step 4: Rank and filter properties
            ranked_properties = self._rank_properties(properties, search_criteria)
            
            # Step 5: Generate personalized summary
            summary = self._generate_search_summary(ranked_properties, search_criteria, user_query)
            
            return self._standardize_response(
                "success",
                summary,
                {
                    "properties": ranked_properties[:10],  # Top 10 matches
                    "total_found": len(properties),
                    "total_displayed": min(len(ranked_properties), 10),
                    "search_criteria": search_criteria,
                    "price_range": self._calculate_price_range(ranked_properties),
                    "locations": self._get_location_summary(ranked_properties)
                }
            )
            
        except Exception as e:
            logger.error(f"Error in property search: {e}")
            return self._standardize_response(
                "error",
                f"I encountered an issue while searching for properties: {str(e)}",
                {"properties": [], "total_found": 0}
            )

    def _extract_search_criteria(self, query: str) -> Dict[str, Any]:
        """Extract detailed search criteria from natural language"""
        try:
            criteria_prompt = f"""
            Analyze this real estate search query and extract precise criteria: "{query}"
            
            Return ONLY valid JSON with these optional fields:
            {{
                "bedrooms": number (exact number from 2BHK, 3BR, etc.),
                "bathrooms": number,
                "min_price": number (in dollars),
                "max_price": number (in dollars from budget/under statements),
                "property_type": ["Apartment", "Condo", "Townhouse"] (array),
                "city": "exact city name",
                "state": "2-letter state code",
                "pet_friendly": boolean (if pet-friendly mentioned),
                "max_amenity_distance": number (in miles if distance mentioned),
                "required_amenities": ["gym", "hospital", "vet", "school", "university", "shopping"]
            }}
            
            City name rules:
            - "New York" or "New York City" → "city": "New York City", "state": "NY"
            - "NYC" → "city": "New York City", "state": "NY"
            - "San Francisco" → "city": "San Francisco", "state": "CA"
            - "LA" or "Los Angeles" → "city": "Los Angeles", "state": "CA"
            - "Chicago" → "city": "Chicago", "state": "IL"
            - "Houston" → "city": "Houston", "state": "TX"
            - Handle "near [city]" or "in [city]" or "around [city]" patterns
            
            Property type rules:
            - Default to ["Apartment"] if no type specified
            - "house" → ["House"]
            - "flat" or "apartment" → ["Apartment"]
            - "condo" → ["Condo"]
            - "any" or "all" → ["Apartment", "Condo", "House", "Townhouse"]
            
            Price rules:
            - Convert "500k" to 500000
            - "under/below/less than X" → "max_price": X
            - "above/more than/over X" → "min_price": X
            - "between X and Y" → set both min_price and max_price
            - Handle ranges like "$400k-600k" or "$400,000 to $600,000"
            
            Special cases:
            - For "show properties" or "show me properties" type queries with just a location,
              return only city/state and property_type=["Apartment", "Condo", "House", "Townhouse"]
            - Include default max_amenity_distance=5 if amenities are mentioned without distance
            - For queries mentioning "available", focus on location and basic criteria only
            """
            
            default_structure = {
                "property_type": ["Apartment", "Condo", "House", "Townhouse"]
            }
            
            response = self.generate_structured_response_sync(criteria_prompt, default_structure)
            
            # Clean up and validate the response
            if isinstance(response, dict):
                # Ensure city names are properly formatted
                if 'city' in response:
                    # Handle special city names
                    city_map = {
                        'nyc': 'New York City',
                        'new york': 'New York City',
                        'sf': 'San Francisco',
                        'la': 'Los Angeles',
                    }
                    city_name = response['city'].lower().strip()
                    response['city'] = city_map.get(city_name, response['city'].title())
                
                # Ensure state codes are uppercase
                if 'state' in response:
                    response['state'] = response['state'].upper()
                
                # Set default property types for general searches
                if 'property_type' not in response or not response['property_type']:
                    response['property_type'] = ["Apartment", "Condo", "House", "Townhouse"]
                
                logger.info(f"Extracted search criteria: {response}")
                return response
            
            return default_structure
            
            default_structure = {
                "property_type": ["Apartment"],  # Default assumption
                "pet_friendly": False,
                "required_amenities": []
            }
            
            response = self.generate_structured_response_sync(criteria_prompt, default_structure)
            
            # Validate and clean the extracted criteria
            search_filters = {}
            
            # Numeric validations
            for field in ['bedrooms', 'bathrooms', 'min_price', 'max_price', 'max_amenity_distance']:
                if field in response and response[field] is not None:
                    try:
                        search_filters[field] = float(response[field])
                        if field in ['bedrooms', 'bathrooms']:
                            search_filters[field] = int(search_filters[field])
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid {field} value: {response[field]}")
            
            # String validations
            if response.get('city'):
                search_filters['city'] = str(response['city']).strip()
            
            if response.get('state'):
                state = str(response['state']).strip().upper()
                # Convert state names to codes if needed
                state_mapping = {
                    'CALIFORNIA': 'CA', 'NEW YORK': 'NY', 'TEXAS': 'TX',
                    'FLORIDA': 'FL', 'ILLINOIS': 'IL'
                }
                search_filters['state'] = state_mapping.get(state, state)
            
            # Boolean validation
            if 'pet_friendly' in response:
                search_filters['pet_friendly'] = bool(response['pet_friendly'])
            
            # Array validations
            if response.get('property_type') and isinstance(response['property_type'], list):
                search_filters['property_type'] = response['property_type']
            
            if response.get('required_amenities') and isinstance(response['required_amenities'], list):
                # Validate amenity names
                valid_amenities = ['gym', 'hospital', 'vet', 'school', 'university', 'shopping']
                search_filters['required_amenities'] = [
                    a for a in response['required_amenities'] if a in valid_amenities
                ]
            
            return search_filters
            
        except Exception as e:
            logger.error(f"Error extracting search criteria: {e}")
            return {"property_type": ["Apartment"]}

    def _rank_properties(self, properties: List[Dict], criteria: Dict[str, Any]) -> List[Dict]:
        """Rank properties based on how well they match the search criteria"""
        try:
            for prop in properties:
                score = 0
                
                # Price preference scoring
                if 'max_price' in criteria:
                    if prop['price'] <= criteria['max_price']:
                        score += 20
                    else:
                        score -= 10
                
                # Bedroom matching
                if 'bedrooms' in criteria:
                    if prop['bedrooms'] == criteria['bedrooms']:
                        score += 15
                    elif prop['bedrooms'] >= criteria['bedrooms']:
                        score += 10
                
                # Pet-friendly bonus
                if criteria.get('pet_friendly') and prop.get('is_pet_friendly'):
                    score += 10
                
                # Amenity scoring
                required_amenities = criteria.get('required_amenities', [])
                if required_amenities:
                    available_amenities = [a['category'] for a in prop.get('amenities', [])]
                    matched_amenities = set(required_amenities) & set(available_amenities)
                    score += len(matched_amenities) * 5
                
                # Location preference (if city specified)
                if criteria.get('city'):
                    if criteria['city'].lower() in prop['city'].lower():
                        score += 15
                
                prop['_match_score'] = score
            
            # Sort by score (descending) then by price (ascending)
            return sorted(properties, key=lambda p: (-p.get('_match_score', 0), p['price']))
            
        except Exception as e:
            logger.error(f"Error ranking properties: {e}")
            return properties

    def _generate_search_summary(self, properties: List[Dict], criteria: Dict[str, Any], query: str) -> str:
        """Generate personalized search summary"""
        try:
            total = len(properties)
            
            if total == 0:
                return "I couldn't find any properties matching your specific criteria."
            
            # Price analysis
            prices = [p['price'] for p in properties]
            min_price = min(prices)
            max_price = max(prices)
            avg_price = sum(prices) / len(prices)
            
            # Location analysis
            cities = list(set(p['city'] for p in properties))
            
            # Generate contextual summary
            summary_parts = []
            
            # Opening
            summary_parts.append(f"🏠 Great news! I found {total} properties that match your search")
            
            # Price context
            if 'max_price' in criteria:
                budget = criteria['max_price']
                within_budget = len([p for p in properties if p['price'] <= budget])
                if within_budget > 0:
                    summary_parts.append(f"with {within_budget} properties within your ${budget:,.0f} budget")
            
            # Location context
            if len(cities) == 1:
                summary_parts.append(f"in {cities[0]}")
            elif len(cities) <= 3:
                summary_parts.append(f"across {', '.join(cities)}")
            else:
                summary_parts.append(f"across {len(cities)} different cities")
            
            # Property type context
            if 'bedrooms' in criteria:
                bedroom_count = criteria['bedrooms']
                summary_parts.append(f"Perfect for your {bedroom_count}-bedroom requirement")
            
            # Price range
            summary_parts.append(f"Price range: ${min_price:,.0f} - ${max_price:,.0f} (avg: ${avg_price:,.0f})")
            
            # Special features
            features = []
            if criteria.get('pet_friendly'):
                pet_friendly_count = len([p for p in properties if p.get('is_pet_friendly')])
                if pet_friendly_count > 0:
                    features.append(f"{pet_friendly_count} pet-friendly options")
            
            if criteria.get('required_amenities'):
                features.append(f"properties with required amenities nearby")
            
            if features:
                summary_parts.append(f"Special features: {', '.join(features)}")
            
            return ". ".join(summary_parts) + "!"
            
        except Exception as e:
            logger.error(f"Error generating search summary: {e}")
            return f"Found {len(properties)} properties matching your criteria."

    def _generate_no_results_response(self, criteria: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Generate helpful response when no properties are found"""
        suggestions = []
        
        # Suggest relaxing criteria
        if 'max_price' in criteria:
            suggestions.append(f"Consider increasing your budget above ${criteria['max_price']:,.0f}")
        
        if 'bedrooms' in criteria and criteria['bedrooms'] > 2:
            suggestions.append(f"Try looking for {criteria['bedrooms']-1}-bedroom options")
        
        if criteria.get('city'):
            suggestions.append(f"Expand your search to nearby areas around {criteria['city']}")
        
        if criteria.get('required_amenities'):
            suggestions.append("Consider prioritizing the most important amenities")
        
        # Get alternative suggestions from database
        relaxed_criteria = {k: v for k, v in criteria.items() if k not in ['max_price', 'bedrooms']}
        alternative_properties = self.db_manager.search_properties(relaxed_criteria)
        
        message = (
            "🔍 I couldn't find properties matching your exact criteria, but I have some suggestions:\n\n"
            + "\n".join(f"• {suggestion}" for suggestion in suggestions[:3])
        )
        
        if alternative_properties:
            message += f"\n\n💡 I found {len(alternative_properties)} similar properties with relaxed criteria. Would you like to see them?"
        
        return self._standardize_response(
            "success",
            message,
            {
                "properties": [],
                "total_found": 0,
                "suggestions": suggestions,
                "alternative_count": len(alternative_properties),
                "search_criteria": criteria
            }
        )

    def _calculate_price_range(self, properties: List[Dict]) -> Dict[str, float]:
        """Calculate price statistics"""
        if not properties:
            return {"min": 0, "max": 0, "average": 0}
        
        prices = [p['price'] for p in properties]
        return {
            "min": min(prices),
            "max": max(prices),
            "average": sum(prices) / len(prices)
        }

    def _get_location_summary(self, properties: List[Dict]) -> Dict[str, Any]:
        """Get summary of locations in results"""
        cities = {}
        states = {}
        
        for prop in properties:
            city = prop.get('city', 'Unknown')
            state = prop.get('state', 'Unknown')
            
            cities[city] = cities.get(city, 0) + 1
            states[state] = states.get(state, 0) + 1
        
        return {
            "cities": cities,
            "states": states,
            "total_cities": len(cities),
            "total_states": len(states)
        }
