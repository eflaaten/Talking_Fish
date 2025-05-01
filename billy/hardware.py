import time
import lgpio as GPIO

# 📌 GPIO Pin Assignments
# 📌 GPIO Pin Assignments (matching your old working setup)
BUTTON_PIN = 17
MOUTH_PIN = 22
TAIL_PIN = 23
TAIL_PIN_2 = 24  # <- THIS was missing in the new version!
PWM_PIN = 18  # GPIO18 supports hardware PWM on Pi

# 🧠 Open GPIO chip
h = GPIO.gpiochip_open(0)

# 🧠 Setup GPIO pins
GPIO.gpio_claim_output(h, MOUTH_PIN)
GPIO.gpio_claim_output(h, TAIL_PIN)
GPIO.gpio_claim_output(h, TAIL_PIN_2)
GPIO.gpio_claim_output(h, PWM_PIN)
GPIO.gpio_claim_input(h, BUTTON_PIN)

# Set default states for outputs
GPIO.gpio_write(h, MOUTH_PIN, 0)  # Mouth motor off
GPIO.gpio_write(h, TAIL_PIN, 0)   # Tail motor off
GPIO.gpio_write(h, TAIL_PIN_2, 0) # Tail motor off
GPIO.gpio_write(h, PWM_PIN, 0)    # PWM off

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

# 🛠 Tail PWM Control
def set_tail_pwm(duty_cycle):
    # duty_cycle: 0-100 (%)
    freq = 1000  # 1kHz PWM frequency
    GPIO.tx_pwm(h, PWM_PIN, freq, duty_cycle)

def stop_tail_pwm():
    GPIO.tx_pwm(h, PWM_PIN, 1000, 0)  # Use 1000 Hz, 0% duty cycle instead of freq=0
