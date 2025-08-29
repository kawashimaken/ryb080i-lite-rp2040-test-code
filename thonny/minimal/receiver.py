"""
BLE Door Lock Receiver - Minimal Version
"""

import time
from ryb080i_simple import SimpleBLE, SimpleAutoScanManager
from oled_tools import MinimalOLED
from rgbled_tools import MinimalRGBLED

# Settings
RSSI_THRESHOLD = -60
RSSI_TIMEOUT = 5000
SCAN_INTERVAL = 3000
TARGET_DEVICE = "PicoKey"

# System states
class State:
    SCANNING = "SCAN"
    UNLOCKED = "UNLOCK"
    LOCKED = "LOCK"

# Global variables
ble = None
oled = None
led = None
scanner = None
current_state = State.SCANNING

def on_scan_result(device_list):
    """Handle scan results"""
    for device in device_list:
        name = device.get('name', '')
        rssi_text = device.get('rssi', '')
        
        if TARGET_DEVICE.upper() in name.upper():
            rssi = ble.parse_rssi_from_text(rssi_text)
            if rssi:
                ble.update_rssi_data(rssi)
                print(f"Found {TARGET_DEVICE}: {rssi}dBm")

def update_state():
    """Update system state based on RSSI"""
    global current_state
    
    rssi = ble.get_current_rssi()
    timeout = ble.check_rssi_timeout(RSSI_TIMEOUT)
    
    if timeout:
        new_state = State.SCANNING
    elif rssi > RSSI_THRESHOLD:
        new_state = State.UNLOCKED
    else:
        new_state = State.LOCKED
    
    if new_state != current_state:
        current_state = new_state
        
        # Update displays
        if oled:
            oled.show_status(current_state, rssi)
        
        if led:
            if current_state == State.SCANNING:
                led.set_scanning()
            elif current_state == State.UNLOCKED:
                led.set_unlocked()
            else:
                led.set_locked()
        
        print(f"State: {current_state} (RSSI: {rssi})")

def init_system():
    """Initialize all components"""
    global ble, oled, led, scanner
    
    print("Initializing BLE Door Lock...")
    
    # BLE
    ble = SimpleBLE()
    ble.set_callback('scan_result', on_scan_result)
    
    # OLED
    oled = MinimalOLED()
    
    # LED
    led = MinimalRGBLED()
    
    # Auto scanner
    scanner = SimpleAutoScanManager(ble, SCAN_INTERVAL)
    scanner.start()
    
    print("System ready")

def main():
    """Main loop"""
    print("BLE Door Lock - Minimal Version")
    print(f"Threshold: {RSSI_THRESHOLD}dBm")
    
    init_system()
    
    try:
        while True:
            # Process BLE
            ble.process_uart_data()
            ble.process_command_queue()
            
            # Auto scan
            if scanner.should_scan():
                scanner.trigger_scan()
            
            # Update state
            update_state()
            
            time.sleep(0.05)
            
    except KeyboardInterrupt:
        print("Shutting down...")
        if led:
            led.set_off()

if __name__ == "__main__":
    main()