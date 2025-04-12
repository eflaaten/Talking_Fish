import time
import lgpio as GPIO

# 📌 GPIO Pin Assignments
MOUTH_PIN = 17
TAIL_PIN = 27
BUTTON_PIN = 17  # You can change if needed

# 🛠 GPIO Setup
h = GPIO.gpiochip_open(0)
GPIO.gpio_claim_output(h, MOUTH_PIN)
GPIO.gpio_claim_output(h, TAIL_PIN)
GPIO.gpio_claim_input(h, BUTTON_PIN)

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
