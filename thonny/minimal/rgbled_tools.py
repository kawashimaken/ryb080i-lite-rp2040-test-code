"""
Minimal RGB LED Control Tool
"""

import neopixel
from machine import Pin
import time
import _thread

# Colors
RED = (30, 0, 0)
GREEN = (0, 30, 0)
PURPLE = (15, 0, 15)
OFF = (0, 0, 0)

class MinimalRGBLED:
    def __init__(self, pin=2, count=8):
        try:
            self.pixels = neopixel.NeoPixel(Pin(pin), count)
            self.count = count
            self.animation_running = False
            self.set_off()
        except:
            self.pixels = None
    
    def set_all(self, color):
        """Set all LEDs to same color"""
        if self.pixels:
            self.stop_animation()
            try:
                self.pixels.fill(color)
                self.pixels.write()
            except:
                pass
    
    def set_scanning(self):
        """Purple for scanning (receiver)"""
        self.set_all(PURPLE)
    
    def set_advertising(self):
        """Purple flowing animation for transmitter"""
        if not self.pixels:
            return
        
        self.stop_animation()
        self.animation_running = True
        try:
            _thread.start_new_thread(self._flow_animation, ())
        except:
            self.set_all(PURPLE)  # Fallback to solid purple
    
    def set_unlocked(self):
        """Green for unlocked"""
        self.set_all(GREEN)
    
    def set_locked(self):
        """Red for locked"""
        self.set_all(RED)
    
    def set_off(self):
        """Turn off all LEDs"""
        self.stop_animation()
        if self.pixels:
            try:
                self.pixels.fill(OFF)
                self.pixels.write()
            except:
                pass
    
    def stop_animation(self):
        """Stop animation"""
        self.animation_running = False
        time.sleep(0.1)
    
    def _flow_animation(self):
        """Purple flowing animation - single point with fading trail"""
        position = 0.0
        direction = 1  # 1: forward, -1: backward
        trail_brightness = [0] * self.count  # Trail brightness for each LED
        
        while self.animation_running:
            try:
                self.pixels.fill(OFF)
                
                # Fade all trails
                for i in range(self.count):
                    if trail_brightness[i] > 0:
                        trail_brightness[i] = max(0, trail_brightness[i] - 3)  # Fade speed
                
                # Set current position (brightest point - whitish red)
                current_pos = int(position)
                if 0 <= current_pos < self.count:
                    trail_brightness[current_pos] = 25  # Brightest
                    self.pixels[current_pos] = (25, 5, 15)  # Whitish red/pink
                
                # Apply trail colors (purple)
                for i in range(self.count):
                    if trail_brightness[i] > 0 and i != current_pos:
                        brightness = trail_brightness[i]
                        purple_intensity = brightness // 2
                        self.pixels[i] = (purple_intensity, 0, purple_intensity)
                
                self.pixels.write()
                
                # Move position
                position += direction * 1.0
                
                # Change direction at ends
                if position >= self.count - 1:
                    position = self.count - 1
                    direction = -1
                elif position <= 0:
                    position = 0
                    direction = 1
                
                time.sleep(0.08)  # Slightly faster
                
            except:
                break
        
        # Turn off when animation stops
        if self.pixels:
            try:
                self.pixels.fill(OFF)
                self.pixels.write()
            except:
                pass