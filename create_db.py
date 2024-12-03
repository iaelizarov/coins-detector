import sqlite3

# Create a new SQLite database (or connect to an existing one)
db_path = "image_detection.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create the image_info table
cursor.execute('''
CREATE TABLE IF NOT EXISTS image_info (
    image_id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_name TEXT NOT NULL UNIQUE,
    is_detected BOOLEAN NOT NULL DEFAULT 0
)
''')

# Create the detector_info table
cursor.execute('''
CREATE TABLE IF NOT EXISTS detector_info (
    detector_id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_id INTEGER NOT NULL,
    coin_id INTEGER NOT NULL,
    bounding_box TEXT NOT NULL, -- Stored as JSON to capture bbox coordinates
    FOREIGN KEY (image_id) REFERENCES image_info(image_id) ON DELETE CASCADE
)
''')

# Commit changes and close the connection
conn.commit()
conn.close()

print(f"Database created successfully at '{db_path}'")
