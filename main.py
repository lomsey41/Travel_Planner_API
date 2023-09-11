from fastapi import FastAPI
import uvicorn

from flight_data import get_flight_data 
from hotel_data import get_hotel_data
from events_data import get_events_data
from get_location import get_locationId
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

best_itinerary = {}
app = FastAPI()

# @app.get('/get_itinerary/', status_code=200)
# def preferences(source: str, destination: str, start_date: str, end_date: str, budget: float):

#     # Gather information from different APIs 
#     options = gather_information(source, destination, start_date, end_date)

#     # Use an algorithm to determine the itinerary option
#     best_itinerary = determine_itinerary(budget, True, *options)
#     additional_itinerary = determine_itinerary(budget + (budget * 0.05), False, *options)

#     # Create itinerary
#     global_itinerary = {
#         'best_itinerary': best_itinerary,
#         'additional_itinerary': additional_itinerary
#     }

#     return global_itinerary

# Gather information from different APIs 
def gather_information(source, destination, start_date, end_date):

    code = get_locationId(destination)

    # flight_data = get_flight_data(source, destination, start_date)
    hotel_data = get_hotel_data(code, start_date, end_date)
    activity_data = get_events_data(code)

    return hotel_data, activity_data

# Use an algorithm to determine the best itinerary option
def determine_itinerary(budget, flag, hotel_data, activity_data):
    best_itinerary = []
    for i in range(1, 25):
        if i > len(hotel_data) or i > len(activity_data):
            break
        cost = hotel_data[i]['price'] + activity_data[i]['price']
        if cost > budget:
            break
        else:
            if flag and len(best_itinerary) > 0:
                break
            if flag != True and len(best_itinerary) > 1:
                break
            best_itinerary.append({
                'hotel': hotel_data[i],
                'activity': activity_data[i],
            })
    return best_itinerary

if __name__ == "__main__":
    uvicorn.run("server.api:app", host="0.0.0.0", port=8000, reload=True)

# Define SQLAlchemy models
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

# Create PostgreSQL database connection
DATABASE_URL = "postgresql://username:password@localhost/dbname"  # Replace with your PostgreSQL connection string
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create FastAPI app
app = FastAPI()

# Security settings
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Pydantic models
class UserCreate(BaseModel):
    username: str
    password: str

class UserInDB(UserCreate):
    id: int

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str

# CRUD operations
def create_user(db: Session, user: UserCreate):
    hashed_password = password_context.hash(user.password)
    db_user = User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

# Authentication
def authenticate_user(db_user: User, password: str):
    return password_context.verify(password, db_user.hashed_password)

# Create a new user
@app.post("/users/", response_model=UserResponse)
def create_new_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return create_user(db, user)

# Login and generate access token
@app.post("/login/", response_model=UserResponse)
def login_user(user: UserLogin, db: Session = Depends(get_db)):
    db_user = get_user_by_username(db, username=user.username)
    if not db_user or not authenticate_user(db_user, user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    # Generate an access token here if needed
    return db_user

# Protect a route with authentication
@app.get("/protected/")
def protected_route(current_user: User = Depends(get_current_user)):
    return {"message": "This is a protected route"}

# Dependency to get the current user from the access token
def get_current_user(token: str = Depends(get_token)):
    # Implement token verification logic here if needed
    return User(username="example_user")  # Replace with your token verification logic

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

