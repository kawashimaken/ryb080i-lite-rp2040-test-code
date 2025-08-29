"""
Minimal OLED Display Tool
"""

from machine import Pin, I2C

try:
    from ssd1306 import SSD1306_I2C
    OLED_AVAILABLE = True
except ImportError:
    OLED_AVAILABLE = False

class MinimalOLED:
    def __init__(self, sda_pin=8, scl_pin=9):
        self.display = None
        
        if not OLED_AVAILABLE:
            return
        
        try:
            i2c = I2C(0, sda=Pin(sda_pin), scl=Pin(scl_pin), freq=40000)
            self.display = SSD1306_I2C(128, 64, i2c, addr=0x3C)
            self.display.fill(0)
            self.display.show()
        except:
            self.display = None
    
    def show_status(self, status, rssi=None):
        """Show system status"""
        if not self.display:
            return
        
        try:
            self.display.fill(0)
            
            # RSSI
            if rssi and rssi > -100:
                self.display.text(f"RSSI:{rssi}", 0, 0)
            else:
                self.display.text("No Signal", 0, 0)
            
            # Status
            self.display.text(status, 0, 25)
            
            self.display.show()
        except:
            pass