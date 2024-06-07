from sqlalchemy import Boolean, Column, Integer, String, text
from db import Base

from sqlalchemy import ARRAY


class UserTable(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    disabled = Column(Boolean, server_default=text("false"))
    hashed_password = Column(String)
    permissions = Column(String, server_default="*")
