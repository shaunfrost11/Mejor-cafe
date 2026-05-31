from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext

# In a real production app, this key is hidden in a .env file!
SECRET_KEY = "my-super-secret-ecommerce-key_1234567889"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120 # Tokens expire after 2 hours for security

# Tell passlib we want to use the bcrypt algorithm
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """Takes a plain text password and turns it into an unreadable hash."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Checks if the typed password matches the hash in the database."""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    """Generates the JWT 'VIP Badge' for the user to hold onto."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    # Cryptographically sign the badge
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt