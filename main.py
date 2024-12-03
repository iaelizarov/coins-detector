from fastapi import FastAPI
import uvicorn
from api_service import app as api_app
import os

# Ensure necessary directories exist
UPLOAD_FOLDER = "./uploaded_images"
DB_PATH = "image_detection.db"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Create the FastAPI application
app = FastAPI()

# Include the API service as a router
app.mount("/api", api_app)


if __name__ == "__main__":
    # Run the application
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
