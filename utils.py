import os
import sqlite3
from PIL import Image
import json
from ultralytics import YOLO
from typing import List, Dict, Tuple


def save_image_to_disk(image, folder: str) -> str:
    """
    Save the uploaded image to the specified folder.

    Args:
        image: The uploaded image file.
        folder (str): The folder path where the image will be saved.

    Returns:
        str: The file path of the saved image.
    """
    file_path = os.path.join(folder, image.filename)
    with open(file_path, "wb") as f:
        f.write(image.file.read())
    return file_path


def add_image_to_db(db_path: str, image_path: str) -> None:
    """
    Add image information to the database if it doesn't already exist.

    Args:
        db_path (str): Path to the SQLite database.
        image_path (str): Path to the image file.

    Raises:
        ValueError: If the image already exists in the database.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    image_base_name = os.path.basename(image_path)

    cursor.execute("SELECT COUNT(*) FROM image_info WHERE image_name = ?", (image_base_name,))
    exists = cursor.fetchone()[0]

    if exists:
        raise ValueError(f"Image '{image_base_name}' already exists in the database. Skipping insertion.")
    else:
        cursor.execute("INSERT INTO image_info (image_name, is_detected) VALUES (?, ?)", (image_base_name, False))
        conn.commit()

    conn.close()


def perform_detection(db_path: str, image_name: str, folder: str = './uploaded_images/') -> bool:
    """
    Run YOLOv8 detection and update the database with results.

    Args:
        db_path (str): Path to the SQLite database.
        image_name (str): Name of the image file.
        folder (str): Folder where the image is stored.

    Returns:
        bool: True if detection is successful.

    Raises:
        ValueError: If the image does not exist or detection is already performed.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    image_path = os.path.join(folder, image_name)
    cursor.execute("SELECT image_id, is_detected FROM image_info WHERE image_name = ?", (image_name,))
    image_row = cursor.fetchone()
    if not image_row:
        raise ValueError("Image not found in database.")
    if image_row[1]:
        raise ValueError("Detection already performed on this image.")

    image_id = image_row[0]

    model = YOLO("./weights/best.pt")
    results = model(image_path)

    detections = []
    for detection in results[0].boxes:
        box = detection.xyxy[0].tolist()
        bounding_box = {"x_min": box[0], "y_min": box[1], "x_max": box[2], "y_max": box[3]}
        detections.append(bounding_box)

    for i, bbox in enumerate(detections, start=1):
        cursor.execute(
            "INSERT INTO detector_info (image_id, coin_id, bounding_box) VALUES (?, ?, ?)",
            (image_id, i, json.dumps(bbox)),
        )
    cursor.execute("UPDATE image_info SET is_detected = ? WHERE image_id = ?", (True, image_id))
    conn.commit()
    conn.close()

    return True


def get_detection_results(db_path: str, image_name: str) -> List[Dict[str, any]]:
    """
    Retrieve detection results from the database.

    Args:
        db_path (str): Path to the SQLite database.
        image_name (str): Name of the image file.

    Returns:
        List[Dict[str, any]]: A list of detection results with coin IDs and bounding boxes.

    Raises:
        ValueError: If the image is not found or detection is not performed.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT is_detected FROM image_info WHERE image_name = ?", (image_name,))
    image_row = cursor.fetchone()
    if not image_row:
        raise ValueError("Image not found in database.")
    if not image_row[0]:
        raise ValueError("Detection has not been performed on this image.")

    cursor.execute(
        "SELECT coin_id, bounding_box FROM detector_info WHERE image_id = (SELECT image_id FROM image_info WHERE image_name = ?)",
        (image_name,),
    )
    results = cursor.fetchall()
    conn.close()

    if not results:
        raise ValueError("No detection results found.")

    return [{"coin_id": row[0], "bounding_box": json.loads(row[1])} for row in results]


def get_centroid(
    image_name: str, object_number: int, db_path: str = "image_detection.db", folder: str = './uploaded_images/'
) -> Tuple[float, float, float]:
    """
    Get the centroid and radius of a bounding box.

    Args:
        image_name (str): Name of the image file.
        object_number (int): Object number in the image.
        db_path (str): Path to the SQLite database.
        folder (str): Folder where the image is stored.

    Returns:
        Tuple[float, float, float]: Centroid coordinates (x, y) and radius.

    Raises:
        ValueError: If bounding box or image is not found.
    """
    bounding_box = get_coin_bounding_box(image_name, object_number, db_path)
    
    # Ensure bounding_box is deserialized from JSON if not already
    if isinstance(bounding_box, str):
        bounding_box = json.loads(bounding_box)
    
    image_path = os.path.join(folder, image_name)
    if not os.path.exists(image_path):
        raise ValueError(f"Image file '{image_path}' not found.")

    img = Image.open(image_path)
    img_height, img_width = img.height, img.width

    # Calculate the center
    x_center, y_center = get_bbox_center(bounding_box, img_height, img_width)

    # Calculate the radius as the max of height or width of the bounding box
    width = bounding_box['x_max'] - bounding_box['x_min']
    height = bounding_box['y_max'] - bounding_box['y_min']
    radius = max(width, height) / 2

    return x_center, y_center, radius


def get_coin_bounding_box(image_name: str, object_number: int, db_path: str = "image_detection.db") -> Dict[str, float]:
    """
    Retrieve bounding box for a specific object number in an image from the database.

    Args:
        image_name (str): Name of the image file.
        object_number (int): Object number in the image.
        db_path (str): Path to the SQLite database.

    Returns:
        Dict[str, float]: Bounding box as a dictionary.

    Raises:
        ValueError: If the object is not found.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT bounding_box
        FROM detector_info di
        JOIN image_info ii ON di.image_id = ii.image_id
        WHERE ii.image_name = ? AND di.coin_id = ?
    """, (image_name, object_number))

    result = cursor.fetchone()
    conn.close()

    if result:
        # Deserialize bounding box from JSON string to dictionary
        return json.loads(result[0])
    else:
        raise ValueError(f"No object found for {image_name} and object number {object_number}.")


def get_bbox_center(bounding_box: Dict[str, float], img_height: int, img_width: int) -> Tuple[float, float]:
    """
    Calculate the center of a bounding box.

    Args:
        bounding_box (Dict[str, float]): Bounding box coordinates.
        img_height (int): Image height.
        img_width (int): Image width.

    Returns:
        Tuple[float, float]: Center coordinates (x, y).
    """
    cropped = which_side_cropped(bounding_box, img_height, img_width)
    
    if cropped == 'regular':
        x_center = (bounding_box['x_min'] + bounding_box['x_max']) / 2
        y_center = (bounding_box['y_min'] + bounding_box['y_max']) / 2
    elif cropped == 'top':
        x_center = (bounding_box['x_min'] + bounding_box['x_max']) / 2
        width = bounding_box['x_max'] - bounding_box['x_min']
        y_center = bounding_box['y_max'] - width / 2
    elif cropped == 'left':
        height = bounding_box['y_max'] - bounding_box['y_min']
        x_center = bounding_box['x_max'] - height / 2
        y_center = (bounding_box['y_max'] + bounding_box['y_min']) / 2
    elif cropped == 'bottom':
        x_center = (bounding_box['x_min'] + bounding_box['x_max']) / 2
        width = bounding_box['x_max'] - bounding_box['x_min']
        y_center = bounding_box['y_min'] + width / 2
    elif cropped == 'right':
        height = bounding_box['y_max'] - bounding_box['y_min']
        x_center = bounding_box['x_min'] + height / 2
        y_center = (bounding_box['y_max'] + bounding_box['y_min']) / 2
    return x_center, y_center


def which_side_cropped(bounding_box: Dict[str, float], img_height: int, img_width: int) -> str:
    """
    Determine which side of the bounding box is cropped.

    Args:
        bounding_box (Dict[str, float]): Bounding box coordinates.
        img_height (int): Image height.
        img_width (int): Image width.

    Returns:
        str: The cropped side ('top', 'left', 'bottom', 'right', or 'regular').
    """
    if bounding_box['y_min'] == 0:
        return 'top'
    elif bounding_box['x_min'] == 0:
        return 'left'
    elif bounding_box['y_max'] == img_height:
        return 'bottom'
    elif bounding_box['x_max'] == img_width:
        return 'right'
    else:
        return 'regular'
