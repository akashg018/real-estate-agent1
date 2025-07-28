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
            
            # Basic property filters
            if 'min_price' in filters:
                query = query.filter(Property.price >= filters['min_price'])
            if 'max_price' in filters:
                query = query.filter(Property.price <= filters['max_price'])
            if 'bedrooms' in filters:
                query = query.filter(Property.bedrooms >= filters['bedrooms'])
            if 'bathrooms' in filters:
                query = query.filter(Property.bathrooms >= filters['bathrooms'])
            if 'property_type' in filters:
                if isinstance(filters['property_type'], list):
                    query = query.filter(Property.property_type.in_(filters['property_type']))
                else:
                    query = query.filter(Property.property_type == filters['property_type'])
            
            # Location filters
            if 'city' in filters:
                query = query.filter(Property.city.ilike(f"%{filters['city']}%"))
            if 'state' in filters:
                query = query.filter(Property.state == filters['state'])
            
            # Pet-friendly filter
            if 'pet_friendly' in filters and filters['pet_friendly']:
                query = query.filter(Property.is_pet_friendly == True)
            
            # Amenities filter
            if 'max_amenity_distance' in filters:
                try:
                    max_distance = float(filters['max_amenity_distance'])
                    required_amenities = filters.get('required_amenities', 
                        ['gym', 'hospital', 'vet', 'school', 'university'])
                    
                    # Filter properties where all required amenities are within max_distance
                    for amenity in required_amenities:
                        query = query.filter(
                            Property.nearby_amenities[amenity]['distance'].astext.cast(Float) <= max_distance
                        )
                except (ValueError, TypeError) as e:
                    print(f"Amenity filter error: {str(e)}")

            # Add sorting by relevance based on filters
            if filters.get('city'):
                query = query.order_by(
                    Property.city.ilike(f"%{filters['city']}%").desc(),
                    Property.price.asc()
                )
            else:
                query = query.order_by(Property.price.asc())
                
            properties = query.filter(Property.is_available == True).limit(50).all()
            
            # Convert to dictionaries with error handling
            result = []
            for prop in properties:
                try:
                    prop_dict = self._property_to_dict(prop)
                    # Verify all required amenities are present
                    if 'required_amenities' in filters:
                        has_all_amenities = all(
                            any(a['category'] == req for a in prop_dict['amenities'])
                            for req in filters['required_amenities']
                        )
                        if not has_all_amenities:
                            continue
                    result.append(prop_dict)
                except Exception as e:
                    print(f"Error converting property {prop.id} to dict: {str(e)}")
                    continue
            
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
