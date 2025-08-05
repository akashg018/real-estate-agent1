from sqlalchemy import create_engine, or_, Float
from sqlalchemy.orm import sessionmaker
from database.db import Property
import os
from dotenv import load_dotenv
import json

load_dotenv()

class DatabaseManager:
    def __init__(self):
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            database_url = 'sqlite:///database/real_estate.db'
            print("Warning: DATABASE_URL not found in environment, using default SQLite database")
        self.engine = create_engine(database_url)
        self.Session = sessionmaker(bind=self.engine)

    def search_properties(self, filters):
        session = self.Session()
        try:
            query = session.query(Property)
            print(f"Initial filters: {filters}")  # Debug log
            
            # Start with available properties
            query = query.filter(Property.is_available == True)
            
            # Location search first (most important)
            if 'city' in filters and filters['city']:
                city_name = filters['city'].strip()
                # Try exact match first
                exact_match = query.filter(Property.city.ilike(city_name))
                if exact_match.count() > 0:
                    query = exact_match
                else:
                    # Try partial match
                    words = city_name.lower().split()
                    conditions = []
                    for word in words:
                        if len(word) > 2:  # Skip short words like "in", "at", etc.
                            conditions.append(Property.city.ilike(f"%{word}%"))
                    if conditions:
                        query = query.filter(or_(*conditions))
            
            if 'state' in filters and filters['state']:
                state_code = filters['state'].strip().upper()
                query = query.filter(Property.state == state_code)
            
            # Property type filter
            if 'property_type' in filters:
                if isinstance(filters['property_type'], list):
                    types = [t.strip() for t in filters['property_type'] if t.strip()]
                    if types:
                        # Create OR conditions for each type and its variations
                        type_conditions = []
                        for t in types:
                            type_conditions.extend([
                                Property.property_type.ilike(f"%{t}%"),
                                Property.property_type.ilike(f"%{t.lower()}%"),
                                Property.property_type.ilike(f"%{t.upper()}%")
                            ])
                        query = query.filter(or_(*type_conditions))
                elif filters['property_type']:
                    query = query.filter(Property.property_type.ilike(f"%{filters['property_type']}%"))
            
            # Price filters
            if 'min_price' in filters:
                query = query.filter(Property.price >= filters['min_price'])
            if 'max_price' in filters:
                query = query.filter(Property.price <= filters['max_price'])
            
            # Room filters
            if 'bedrooms' in filters:
                query = query.filter(Property.bedrooms >= filters['bedrooms'])
            if 'bathrooms' in filters:
                query = query.filter(Property.bathrooms >= filters['bathrooms'])
            
            # Pet-friendly filter
            if 'pet_friendly' in filters and filters['pet_friendly']:
                query = query.filter(Property.is_pet_friendly == True)
            
            # Location filters
            if 'city' in filters and filters['city']:
                city_name = filters['city'].strip()
                query = query.filter(Property.city.ilike(f"%{city_name}%"))
                print(f"Filtering for city: {city_name}")  # Debug log
            if 'state' in filters and filters['state']:
                state_code = filters['state'].strip().upper()
                query = query.filter(Property.state == state_code)
                print(f"Filtering for state: {state_code}")  # Debug log
            
            # Pet-friendly filter
            if 'pet_friendly' in filters and filters['pet_friendly']:
                query = query.filter(Property.is_pet_friendly == True)
            
            # Get properties matching the filters so far
            properties = query.all()
            print(f"Found {len(properties)} properties after basic filters")
            
            # Amenities filter (if needed)
            if properties and 'max_amenity_distance' in filters:
                try:
                    max_distance = float(filters['max_amenity_distance'])
                    required_amenities = filters.get('required_amenities', [])
                    
                    if required_amenities:
                        filtered_properties = []
                        for prop in properties:
                            if not prop.nearby_amenities:
                                continue
                                
                            amenities_in_range = True
                            for amenity in required_amenities:
                                if (amenity not in prop.nearby_amenities or 
                                    float(prop.nearby_amenities[amenity]['distance']) > max_distance):
                                    amenities_in_range = False
                                    break
                                    
                            if amenities_in_range:
                                filtered_properties.append(prop)
                        
                        properties = filtered_properties
                        print(f"Found {len(properties)} properties after amenity filtering")
                        
                except (ValueError, TypeError) as e:
                    print(f"Amenity filter error: {str(e)}")
            
            # If no properties found with strict criteria, try more lenient search
            if not properties and filters.get('city'):
                print("No properties found with strict criteria, trying lenient search...")
                query = session.query(Property).filter(Property.is_available == True)
                
                # Try matching any word in the city name
                city_words = filters['city'].lower().split()
                conditions = []
                for word in city_words:
                    if len(word) > 2:  # Skip short words
                        conditions.append(Property.city.ilike(f"%{word}%"))
                if conditions:
                    query = query.filter(or_(*conditions))
                
                # Only keep basic filters for lenient search
                if 'max_price' in filters:
                    query = query.filter(Property.price <= filters['max_price'])
                if 'property_type' in filters and isinstance(filters['property_type'], list):
                    query = query.filter(Property.property_type.in_(filters['property_type']))
                
                properties = query.all()
                print(f"Lenient search found {len(properties)} properties")
            
            # Sort results
            if properties:
                # Sort by relevance if city was specified
                if filters.get('city'):
                    properties.sort(
                        key=lambda p: (
                            0 if p.city.lower() == filters['city'].lower() else 1,  # Exact city match first
                            p.price  # Then by price
                        )
                    )
                else:
                    # Sort by price if no city specified
                    properties.sort(key=lambda p: p.price)
            
            # Convert to dictionaries and return (limit to 50 results)
            result = self._convert_properties_to_dict(properties[:50])
            print(f"Returning {len(result)} properties")
            return result
        finally:
            session.close()

    def get_property(self, property_id):
        session = self.Session()
        try:
            property = session.query(Property).filter(Property.id == property_id).first()
            return self._property_to_dict(property) if property else None
        finally:
            session.close()
            
    def get_property_amenities(self, property_id):
        """Get amenities for a specific property"""
        session = self.Session()
        try:
            property = session.query(Property).filter(Property.id == property_id).first()
            if not property:
                return []
            
            # Get both direct amenities and nearby amenities
            amenities = []
            
            # Add direct amenities (from the amenities relationship)
            if property.amenities:
                amenities.extend([
                    {
                        'name': amenity.name,
                        'category': amenity.category,
                        'distance': float(amenity.distance) if amenity.distance else 0.0
                    }
                    for amenity in property.amenities
                ])
            
            # Add nearby amenities from the JSON field
            if property.nearby_amenities:
                for category, info in property.nearby_amenities.items():
                    if isinstance(info, dict):
                        amenities.append({
                            'name': info.get('name', f'Nearby {category.title()}'),
                            'category': category,
                            'distance': float(info.get('distance', 0))
                        })
            
            return sorted(amenities, key=lambda x: x.get('distance', 0))
        except Exception as e:
            print(f"Error getting amenities for property {property_id}: {e}")
            return []
        finally:
            session.close()

    def _convert_properties_to_dict(self, properties):
        """Convert a list of property objects to dictionaries"""
        result = []
        for prop in properties:
            prop_dict = self._property_to_dict(prop)
            if prop_dict:
                result.append(prop_dict)
        return result

    def _property_to_dict(self, property):
        if not property:
            return None
            
        try:
            return {
                'id': property.id,
                'address': property.address or '',
                'city': property.city or '',
                'state': property.state or '',
                'zip_code': property.zip_code or '',
                'price': float(property.price) if property.price else 0.0,
                'bedrooms': int(property.bedrooms) if property.bedrooms else 0,
                'bathrooms': float(property.bathrooms) if property.bathrooms else 0.0,
                'square_feet': float(property.square_feet) if property.square_feet else 0.0,
                'lot_size': float(property.lot_size) if property.lot_size else 0.0,
                'year_built': int(property.year_built) if property.year_built else 0,
                'property_type': property.property_type or 'Unknown',
                'is_available': bool(property.is_available),
                'is_pet_friendly': bool(property.is_pet_friendly),
                'nearby_amenities': property.nearby_amenities or {},
                'amenities': [
                    {
                        'name': a.name or '',
                        'category': a.category or 'other',
                        'distance': float(a.distance) if a.distance else 0.0
                    } 
                    for a in (property.amenities or [])
                ]
            }
        except Exception as e:
            print(f"Error converting property {property.id} to dict: {str(e)}")
            return None
            
    def update_property_availability(self, property_id: int, is_available: bool) -> bool:
        """Update property availability status"""
        session = self.Session()
        try:
            property = session.query(Property).filter(Property.id == property_id).first()
            if not property:
                return False
                
            property.is_available = is_available
            session.commit()
            return True
            
        except Exception as e:
            print(f"Error updating property {property_id} availability: {e}")
            session.rollback()
            return False
            
        finally:
            session.close()
