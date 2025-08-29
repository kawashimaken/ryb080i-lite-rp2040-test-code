"""
RYB080I BLE Module - Minimal Version
"""

import machine
import time
from machine import Pin, UART
import re

class SimpleBLE:
    def __init__(self):
        self.uart = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))
        self.callbacks = {}
        self.connection_state = {
            'current_rssi': -100,
            'last_rssi_time': 0
        }
        self.response_buffer = ""
        self.command_queue = []
        self.command_id = 0
        self.scan_stats = {'total_scans': 0, 'found_count': 0}
        time.sleep(0.1)
    
    def set_debug(self, enabled):
        pass  # Debug removed for minimal version
    
    def set_callback(self, event_type, callback_func):
        self.callbacks[event_type] = callback_func
    
    def _trigger_callback(self, event_type, *args):
        callback = self.callbacks.get(event_type)
        if callback:
            try:
                callback(*args)
            except:
                pass
    
    def parse_rssi_from_text(self, rssi_text):
        """Extract RSSI value from text"""
        try:
            match = re.search(r'(-?\s*\d+)', rssi_text)
            if match:
                rssi = int(match.group(1).replace(" ", ""))
                if -150 <= rssi <= 0:
                    return rssi
        except:
            pass
        return None
    
    def process_uart_data(self):
        """Process incoming UART data"""
        if self.uart.any():
            try:
                data = self.uart.read().decode('utf-8')
                self.response_buffer += data
                
                while '\n' in self.response_buffer:
                    line_end = self.response_buffer.find('\n')
                    line = self.response_buffer[:line_end].strip()
                    self.response_buffer = self.response_buffer[line_end + 1:]
                    
                    if line:
                        self._process_line(line)
            except:
                pass
    
    def _process_line(self, line):
        """Process received line"""
        # Scan result detection
        if line.startswith('+') and ':0x' in line and ',' in line:
            device_info = self._parse_scan_result(line)
            if device_info:
                self._trigger_callback('scan_result', [device_info])
        else:
            self._trigger_callback('response', None, line)
    
    def _parse_scan_result(self, line):
        """Parse scan result line"""
        try:
            parts = line.split(',')
            if len(parts) >= 2:
                return {
                    "name": parts[1].strip(),
                    "rssi": parts[2].strip() if len(parts) > 2 else "Unknown"
                }
        except:
            pass
        return None
    
    def process_command_queue(self):
        """Process command queue"""
        current_time = time.ticks_ms()
        
        if self.command_queue and self.uart:
            cmd = self.command_queue.pop(0)
            
            try:
                self.uart.write(b'A')
                time.sleep(0.01)
                
                full_command = cmd['command']
                if not full_command.endswith('\r\n'):
                    full_command += '\r\n'
                
                self.uart.write(full_command.encode())
                self.uart.flush()
            except:
                pass
    
    def send_command_async(self, command):
        """Queue command for sending"""
        cmd_id = self.command_id
        self.command_id += 1
        
        self.command_queue.append({
            'id': cmd_id,
            'command': command,
            'timestamp': time.ticks_ms()
        })
        
        return cmd_id
    
    def start_scan_async(self):
        """Start BLE scan"""
        self.scan_stats['total_scans'] += 1
        return self.send_command_async("AT+SCAN")
    
    def start_advertising_async(self):
        """Start advertising"""
        return self.send_command_async("AT+ADVEN=1")
    
    def get_current_rssi(self):
        return self.connection_state['current_rssi']
    
    def check_rssi_timeout(self, timeout_ms):
        current_time = time.ticks_ms()
        last_time = self.connection_state['last_rssi_time']
        return time.ticks_diff(current_time, last_time) > timeout_ms
    
    def update_rssi_data(self, rssi_value):
        """Update RSSI data"""
        self.connection_state['current_rssi'] = rssi_value
        self.connection_state['last_rssi_time'] = time.ticks_ms()
    
    def update_found_count(self):
        self.scan_stats['found_count'] += 1

class SimpleAutoScanManager:
    """Auto scan manager"""
    
    def __init__(self, ble_module, interval_ms=3000):
        self.ble = ble_module
        self.interval_ms = interval_ms
        self.last_scan_time = 0
        self.running = False
    
    def should_scan(self):
        if not self.running:
            return False
        
        current_time = time.ticks_ms()
        return time.ticks_diff(current_time, self.last_scan_time) >= self.interval_ms
    
    def trigger_scan(self):
        if self.ble:
            self.ble.start_scan_async()
            self.last_scan_time = time.ticks_ms()
    
    def start(self):
        self.running = True
    
    def stop(self):
        self.running = False