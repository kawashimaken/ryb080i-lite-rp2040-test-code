"""
BLE Key Fob Transmitter - Minimal Version
"""
import time
from ryb080i_simple import SimpleBLE
from oled_tools import MinimalOLED
from rgbled_tools import MinimalRGBLED

# Settings
ADVERTISING_INTERVAL = 15000  # Restart advertising every 15 seconds

# Global variables
ble = None
oled = None
led = None

def init_system():
    """Initialize all components"""
    global ble, oled, led
    
    print("Initializing BLE Key Fob...")
    
    # BLE
    ble = SimpleBLE()
    
    # OLED - Use new centered large text feature
    oled = MinimalOLED()
    if oled.display:
        # Show ADVERTISING with large centered text
        oled.show_status("ADVERTISING")
    
    # LED - Purple flowing animation for advertising
    led = MinimalRGBLED()
    if led:
        led.set_advertising()  # Purple flowing animation
    
    print("Key Fob ready")

def start_advertising():
    """Start BLE advertising"""
    if ble:
        ble.start_advertising_async()

def main():
    """Main advertising loop"""
    print("BLE Key Fob Transmitter - Minimal Version")
    
    init_system()
    start_advertising()
    
    last_advertising = time.ticks_ms()
    
    try:
        while True:
            current_time = time.ticks_ms()
            
            # Process BLE
            ble.process_uart_data()
            ble.process_command_queue()
            
            # Restart advertising periodically
            if time.ticks_diff(current_time, last_advertising) >= ADVERTISING_INTERVAL:
                start_advertising()
                last_advertising = current_time
            
            time.sleep(0.05)
            
    except KeyboardInterrupt:
        print("Shutting down...")
        if led:
            led.set_off()
        if oled and oled.display:
            oled.display.fill(0)
            oled.display.show()

if __name__ == "__main__":
    main()