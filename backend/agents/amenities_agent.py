from .base_agent import BaseAgent
import logging
from datetime import datetime
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class AmenitiesAgent(BaseAgent):
    """
    Intelligent amenities agent that provides detailed property amenities
    and nearby facilities information
    """
    
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager

    def get_amenities(self, property_id: int) -> Dict[str, Any]:
        """Get comprehensive amenities information for a specific property"""
        try:
            logger.info(f"Getting amenities for property {property_id}")
            
            # Get property data from database
            property_data = self.db_manager.get_property(property_id)
            if not property_data:
                return self._standardize_response(
                    "error",
                    f"Property {property_id} not found in our database",
                    {}
                )
            
            # Get actual amenities from database
            db_amenities = self.db_manager.get_property_amenities(property_id)
            nearby_amenities = property_data.get('nearby_amenities', {})
            
            # Generate AI-enhanced amenities description
            enhanced_amenities = self._generate_enhanced_amenities(property_data, db_amenities, nearby_amenities)
            
            return self._standardize_response(
                "success",
                self._generate_amenities_summary(property_data, enhanced_amenities),
                {
                    "property_id": property_id,
                    "property_info": {
                        "address": property_data['address'],
                        "type": property_data['property_type'],
                        "price": property_data['price']
                    },
                    "amenities": enhanced_amenities,
                    "amenity_count": len(enhanced_amenities.get('all_amenities', [])),
                    "nearby_facilities": self._format_nearby_amenities(nearby_amenities)
                }
            )
            
        except Exception as e:
            logger.error(f"Error retrieving amenities for property {property_id}: {e}")
            return self._standardize_response(
                "error",
                f"Failed to retrieve amenities information: {str(e)}",
                {}
            )

    def _generate_enhanced_amenities(self, property_data: Dict[str, Any], 
                                   db_amenities: List[Dict], 
                                   nearby_amenities: Dict[str, Any]) -> Dict[str, Any]:
        """Generate enhanced amenities using AI based on property characteristics"""
        try:
            property_type = property_data.get('property_type', 'Unknown')
            price = property_data.get('price', 0)
            bedrooms = property_data.get('bedrooms', 0)
            square_feet = property_data.get('square_feet', 0)
            year_built = property_data.get('year_built', 2000)
            city = property_data.get('city', '')
            
            # Determine luxury level based on price
            luxury_level = self._determine_luxury_level(price, city)
            
            amenities_prompt = f"""
            Generate detailed amenities for this property:
            
            Property Details:
            - Type: {property_type}
            - Price: ${price:,.2f}
            - Bedrooms: {bedrooms}
            - Size: {square_feet:,.0f} sq ft
            - Year Built: {year_built}
            - Location: {city}
            - Luxury Level: {luxury_level}
            
            Existing Amenities: {[a['name'] for a in db_amenities]}
            Nearby Facilities: {list(nearby_amenities.keys())}
            
            Return JSON with:
            {{
                "building_amenities": ["list of building amenities"],
                "unit_features": ["list of in-unit features"],
                "luxury_features": ["list of premium features if applicable"],
                "outdoor_spaces": ["list of outdoor amenities"],
                "technology": ["list of tech features"],
                "safety_security": ["list of security features"],
                "convenience": ["list of convenience features"]
            }}
            
            Base amenities on the price point and property type. Higher priced properties should have more luxury amenities.
            """
            
            default_structure = {
                "building_amenities": self._get_default_building_amenities(luxury_level),
                "unit_features": self._get_default_unit_features(bedrooms, luxury_level),
                "luxury_features": self._get_default_luxury_features(luxury_level),
                "outdoor_spaces": self._get_default_outdoor_amenities(property_type),
                "technology": self._get_default_tech_features(luxury_level, year_built),
                "safety_security": self._get_default_security_features(luxury_level),
                "convenience": self._get_default_convenience_features(luxury_level)
            }
            
            ai_amenities = self.generate_structured_response_sync(amenities_prompt, default_structure)
            
            # Combine with actual database amenities
            all_amenities = []
            for category, amenities_list in ai_amenities.items():
                if isinstance(amenities_list, list):
                    for amenity in amenities_list:
                        all_amenities.append({
                            "name": amenity,
                            "category": category.replace('_', ' ').title(),
                            "source": "ai_generated"
                        })
            
            # Add database amenities
            for db_amenity in db_amenities:
                all_amenities.append({
                    "name": db_amenity['name'],
                    "category": db_amenity['category'].title(),
                    "distance": db_amenity.get('distance', 0),
                    "source": "database"
                })
            
            # Organize final structure
            result = ai_amenities.copy()
            result['all_amenities'] = all_amenities
            result['amenity_score'] = self._calculate_amenity_score(all_amenities, luxury_level)
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating enhanced amenities: {e}")
            return self._get_fallback_amenities(property_data)

    def _determine_luxury_level(self, price: float, city: str) -> str:
        """Determine luxury level based on price and location"""
        # Price thresholds vary by city
        city_multipliers = {
            'San Francisco': 1.5,
            'New York City': 1.4,
            'Los Angeles': 1.2,
            'Seattle': 1.1,
            'Miami': 1.0,
            'Chicago': 0.9,
            'Austin': 0.8,
            'Houston': 0.7
        }
        
        multiplier = city_multipliers.get(city, 0.8)
        adjusted_price = price / multiplier
        
        if adjusted_price >= 1500000:
            return "ultra_luxury"
        elif adjusted_price >= 1000000:
            return "luxury"
        elif adjusted_price >= 600000:
            return "premium"
        elif adjusted_price >= 400000:
            return "standard_plus"
        else:
            return "standard"

    def _get_default_building_amenities(self, luxury_level: str) -> List[str]:
        """Get default building amenities based on luxury level"""
        base_amenities = ["Elevator", "Lobby", "Mail Room", "Trash Collection"]
        
        if luxury_level in ["standard_plus", "premium", "luxury", "ultra_luxury"]:
            base_amenities.extend(["Fitness Center", "Resident Lounge", "Package Room"])
        
        if luxury_level in ["premium", "luxury", "ultra_luxury"]:
            base_amenities.extend(["Swimming Pool", "Rooftop Deck", "Business Center", "Guest Parking"])
        
        if luxury_level in ["luxury", "ultra_luxury"]:
            base_amenities.extend(["Concierge Service", "Valet Parking", "Wine Storage", "Private Theater"])
        
        if luxury_level == "ultra_luxury":
            base_amenities.extend(["Spa", "Private Chef Kitchen", "Golf Simulator", "Car Charging Stations"])
        
        return base_amenities

    def _get_default_unit_features(self, bedrooms: int, luxury_level: str) -> List[str]:
        """Get default unit features"""
        features = ["Kitchen", "Bathroom", "Living Room", "Windows", "Closets"]
        
        if bedrooms >= 2:
            features.extend(["Master Bedroom", "Guest Bedroom"])
        
        if luxury_level in ["premium", "luxury", "ultra_luxury"]:
            features.extend(["Hardwood Floors", "Granite Countertops", "Stainless Steel Appliances", "In-Unit Laundry"])
        
        if luxury_level in ["luxury", "ultra_luxury"]:
            features.extend(["Walk-in Closets", "Marble Bathrooms", "High Ceilings", "Floor-to-Ceiling Windows"])
        
        return features

    def _get_default_luxury_features(self, luxury_level: str) -> List[str]:
        """Get luxury features based on level"""
        if luxury_level == "ultra_luxury":
            return ["Private Balcony", "Smart Home Technology", "Premium Finishes", "Butler Service", "Private Elevator"]
        elif luxury_level == "luxury":
            return ["Private Balcony", "Smart Home Technology", "Premium Finishes", "Doorman Service"]
        elif luxury_level == "premium":
            return ["Balcony/Patio", "Smart Thermostat", "Premium Appliances"]
        else:
            return []

    def _get_default_outdoor_amenities(self, property_type: str) -> List[str]:
        """Get outdoor amenities based on property type"""
        base_outdoor = ["Courtyard", "Landscaping"]
        
        if "Townhouse" in property_type:
            base_outdoor.extend(["Private Yard", "Patio", "Garden Space"])
        else:
            base_outdoor.extend(["Shared Garden", "BBQ Area", "Outdoor Seating"])
        
        return base_outdoor

    def _get_default_tech_features(self, luxury_level: str, year_built: int) -> List[str]:
        """Get technology features"""
        tech_features = ["High-Speed Internet Ready", "Cable Ready"]
        
        if year_built >= 2015:
            tech_features.extend(["Smart Home Pre-wiring", "USB Outlets"])
        
        if luxury_level in ["premium", "luxury", "ultra_luxury"]:
            tech_features.extend(["Smart Thermostat", "Keyless Entry", "Smart Lighting"])
        
        if luxury_level in ["luxury", "ultra_luxury"]:
            tech_features.extend(["Home Automation System", "Security Cameras", "Smart Appliances"])
        
        return tech_features

    def _get_default_security_features(self, luxury_level: str) -> List[str]:
        """Get security features"""
        security = ["Secure Entry", "Locks on All Doors"]
        
        if luxury_level in ["standard_plus", "premium", "luxury", "ultra_luxury"]:
            security.extend(["Security System", "Emergency Lighting"])
        
        if luxury_level in ["premium", "luxury", "ultra_luxury"]:
            security.extend(["24/7 Security", "Video Surveillance", "Controlled Access"])
        
        if luxury_level in ["luxury", "ultra_luxury"]:
            security.extend(["Personal Security", "Biometric Access", "Panic Rooms"])
        
        return security

    def _get_default_convenience_features(self, luxury_level: str) -> List[str]:
        """Get convenience features"""
        convenience = ["On-site Maintenance", "Online Rent Payment"]
        
        if luxury_level in ["standard_plus", "premium", "luxury", "ultra_luxury"]:
            convenience.extend(["Package Acceptance", "Dry Cleaning Service"])
        
        if luxury_level in ["premium", "luxury", "ultra_luxury"]:
            convenience.extend(["Grocery Delivery", "Pet Services", "Housekeeping Available"])
        
        if luxury_level in ["luxury", "ultra_luxury"]:
            convenience.extend(["Personal Assistant", "Event Planning", "Travel Services"])
        
        return convenience

    def _format_nearby_amenities(self, nearby_amenities: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format nearby amenities for display"""
        formatted = []
        
        for category, info in nearby_amenities.items():
            if isinstance(info, dict):
                formatted.append({
                    "category": category.title(),
                    "name": info.get('name', 'Unknown'),
                    "distance": info.get('distance', 0),
                    "distance_text": f"{info.get('distance', 0)} miles away"
                })
        
        # Sort by distance
        return sorted(formatted, key=lambda x: x['distance'])

    def _calculate_amenity_score(self, amenities: List[Dict], luxury_level: str) -> Dict[str, Any]:
        """Calculate amenity score and rating"""
        total_amenities = len(amenities)
        
        # Base scoring
        base_score = min(total_amenities * 2, 50)  # Max 50 points for quantity
        
        # Luxury bonus
        luxury_bonus = {
            "standard": 0,
            "standard_plus": 5,
            "premium": 10,
            "luxury": 20,
            "ultra_luxury": 30
        }.get(luxury_level, 0)
        
        # Category diversity bonus
        categories = set(a.get('category', '') for a in amenities)
        diversity_bonus = len(categories) * 2
        
        total_score = base_score + luxury_bonus + diversity_bonus
        rating = min(total_score / 20, 5.0)  # Convert to 5-star rating
        
        return {
            "total_score": total_score,
            "rating": round(rating, 1),
            "total_amenities": total_amenities,
            "unique_categories": len(categories),
            "luxury_level": luxury_level
        }

    def _generate_amenities_summary(self, property_data: Dict[str, Any], amenities: Dict[str, Any]) -> str:
        """Generate personalized amenities summary"""
        try:
            address = property_data['address']
            property_type = property_data['property_type']
            score_info = amenities.get('amenity_score', {})
            rating = score_info.get('rating', 0)
            total_amenities = score_info.get('total_amenities', 0)
            
            summary = f"🏢 {property_type} at {address}\n\n"
            summary += f"⭐ Amenity Rating: {rating}/5.0 ({total_amenities} total amenities)\n\n"
            
            # Highlight top categories
            top_categories = []
            if amenities.get('luxury_features'):
                top_categories.append("✨ Luxury Features")
            if amenities.get('building_amenities'):
                top_categories.append("🏢 Building Amenities")
            if amenities.get('technology'):
                top_categories.append("💻 Smart Technology")
            
            if top_categories:
                summary += f"Highlights: {', '.join(top_categories)}\n\n"
            
            summary += "This property offers excellent amenities and nearby facilities to enhance your lifestyle!"
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating amenities summary: {e}")
            return "Property amenities information available."

    def _get_fallback_amenities(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback amenities when AI generation fails"""
        return {
            "building_amenities": ["Lobby", "Elevator", "Mail Room"],
            "unit_features": ["Kitchen", "Bathroom", "Living Room"],
            "luxury_features": [],
            "outdoor_spaces": ["Courtyard"],
            "technology": ["Internet Ready"],
            "safety_security": ["Secure Entry"],
            "convenience": ["On-site Maintenance"],
            "all_amenities": [
                {"name": "Basic Amenities", "category": "Standard", "source": "fallback"}
            ],
            "amenity_score": {"total_score": 20, "rating": 2.0, "total_amenities": 1}
        }
