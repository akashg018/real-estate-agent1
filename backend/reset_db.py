from database.db import Base, init_db
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()

def reset_database():
    # Drop all tables and recreate them
    engine = create_engine(os.getenv('DATABASE_URL'))
    Base.metadata.drop_all(engine)
    print("Database tables dropped.")
    
    # Reinitialize database with new mock data
    init_db()
    print("Database reinitialized with new data.")

if __name__ == "__main__":
    reset_database()
