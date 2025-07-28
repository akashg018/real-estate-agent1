from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Table, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os
from dotenv import load_dotenv
import pandas as pd
import random
from faker import Faker
import json

load_dotenv()

Base = declarative_base()

# Association table for property amenities
property_amenities = Table('property_amenities', Base.metadata,
    Column('property_id', Integer, ForeignKey('properties.id')),
    Column('amenity_id', Integer, ForeignKey('amenities.id'))
)

class Amenity(Base):
    __tablename__ = 'amenities'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)  # e.g., 'gym', 'hospital', 'school', etc.
    distance = Column(Float)  # Distance in miles
    properties = relationship('Property', secondary=property_amenities, back_populates='amenities')

class Property(Base):
    __tablename__ = 'properties'

    id = Column(Integer, primary_key=True)
    address = Column(String)
    city = Column(String)
    state = Column(String)
    zip_code = Column(String)
    price = Column(Float)
    bedrooms = Column(Integer)
    bathrooms = Column(Float)
    square_feet = Column(Float)
    lot_size = Column(Float)
    year_built = Column(Integer)
    property_type = Column(String)
    is_available = Column(Boolean, default=True)
    is_pet_friendly = Column(Boolean, default=False)
    nearby_amenities = Column(JSON)  # Store distances to various amenities
    amenities = relationship('Amenity', secondary=property_amenities, back_populates='properties')

def init_db():
    engine = create_engine(os.getenv('DATABASE_URL'))
    Base.metadata.create_all(engine)
    
    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Check if database is empty
    if session.query(Property).count() == 0:
        generate_mock_data(session)
    
    session.close()

def generate_mock_data(session):
    fake = Faker()
    
    states = {
        'CA': {
            'San Francisco': ['Mission District', 'Pacific Heights', 'Marina District', 'Nob Hill', 'SoMa'],
            'Los Angeles': ['Downtown', 'Hollywood', 'Santa Monica', 'Venice'],
            'San Diego': ['Downtown', 'La Jolla', 'Pacific Beach'],
            'San Jose': ['Downtown', 'Willow Glen', 'North San Jose']
        },
        'NY': {'New York City': ['Manhattan', 'Brooklyn', 'Queens']},
        'TX': {'Austin': ['Downtown', 'South Congress'], 'Houston': ['Downtown', 'Midtown']},
        'FL': {'Miami': ['Downtown', 'South Beach'], 'Orlando': ['Downtown', 'Winter Park']},
        'IL': {'Chicago': ['Loop', 'River North', 'Lincoln Park']}
    }
    
    property_types = {
        'Apartment': ['Studio', '1BHK', '2BHK', '3BHK', 'Penthouse'],
        'Condo': ['Standard', 'Luxury', 'Waterfront'],
        'Townhouse': ['Standard', 'End Unit', 'Corner Unit']
    }
    amenity_categories = {
        'gym': ['24 Hour Fitness', 'LA Fitness', 'Planet Fitness'],
        'hospital': ['General Hospital', 'Medical Center', 'Community Hospital'],
        'vet': ['PetCare Clinic', 'VCA Animal Hospital', 'Pet Emergency Center'],
        'school': ['Elementary School', 'Middle School', 'High School'],
        'university': ['State University', 'Community College', 'Technical Institute'],
        'shopping': ['Shopping Mall', 'Grocery Store', 'Shopping Center']
    }
    
    # Create amenities first
    amenities = []
    for category, names in amenity_categories.items():
        for name in names:
            amenity = Amenity(
                name=name,
                category=category,
                distance=round(random.uniform(0.1, 5.0), 1)
            )
            session.add(amenity)
            amenities.append(amenity)
    
    session.commit()
    
    # Create properties
    properties = []
    for _ in range(1000):
        state = random.choice(list(states.keys()))
        city = random.choice(list(states[state].keys()))
        neighborhood = random.choice(states[state][city])
        
        # Select property type and subtype
        main_type = random.choice(list(property_types.keys()))
        sub_type = random.choice(property_types[main_type])
        
        # Determine price range based on location and type
        base_price = {
            'CA': {'San Francisco': (800000, 2000000), 'Los Angeles': (600000, 1500000)}.get(city, (400000, 1000000)),
            'NY': (700000, 1800000),
            'TX': (300000, 800000),
            'FL': (350000, 900000),
            'IL': (400000, 1000000)
        }.get(state, (300000, 800000))
        
        # Adjust price based on property type
        type_multiplier = 1.0
        if '2BHK' in sub_type:
            type_multiplier = 1.2
        elif '3BHK' in sub_type:
            type_multiplier = 1.5
        elif 'Luxury' in sub_type or 'Penthouse' in sub_type:
            type_multiplier = 2.0
        
        price = round(random.uniform(base_price[0], base_price[1]) * type_multiplier, 2)
        
        # Generate nearby amenities with more realistic distances
        nearby = {}
        for category, names in amenity_categories.items():
            # More likely to have amenities within 5 miles in urban areas
            max_distance = 3.0 if city in ['San Francisco', 'New York City', 'Chicago'] else 5.0
            nearby[category] = {
                "name": random.choice(names),
                "distance": round(random.uniform(0.1, max_distance), 1)
            }
        
        # Determine number of bedrooms based on sub_type
        bedrooms = {
            'Studio': 0,
            '1BHK': 1,
            '2BHK': 2,
            '3BHK': 3,
            'Penthouse': random.choice([2, 3, 4])
        }.get(sub_type, random.randint(1, 4))
        
        property = Property(
            address=f"{fake.building_number()} {fake.street_name()}, {neighborhood}",
            city=city,
            state=state,
            zip_code=fake.zipcode(),
            price=price,
            bedrooms=bedrooms,
            bathrooms=bedrooms + 0.5 if bedrooms > 0 else 1,
            square_feet=round(random.uniform(600 + (bedrooms * 300), 800 + (bedrooms * 400)), 2),
            lot_size=round(random.uniform(0.1, 0.5), 2),
            year_built=random.randint(1980, 2023),
            property_type=f"{main_type} - {sub_type}",
            is_available=True,
            is_pet_friendly=random.choice([True, False] * 2 + [True] * 3),  # 60% chance of being pet-friendly
            nearby_amenities=nearby
        )
        
        # Add random amenities to each property
        property_amenities = random.sample(amenities, random.randint(3, len(amenities)))
        property.amenities.extend(property_amenities)
        
        session.add(property)
    
    session.commit()
