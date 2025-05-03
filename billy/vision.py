import os
import time
from datetime import datetime
from picamera2 import Picamera2

default_save_dir = '/home/eflaaten/billy/captures'

# Persistent camera object for speed
picam2_instance = None

def get_camera():
    global picam2_instance
    if picam2_instance is None:
        picam2_instance = Picamera2()
        config = picam2_instance.create_still_configuration(raw={"size": (640, 360)}, display="main")
        picam2_instance.configure(config)
        picam2_instance.start()
        time.sleep(0.2)  # Shorter warm-up since we keep it open
    return picam2_instance

def ensure_save_dir(save_dir=default_save_dir):
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

def capture_image(save_dir=default_save_dir):
    ensure_save_dir(save_dir)
    try:
        picam2 = get_camera()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"billy_view_{timestamp}.jpg"
        filepath = os.path.join(save_dir, filename)
        picam2.capture_file(filepath)
        print(f"📸 Photo taken: {filepath}")
        return filepath
    except Exception as e:
        print(f"[VISION ERROR] Could not capture image: {e}")
        return None

def get_image_bytes(image_path):
    with open(image_path, 'rb') as f:
        return f.read()
