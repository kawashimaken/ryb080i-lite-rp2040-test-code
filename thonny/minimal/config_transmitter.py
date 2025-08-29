"""
BLE Key Fob Transmitter - Minimal Configuration
"""

import time
from ryb080i_simple import SimpleBLE

class MinimalTransmitterSetup:
    def __init__(self):
        self.ble = SimpleBLE()
        self.ble.set_debug(False)
    
    def send_command(self, command, timeout=3000):
        """Send command and wait"""
        self.ble.send_command_async(command)
        
        start = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start) < timeout:
            self.ble.process_uart_data()
            self.ble.process_command_queue()
            time.sleep(0.1)
        
        return True
    
    def configure(self):
        """Configure BLE module as transmitter (key)"""
        print("Configuring BLE transmitter...")
        
        # Basic settings
        self.send_command("AT+NAME=PicoKey")
        self.send_command("AT+CRFOP=C")    # Max power
        self.send_command("AT+CFUN=1")     # Enable BLE
        
        time.sleep(1)
        
        print("Configuration complete")
        return True

def main():
    print("BLE Transmitter (Key) Configuration")
    
    setup = MinimalTransmitterSetup()
    success = setup.configure()
    
    if success:
        print("✅ SUCCESS - Ready to run transmitter.py")
    else:
        print("❌ FAILED - Check BLE module connection")
    
    return success

if __name__ == "__main__":
    main()