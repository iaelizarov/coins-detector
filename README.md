# Coins Detection Application

## 1. Structure

The coins detection application is organized as follows:

- **API Endpoints:** Defined in the api.py file, the application provides endpoints for uploading images, performing detection, and retrieving information about detected coins.

- **Logic Functions:** All core logic for image processing, detection, and database operations is stored in utils.py. This includes functions for saving images, interacting with the database, and performing YOLO-based detections.

- **Database:** A SQLite database (image_detection.db) stores information about uploaded images, detection status, and bounding boxes for detected coins. The database has the following tables:
Table: `image_info`

| Column Name | Data Type | Description                        |
|-------------|-----------|------------------------------------|
| `image_id`  | INTEGER   | Primary key, auto-incremented ID. |
| `image_name`| TEXT      | Name of the image file.           |
| `is_detected` | BOOLEAN | Indicates whether detection is complete (default: 0). |

Table: `detector_info`

| Column Name    | Data Type | Description                                     |
|----------------|-----------|-------------------------------------------------|
| `detector_id`  | INTEGER   | Primary key, auto-incremented ID.              |
| `image_id`     | INTEGER   | Foreign key, references `image_info.image_id`. |
| `coin_id`      | INTEGER   | Identifier for the detected coin.              |
| `bounding_box` | TEXT      | Bounding box details in JSON format.           |

- **Storage:** Uploaded images are stored in the uploaded_images directory.

- **Docker Configuration:** The Dockerfile contains all the steps to set up the application in a containerized environment, which includes creating the database using create_db.py script, and launching the server in main

## 2. How to Run It

**Build the Docker Image**

`docker build -t coins-detection-app .`

**Run the Docker Container**

`docker run -d -p 8000:8000 --name coins-app coins-detection-app`

**Access the Running Application**

The application will be accessible at http://127.0.0.1:8000.

## 3. Description of API Requests

**1. Upload Image**

Endpoint: `POST /api/upload-image/`

Description: Upload an image to the server and save its metadata in the database.

**2. Perform Detection**

Endpoint: `GET /api/detect-image/{image_name}`

Description: Perform YOLO detection on the specified image and save the results in the database

**3. Get Detection Results**

Endpoint: `GET /api/get-detection/{image_name}`

Description: Retrieve detection results for a specific image, including all the bounding boxes.

**4. Get Coin Details**

Endpoint: GET `/api/get-coin/`

Description: Retrieve details for a specific coin detected in an image, including its center, and radius.

## 4. Visualization of the results

There is a notebook "coins_test_requests.ipynb" attached that contains all the requests and the results of the visualization

## 5. Borderline cases

If a coin is cropped by the border of the image, calculating its mask becomes more challenging. This application accounts for four cases where a coin is cropped by any side of the image. However, performance may degrade if the coin is located in a corner, as it becomes impossible to accurately determine its actual size compared to when it is cropped along a single border.
