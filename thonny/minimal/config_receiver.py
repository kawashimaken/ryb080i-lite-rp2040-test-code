"""
BLE Door Lock Receiver - Minimal Configuration
"""

import time
import machine
from ryb080i_simple import SimpleBLE

class MinimalBLESetup:
    def __init__(self):
        self.ble = SimpleBLE()
        self.ble.set_debug(False)
    
    def send_command(self, command, timeout=3000):
        """Send command and wait for response"""
        self.ble.send_command_async(command)
        
        start = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start) < timeout:
            self.ble.process_uart_data()
            self.ble.process_command_queue()
            time.sleep(0.1)
        
        return True
    
    def configure(self):
        """Configure BLE module as receiver"""
        print("Configuring BLE receiver...")
        
        # Basic settings
        self.send_command("AT+NAME=PicoLock")
        self.send_command("AT+CRFOP=C")  # Max power
        self.send_command("AT+CNE=1")    # Enable connections
        
        # Reset detection
        time.sleep(2)
        
        # Enable BLE
        self.send_command("AT+CFUN=1")
        time.sleep(1)
        
        print("Configuration complete")
        return True

def main():
    print("BLE Receiver Configuration")
    
    setup = MinimalBLESetup()
    success = setup.configure()
    
    if success:
        print("✅ SUCCESS - Ready to run receiver.py")
    else:
        print("❌ FAILED - Check BLE module connection")
    
    return success

if __name__ == "__main__":
    main()