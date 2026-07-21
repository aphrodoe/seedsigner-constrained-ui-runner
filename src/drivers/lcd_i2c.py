import time
try:
    import smbus2 as smbus
except ImportError:
    import smbus  # type: ignore

# I2C device constants
LCD_CHR = 1 # Mode - Sending data
LCD_CMD = 0 # Mode - Sending command

LCD_LINE_1 = 0x80 # LCD RAM address for the 1st line
LCD_LINE_2 = 0xC0 # LCD RAM address for the 2nd line
LCD_LINE_3 = 0x94 # LCD RAM address for the 3rd line
LCD_LINE_4 = 0xD4 # LCD RAM address for the 4th line

LCD_BACKLIGHT  = 0x08  # On
LCD_NOBACKLIGHT = 0x00  # Off

ENABLE = 0b00000100 # Enable bit

# Timing constants
E_PULSE = 0.0005
E_DELAY = 0.0005

class LCDI2C:
    def __init__(self, i2c_addr=0x27, bus_num=1, rows=2, cols=16):
        self.i2c_addr = i2c_addr
        self.bus = smbus.SMBus(bus_num)
        self.rows = rows
        self.cols = cols
        self._backlight = LCD_BACKLIGHT
        
        self.row_offsets = [LCD_LINE_1, LCD_LINE_2, LCD_LINE_3, LCD_LINE_4]
        self._init_lcd()

    def _init_lcd(self):
        """Initialize display"""
        self._lcd_byte(0x33, LCD_CMD) # 110011 Initialize
        self._lcd_byte(0x32, LCD_CMD) # 110010 Initialize
        self._lcd_byte(0x06, LCD_CMD) # 000110 Cursor move direction
        self._lcd_byte(0x0C, LCD_CMD) # 001100 Display On,Cursor Off, Blink Off 
        self._lcd_byte(0x28, LCD_CMD) # 101000 Data length, number of lines, font size
        self._lcd_byte(0x01, LCD_CMD) # 000001 Clear display
        time.sleep(E_DELAY)
        
        # Load custom character bitmaps into CGRAM slots 0-3
        custom_chars = {
            0: [0b00000, 0b00001, 0b00011, 0b10110, 0b11100, 0b01000, 0b00000, 0b00000], # ✓ (Success)
            1: [0b00100, 0b01010, 0b01110, 0b01110, 0b11111, 0b00000, 0b00100, 0b00000], # ⚠ (Warning)
            2: [0b01010, 0b01010, 0b01010, 0b01010, 0b00000, 0b01010, 0b01010, 0b00000], # ‼ (Dire Warning)
            3: [0b00000, 0b10001, 0b01010, 0b00100, 0b01010, 0b10001, 0b00000, 0b00000], # ✕ (Error)
            4: [0b11011, 0b10101, 0b11011, 0b00000, 0b10010, 0b01001, 0b11011, 0b00000], # ▦ (QR Code)
            5: [0b01110, 0b10001, 0b01110, 0b00100, 0b00111, 0b00100, 0b00111, 0b00000], # ⚿ (Key)
            6: [0b01100, 0b10010, 0b01100, 0b00100, 0b00010, 0b00001, 0b00000, 0b00000], # ⚒ (Wrench)
            7: [0b01010, 0b01110, 0b11011, 0b01110, 0b01010, 0b00000, 0b00000, 0b00000]  # ⚙ (Gear)
        }
        for loc, charmap in custom_chars.items():
            self.load_custom_character(loc, charmap)

    def load_custom_character(self, location: int, charmap: list):
        """Load a custom 5x8 character into CGRAM (location 0-7)"""
        location &= 0x07  # restrict to 0-7
        self._lcd_byte(0x40 | (location << 3), LCD_CMD)
        for i in range(8):
            self._lcd_byte(charmap[i], LCD_CHR)

    def _lcd_byte(self, bits, mode):
        """Send byte to data pins
        bits = the data
        mode = 1 for data, 0 for command"""
        
        bits_high = mode | (bits & 0xF0) | self._backlight
        bits_low = mode | ((bits << 4) & 0xF0) | self._backlight
        
        # High bits
        self.bus.write_byte(self.i2c_addr, bits_high)
        self._lcd_toggle_enable(bits_high)
        
        # Low bits
        self.bus.write_byte(self.i2c_addr, bits_low)
        self._lcd_toggle_enable(bits_low)

    def _lcd_toggle_enable(self, bits):
        """Toggle enable"""
        time.sleep(E_DELAY)
        self.bus.write_byte(self.i2c_addr, (bits | ENABLE))
        time.sleep(E_PULSE)
        self.bus.write_byte(self.i2c_addr, (bits & ~ENABLE))
        time.sleep(E_DELAY)

    def clear(self):
        """Clear the display"""
        self._lcd_byte(0x01, LCD_CMD)
        time.sleep(E_DELAY)

    def write_line(self, row, text):
        """Write string to a specific line/row (0-indexed)"""
        if row >= self.rows:
            return
            
        # Pad with spaces to clear any old characters
        text = text.ljust(self.cols, " ")
        
        self._lcd_byte(self.row_offsets[row], LCD_CMD)
        
        for i in range(self.cols):
            # Write characters (up to the maximum width)
            if i < len(text):
                self._lcd_byte(ord(text[i]), LCD_CHR)

    def write_lines(self, lines):
        """Write multiple lines to the LCD"""
        for row, text in enumerate(lines):
            self.write_line(row, text)
            
    def set_backlight(self, on: bool):
        """Turn backlight on or off"""
        self._backlight = 0x08 if on else 0x00
        self.bus.write_byte(self.i2c_addr, self._backlight)
