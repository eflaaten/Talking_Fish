import os
import time
from datetime import datetime
from picamera2 import Picamera2

default_save_dir = '/home/eflaaten/billy/captures'

def ensure_save_dir(save_dir=default_save_dir):
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

def capture_image(save_dir=default_save_dir):
    ensure_save_dir(save_dir)
    picam2 = Picamera2()
    config = picam2.create_still_configuration(raw={"size": (1280, 720)}, display="main")
    picam2.configure(config)
    picam2.start()
    time.sleep(0.5)  # Camera warm-up
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"billy_view_{timestamp}.jpg"
    filepath = os.path.join(save_dir, filename)
    picam2.capture_file(filepath)
    picam2.close()
    return filepath

def get_image_bytes(image_path):
    with open(image_path, 'rb') as f:
        return f.read()
