from multiprocessing import get_context
import subprocess
from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, UnidentifiedImageError
import os
from io import BytesIO
import tempfile
import ffmpeg
from datetime import timedelta
from schemas import Base, UserTable
from db import engine, get_db
from config import ACCESS_TOKEN_EXPIRE_MINUTES
from sqlalchemy.orm import Session
from models import Token, User
from utils import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_password_hash,
)

import cairosvg

app = FastAPI(title="Indian Police", version="0.1", description="API for Indian Police")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# # Base.metadata.create_all(bind=engine)
# # Endpoints
@app.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
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


@app.post("/convert/image/")
async def convert_image(
    file: UploadFile = File(...),
    format: str = "jpeg",
):
    # Normalize the format string
    format = format.lower()

    # Ensure format is one of the acceptable types
    if format not in [
        "jpg",
        "jpeg",
        "png",
        "bmp",
        "gif",
        "tiff",
        "svg",
        "ps",
        "pdf",
        "eps",
    ]:
        raise HTTPException(status_code=400, detail="Invalid format")

    # Read the uploaded image file
    try:
        file_content = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading file: {e}")

    # Handle SVG conversion separately
    if file.filename.lower().endswith(".svg"):
        # Define the output format and file extension
        output_format = format if format != "svg" else "svg"
        output_extension = format if format != "jpeg" else "jpg"

        # Create a temporary file to save the converted image
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=f".{output_extension}"
        ) as temp_file:
            temp_file_name = temp_file.name
            if format == "png":
                cairosvg.svg2png(bytestring=file_content, write_to=temp_file_name)
                return FileResponse(
                    temp_file_name, filename=f"converted_image.{output_extension}"
                )
            if format == "ps":
                cairosvg.svg2ps(bytestring=file_content, write_to=temp_file_name)
                return FileResponse(
                    temp_file_name, filename=f"converted_image.{output_extension}"
                )
            if format == "pdf":
                cairosvg.svg2pdf(bytestring=file_content, write_to=temp_file_name)
                return FileResponse(
                    temp_file_name, filename=f"converted_image.{output_extension}"
                )
            if format == "eps":
                cairosvg.svg2eps(bytestring=file_content, write_to=temp_file_name)
                return FileResponse(
                    temp_file_name, filename=f"converted_image.{output_extension}"
                )
            return FileResponse(temp_file_path, filename=filename)
    # For non-SVG files

    image = Image.open(BytesIO(file_content))
    if format == "jpeg":
        image = image.convert("RGB")
    if format == "jpg":
        image = image.convert("RGB")
    # Create a BytesIO object to save the converted image
    converted_image = BytesIO()
    image.save(converted_image, format=format.upper() if format != "jpg" else "JPEG")
    converted_image.seek(0)

    filename = f"converted_image.{format}"

    # Create a temporary file to save the converted image
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{format}") as temp_file:
        temp_file.write(converted_image.read())
        temp_file_path = temp_file.name

    return FileResponse(temp_file_path, filename=filename)


@app.post("/convert/video/")
async def convert_video(
    format: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
):
    # Ensure format is one of the acceptable types
    if format.lower() not in ["mp4", "avi", "mkv", "flv", "mov"]:
        raise HTTPException(status_code=400, detail="Invalid format")

    # Read the uploaded video file
    input_file = await file.read()

    # Create a temporary input file
    input_temp = tempfile.NamedTemporaryFile(
        delete=False, suffix=os.path.splitext(file.filename)[-1]
    )
    with open(input_temp.name, "wb") as f:
        f.write(input_file)

    # Create a temporary output file
    output_temp = tempfile.NamedTemporaryFile(delete=False, suffix=f".{format.lower()}")
    output_path = output_temp.name

    # Convert video using ffmpeg
    try:
        ffmpeg.input(input_temp.name).output(output_path).run()
    except ffmpeg.Error as e:
        raise HTTPException(status_code=500, detail=f"Video conversion failed: {e}")

    # Return the converted video file
    return FileResponse(output_path, filename=f"converted_video.{format.lower()}")
