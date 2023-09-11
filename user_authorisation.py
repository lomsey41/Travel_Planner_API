from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta

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
    
    # Create an access token
    access_token = create_access_token(data={"sub": db_user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# Protect a route with authentication
@app.get("/protected/")
def protected_route(current_user: User = Depends(get_current_user)):
    return {"message": "This is a protected route"}

# Dependency to get the current user from the access token
def get_current_user(token: str = Depends(get_token)):
    payload = decode_token(token)
    username = payload.get("sub")
    db_user = get_user_by_username(db, username)
    if db_user is None:
        raise HTTPException(status_code=401, detail="Invalid Token")
    return db_user

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Token handling
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

# Database initialization (create tables if they don't exist)
Base.metadata.create_all(bind=engine)

