from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
from dotenv import load_dotenv

# load 
load_dotenv()
# url
DATABASE_URL =os.getenv('DATABASE_URL')

# create engine means connection 
engine = create_engine(url=DATABASE_URL,echo=True)
# session maker
SessionLocal = sessionmaker(autocommit=False,autoflush=False,bind=engine)
Base = declarative_base()


# get db

def get_db():
   db = SessionLocal()
   print(type(db))
   try:
      yield db
   finally:
      db.close()