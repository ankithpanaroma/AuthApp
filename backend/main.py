
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
from models import User
from database import SessionLocal, engine
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
import requests
import schemas
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

origins = [
    "http://localhost:3000",  # Adjust the port if your frontend runs on a different one
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows all origins from the list
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID")
MICROSOFT_TENANT_ID = os.getenv("MICROSOFT_TENANT_ID", "common")
MICROSOFT_REDIRECT_URI = os.getenv("MICROSOFT_REDIRECT_URI")
MICROSOFT_GRAPH_URL = os.getenv("MICROSOFT_GRAPH_URL")


def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first() #returns first result


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = pwd_context.hash(user.password)
    db_user = User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    return db_user

@app.post("/register")
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="User already registered")
    
    create_user(db=db, user=user)
    return {"message": "User registered successfully"}


def authenticate_user(username: str, password: str, db: Session):
    user = db.query(User).filter(User.username == username).first()
    if not user or not pwd_context.verify(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta  #timezone.utc
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@app.post("/login")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=403, detail="Token is invalid or expired")
        return payload
    except JWTError:
        raise HTTPException(status_code=403, detail="Token is invalid or expired")

@app.get("/verify-token/{token}")
async def verify_user_token(token: str):
    verify_token(token=token)
    return {"message": "Token is valid"}


@app.post("/auth/google")
def google_auth(request: schemas.GoogleAuthRequest, db: Session = Depends(get_db)):
    try:
        token = request.token  
        # print("Received Token:", token)

        id_info = id_token.verify_oauth2_token(token, google_requests.Request(), GOOGLE_CLIENT_ID)
        # print("Decoded Google Token Info:", id_info)

        google_email = id_info.get("email")
        if not google_email:
            raise HTTPException(status_code=400, detail="Invalid Google response: No email found")

        user = db.query(User).filter(User.username == google_email).first()

        if not user:
            new_user = User(username=google_email, hashed_password="")
            db.add(new_user)
            db.commit()
            user = new_user

        access_token = create_access_token(
            data={"sub": user.username},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        return {"access_token": access_token, "token_type": "bearer"}

    except ValueError as e:
        print("Google Token Verification Failed:", str(e))
        raise HTTPException(status_code=401, detail="Invalid Google token")

# Microsoft Authentication
@app.post("/auth/microsoft")
def microsoft_auth(request: schemas.MicrosoftAuthRequest, db: Session = Depends(get_db)):
    try:
        # Exchange authorization code for access token
        token_url = f"https://login.microsoftonline.com/{MICROSOFT_TENANT_ID}/oauth2/v2.0/token"
        token_data = {
            "client_id": MICROSOFT_CLIENT_ID,
            "code": request.code,
            "redirect_uri": MICROSOFT_REDIRECT_URI,
            "grant_type": "authorization_code",
            "scope": "User.Read"
        }
        
        token_response = requests.post(token_url, data=token_data)
        token_response.raise_for_status()
        
        token_info = token_response.json()
        access_token = token_info.get("access_token")
        
        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to obtain Microsoft access token")
        
        # Use the access token to get user information
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
        
        user_response = requests.get(MICROSOFT_GRAPH_URL, headers=headers)
        user_response.raise_for_status()
        
        user_info = user_response.json()
        microsoft_email = user_info.get("mail") or user_info.get("userPrincipalName")
        
        if not microsoft_email:
            raise HTTPException(status_code=400, detail="Invalid Microsoft response: No email found")
        
        # Check if user exists, create if not
        user = db.query(User).filter(User.username == microsoft_email).first()
        
        if not user:
            new_user = User(username=microsoft_email, hashed_password="")
            db.add(new_user)
            db.commit()
            user = new_user
        
        # Create our own JWT token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        jwt_token = create_access_token(
            data={"sub": user.username},
            expires_delta=access_token_expires
        )
        
        return {"access_token": jwt_token, "token_type": "bearer"}
        
    except requests.RequestException as e:
        print(f"Microsoft Auth Error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Microsoft authentication failed: {str(e)}")

# Alternative Microsoft authentication with ID token
class MicrosoftTokenAuthRequest(BaseModel):
    token: str  # ID token from Microsoft
from fastapi import HTTPException
from datetime import timedelta
from jose import jwt  # assuming you're using python-jose

@app.post("/auth/microsoft/token")
def microsoft_token_auth(request: MicrosoftTokenAuthRequest, db: Session = Depends(get_db)):
    try:
        token = request.token
        
        # Decode token without verification (for demo purposes)
        payload = jwt.decode(token, options={"verify_signature": False})
        
        microsoft_email = payload.get("email") or payload.get("preferred_username")
        if not microsoft_email:
            raise HTTPException(status_code=400, detail="Invalid Microsoft token: No email found")
        
        # Check if user exists, create if not
        user = db.query(User).filter(User.username == microsoft_email).first()
        
        if not user:
            new_user = User(username=microsoft_email, hashed_password="")
            db.add(new_user)
            db.commit()
            user = new_user
        
        # Create JWT token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        jwt_token = create_access_token(
            data={"sub": user.username},
            expires_delta=access_token_expires
        )
        
        return {"access_token": jwt_token, "token_type": "bearer"}
    
    except jwt.JWTError as e:
        raise HTTPException(status_code=401, detail="Token decode error")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

        