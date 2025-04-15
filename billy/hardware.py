import time
import lgpio as GPIO

# 📌 GPIO Pin Assignments
# 📌 GPIO Pin Assignments (matching your old working setup)
BUTTON_PIN = 17
MOUTH_PIN = 22
HEAD_PIN = 23
HEAD_PIN_2 = 24  # <- THIS was missing in the new version!

# 🧠 Open GPIO chip
h = GPIO.gpiochip_open(0)

# 🧠 Setup GPIO pins
GPIO.gpio_claim_output(h, MOUTH_PIN)
GPIO.gpio_claim_output(h, HEAD_PIN)
GPIO.gpio_claim_output(h, HEAD_PIN_2)
GPIO.gpio_claim_input(h, BUTTON_PIN)

# Set default states for outputs
GPIO.gpio_write(h, MOUTH_PIN, 0)  # Mouth motor off
GPIO.gpio_write(h, HEAD_PIN, 0)   # Tail motor off
GPIO.gpio_write(h, HEAD_PIN_2, 0) # Tail motor off

# 🎬 Button Press Waiter
def wait_for_button():
    print("🔧 Waiting for button press...")
    while True:
        if GPIO.gpio_read(h, BUTTON_PIN) == 0:
            time.sleep(0.1)
            if GPIO.gpio_read(h, BUTTON_PIN) == 0:
                print("🎬 Button pressed!")
                return
        time.sleep(0.1)
