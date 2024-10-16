from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import UserInDB, TokenData, User
from db import get_db
from config import EMAIL_ADDR, EMAIL_PASSWORD, SECRET_KEY, ALGORITHM
from schemas import UserTable

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import time

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Utility functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(db: Session, username: str):
    # db.execute("SELECT * FROM users WHERE username = :username", {"username": username})
    user = db.query(UserTable).filter(UserTable.username == username).first()
    if user:
        UserInDB(
            **{
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "disabled": user.disabled,
                "permissions": user.permissions,
                "hashed_password": user.hashed_password,
            }
        )
        return user
    return None


def authenticate_user(db: Session, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    db: Session = get_db().__next__()
    user = get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def send_email(subject, body, email):
    print("Sending Mail To : ", email)
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = EMAIL_ADDR
    password = EMAIL_PASSWORD

    # List of recipients
    recipient_emails = [email]

    # Send emails in batches
    batch_size = 10

    for i in range(0, len(recipient_emails), batch_size):
        batch = recipient_emails[i : i + batch_size]

        for recipient_email in batch:
            msg = MIMEMultipart()
            msg["From"] = f"Drona Gaming League <{sender_email}>"
            msg["To"] = recipient_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "html"))

            try:
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()
                server.login(sender_email, password)
                server.send_message(msg)
                print(f"Email sent to {recipient_email}")
            except Exception as e:
                print(f"Failed to send email to {recipient_email}: {e}")
            finally:
                server.quit()
