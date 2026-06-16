from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/market_data.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Property(Base):
    __tablename__ = "properties"

    id = Column(String, primary_key=True, index=True)
    title = Column(String)
    price = Column(Float)
    currency = Column(String)
    area_m2 = Column(Float)
    price_per_m2 = Column(Float)
    property_type = Column(String)
    contract_type = Column(String)
    city = Column(String)
    zone = Column(String)
    address = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    
    # --- NUEVOS CAMPOS ADICIONALES ---
    construction_state = Column(String, nullable=True) # En construcción, Usado, etc.
    bathrooms = Column(Integer, nullable=True)
    bedrooms = Column(Integer, nullable=True)
    stratum = Column(Integer, nullable=True) # Estrato (1 al 6)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def upsert_property(db, prop_dict):
    # Calcular precio por metro cuadrado antes de guardar si existen los datos
    if prop_dict.get("price") and prop_dict.get("area_m2") and prop_dict["area_m2"] > 0:
        prop_dict["price_per_m2"] = prop_dict["price"] / prop_dict["area_m2"]
    else:
        prop_dict["price_per_m2"] = None

    db_obj = db.query(Property).filter(Property.id == prop_dict["id"]).first()
    if db_obj:
        for key, value in prop_dict.items():
            setattr(db_obj, key, value)
    else:
        db_obj = Property(**prop_dict)
        db.add(db_obj)
    db.commit()
    return db_obj
    