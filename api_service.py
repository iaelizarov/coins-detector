from fastapi import FastAPI, File, UploadFile, HTTPException
import os
from utils import (
    save_image_to_disk,
    add_image_to_db,
    get_detection_results,
    perform_detection,
    get_centroid
)

# Constants
UPLOAD_FOLDER = "./uploaded_images"
DB_PATH = "image_detection.db"

# Initialize FastAPI app
app = FastAPI()

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.post("/upload-image/")
def upload_image(image: UploadFile = File(...)):
    """Upload an image and store it in the database."""
    try:
        # Save image to disk
        file_path = save_image_to_disk(image, UPLOAD_FOLDER)

        # Add image to the database
        add_image_to_db(DB_PATH, file_path)

        return {"message": "Image uploaded successfully.", "image_path": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading image: {e}")


@app.get("/get-detection/{image_name}")
def get_detection(image_name: str):
    """Retrieve detection results for an image."""
    try:
        # Get detection results
        detection_results = get_detection_results(DB_PATH, image_name)
        return {"image_name": image_name, "detection_results": detection_results}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving detection: {e}")


@app.get("/detect-image/{image_name}")
def detect_image(image_name: str):
    """Run detection on an image and update the database."""
    try:
        # Perform detection
        detection_status = perform_detection(DB_PATH, image_name, UPLOAD_FOLDER)

        if detection_status:
            return {"message": "Detection completed successfully."}
        else:
            raise ValueError("Detection could not be completed.")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error applying detection: {e}")
    

@app.get("/get-coin/")
def get_coin(image_name: str, object_number: int):
    """
    Get bounding box centroid and radius for a specific object number in an image.

    Args:
        image_name (str): The name of the image.
        object_number (int): The object number in the image.

    Returns:
        dict: Centroid coordinates (x, y) and radius.

    Raises:
        HTTPException: If any errors occur during processing.
    """
    try:
        x_center, y_center, radius = get_centroid(image_name, object_number)
        return {
            "image_name": image_name,
            "object_number": object_number,
            "x_center": x_center,
            "y_center": y_center,
            "radius": radius
        }
    except ValueError as e:
        # Handle specific errors, such as missing data in the database
        raise HTTPException(status_code=404, detail=f"Not found: {e}")
    except Exception as e:
        # Handle generic errors
        raise HTTPException(status_code=500, detail=f"Error fetching centroid: {e}")
    


