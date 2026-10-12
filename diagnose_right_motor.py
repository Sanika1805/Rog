import time
from gpiozero import PWMOutputDevice, OutputDevice

RIGHT_PWM_PIN = 19
RIGHT_DIR_PIN = 16
RIGHT_EN_PIN = 26

def run_hardware_wire_diagnostic():
    print("==================================================")
    print("  BLDC HARDWARE / PHASE WIRE DIAGNOSTIC (GPIO 19) ")
    print("==================================================")
    
    pwm = PWMOutputDevice(RIGHT_PWM_PIN, frequency=100)
    direction = OutputDevice(RIGHT_DIR_PIN)
    enable = OutputDevice(RIGHT_EN_PIN)

    enable.off() # Active LOW

    print("\n--- TEST 1: Low-Speed Torque Test (30% Duty Cycle) ---")
    print("Healthy 3-phase BLDC motors should turn at 30% speed.")
    print("If it hums/vibrates without turning, 1 phase wire is disconnected.")
    
    direction.on()
    pwm.value = 0.3
    time.sleep(3)
    pwm.value = 0
    time.sleep(1)

    print("\n--- TEST 2: Reverse Direction Test ---")
    print("Testing if reverse torque works properly...")
    direction.off()
    pwm.value = 0.4
    time.sleep(3)
    pwm.value = 0
    time.sleep(1)

    print("\n--- TEST 3: Positional Dead-Spot Sweep ---")
    print("We will pulse the motor 6 times for 0.5s with short pauses.")
    print("Observe if the motor gets stuck at specific shaft angles:\n")

    direction.on()
    stuck_count = 0
    for pulse in range(1, 7):
        print(f"Pulse {pulse}/6: Applying 50% PWM for 0.5 seconds...")
        pwm.value = 0.5
        time.sleep(0.5)
        pwm.value = 0
        time.sleep(1.5) # Wait for motor to stop completely
        
        user_check = input(f"Did Pulse {pulse} spin on its own? (y/n): ").strip().lower()
        if user_check == 'n':
            stuck_count += 1

    print("\n==================================================")
    print("              DIAGNOSTIC SUMMARY                  ")
    print("==================================================")
    
    if stuck_count == 0:
        print("[RESULT]: PASS. All 3 phases are connected and functioning.")
        print("          If the motor stuck on the ground earlier, the issue is purely")
        print("          mechanical binding/friction or low driver current limits.")
    elif stuck_count > 0:
        print(f"[RESULT]: FAIL ({stuck_count}/6 pulses failed to start).")
        print("          This confirms a HARDWARE issue:")
        print("          1. Loose/Disconnected Phase Wire (U, V, or W terminal).")
        print("          2. Bad solder joint on the motor phase harness.")
        print("          3. Damaged MOSFET channel on the BLDC driver board.")

    # Cleanup
    pwm.value = 0
    enable.off()

if __name__ == "__main__":
    try:
        run_hardware_wire_diagnostic()
    except KeyboardInterrupt:
        print("\n[!] Aborted by user.")