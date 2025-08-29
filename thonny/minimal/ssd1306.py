# High-performance SSD1306 library for Raspberry Pi Pico
# Save this as "ssd1306_fast.py"

from micropython import const
import framebuf
import time

# register definitions
SET_CONTRAST = const(0x81)
SET_ENTIRE_ON = const(0xA4)
SET_NORM_INV = const(0xA6)
SET_DISP = const(0xAE)
SET_MEM_ADDR = const(0x20)
SET_COL_ADDR = const(0x21)
SET_PAGE_ADDR = const(0x22)
SET_DISP_START_LINE = const(0x40)
SET_SEG_REMAP = const(0xA0)
SET_MUX_RATIO = const(0xA8)
SET_COM_OUT_DIR = const(0xC0)
SET_DISP_OFFSET = const(0xD3)
SET_COM_PIN_CFG = const(0xDA)
SET_DISP_CLK_DIV = const(0xD5)
SET_PRECHARGE = const(0xD9)
SET_VCOM_DESEL = const(0xDB)
SET_CHARGE_PUMP = const(0x8D)

class SSD1306(framebuf.FrameBuffer):
    def __init__(self, width, height, external_vcc):
        self.width = width
        self.height = height
        self.external_vcc = external_vcc
        self.pages = self.height // 8
        self.buffer = bytearray(self.pages * self.width)
        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_VLSB)
        self.init_display()

    def init_display(self):
        # Initialization commands grouped in an array
        init_sequence = [
            SET_DISP | 0x00,  # off
            SET_MEM_ADDR, 0x00,  # horizontal addressing
            SET_DISP_START_LINE | 0x00,
            SET_SEG_REMAP | 0x01,
            SET_MUX_RATIO, self.height - 1,
            SET_COM_OUT_DIR | 0x08,
            SET_DISP_OFFSET, 0x00,
            SET_COM_PIN_CFG, 0x02 if self.width > 2 * self.height else 0x12,
            SET_DISP_CLK_DIV, 0x80,
            SET_PRECHARGE, 0x22 if self.external_vcc else 0xF1,
            SET_VCOM_DESEL, 0x30,
            SET_CONTRAST, 0xFF,
            SET_ENTIRE_ON,
            SET_NORM_INV,
            SET_CHARGE_PUMP, 0x10 if self.external_vcc else 0x14,
            SET_DISP | 0x01,  # on
        ]
        
        for cmd in init_sequence:
            self.write_cmd(cmd)
            # Minimal wait time
            time.sleep_us(100)  # 0.1ms in microseconds
        
        self.fill(0)
        self.show()

    def poweroff(self):
        self.write_cmd(SET_DISP | 0x00)

    def poweron(self):
        self.write_cmd(SET_DISP | 0x01)

    def contrast(self, contrast):
        self.write_cmd(SET_CONTRAST)
        self.write_cmd(contrast)

    def invert(self, invert):
        self.write_cmd(SET_NORM_INV | (invert & 1))

    def show(self):
        x0 = 0
        x1 = self.width - 1
        if self.width == 64:
            x0 += 32
            x1 += 32
        
        # Send address setting commands in one sequence
        self.write_cmd(SET_COL_ADDR)
        self.write_cmd(x0)
        self.write_cmd(x1)
        self.write_cmd(SET_PAGE_ADDR)
        self.write_cmd(0)
        self.write_cmd(self.pages - 1)
        self.write_data(self.buffer)

class SSD1306_I2C(SSD1306):
    def __init__(self, width, height, i2c, addr=0x3C, external_vcc=False):
        self.i2c = i2c
        self.addr = addr
        self.temp = bytearray(2)
        self.write_list = [b"\x40", None]
        # Performance settings
        self.fast_mode = True
        self.max_chunk_size = 128  # Larger chunk size
        super().__init__(width, height, external_vcc)

    def write_cmd(self, cmd):
        self.temp[0] = 0x80
        self.temp[1] = cmd
        
        if self.fast_mode:
            try:
                self.i2c.writeto(self.addr, self.temp)
                # In fast mode, minimize wait time
                time.sleep_us(50)  # 50 microseconds
            except OSError:
                # Switch to safe mode only on error
                self._safe_write_cmd(cmd)
        else:
            self._safe_write_cmd(cmd)
    
    def _safe_write_cmd(self, cmd):
        """Command transmission in safe mode"""
        self.temp[0] = 0x80
        self.temp[1] = cmd
        try:
            self.i2c.writeto(self.addr, self.temp)
            time.sleep_us(500)
        except OSError as e:
            print(f"Command write error: {e}")
            time.sleep_us(5000)  # 5ms
            self.fast_mode = False  # Switch to safe mode

    def write_data(self, buf):
        if self.fast_mode:
            # Fast mode: try sending in large chunks
            try:
                self._write_data_fast(buf)
            except OSError:
                # On error, fallback to safe mode
                self.fast_mode = False
                self._write_data_safe(buf)
        else:
            self._write_data_safe(buf)
    
    def _write_data_fast(self, buf):
        """Fast data transmission"""
        chunk_size = self.max_chunk_size
        
        for i in range(0, len(buf), chunk_size):
            chunk = buf[i:i+chunk_size]
            self.write_list[1] = chunk
            self.i2c.writevto(self.addr, self.write_list)
            # Minimal wait time
            if len(chunk) > 64:
                time.sleep_us(200)  # Only for larger chunks
    
    def _write_data_safe(self, buf):
        """Safe data transmission"""
        chunk_size = 32
        
        for i in range(0, len(buf), chunk_size):
            chunk = buf[i:i+chunk_size]
            self.write_list[1] = chunk
            
            retry_count = 3
            for attempt in range(retry_count):
                try:
                    self.i2c.writevto(self.addr, self.write_list)
                    time.sleep_us(500)
                    break
                except OSError as e:
                    if attempt == retry_count - 1:
                        print(f"Data write failed after {retry_count} attempts: {e}")
                    time.sleep_us(2000)  # Retry after 2ms
    
    def enable_fast_mode(self):
        """Enable fast mode"""
        self.fast_mode = True
        self.max_chunk_size = 128
    
    def enable_safe_mode(self):
        """Enable safe mode (compatibility-focused)"""
        self.fast_mode = False
        self.max_chunk_size = 32

# SPI version also optimized
class SSD1306_SPI(SSD1306):
    def __init__(self, width, height, spi, dc, res, cs, external_vcc=False):
        self.rate = 20 * 1024 * 1024  # Increase SPI clock
        dc.init(dc.OUT, value=0)
        res.init(res.OUT, value=0)
        cs.init(cs.OUT, value=1)
        self.spi = spi
        self.dc = dc
        self.res = res
        self.cs = cs
        
        # Optimized reset process
        self.res(1)
        time.sleep_us(1000)  # 1ms
        self.res(0)
        time.sleep_us(10000)  # 10ms
        self.res(1)
        super().__init__(width, height, external_vcc)

    def write_cmd(self, cmd):
        self.spi.init(baudrate=self.rate, polarity=0, phase=0)
        self.cs(1)
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)

    def write_data(self, buf):
        self.spi.init(baudrate=self.rate, polarity=0, phase=0)
        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(buf)
        self.cs(1)
