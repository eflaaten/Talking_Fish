import time
import lgpio as GPIO

# Define pins
MOUTH_PIN = 17
HEAD_PIN = 27

# Open GPIO chip
h = GPIO.gpiochip_open(0)

# Claim pins
GPIO.gpio_claim_output(h, MOUTH_PIN)
GPIO.gpio_claim_output(h, HEAD_PIN)

# Move Billy
print("👄 Flapping mouth...")
GPIO.gpio_write(h, MOUTH_PIN, 1)
time.sleep(1)
GPIO.gpio_write(h, MOUTH_PIN, 0)

print("🕺 Wagging tail...")
GPIO.gpio_write(h, HEAD_PIN, 1)
time.sleep(1)
GPIO.gpio_write(h, HEAD_PIN, 0)

# Release GPIO
GPIO.gpiochip_close(h)
