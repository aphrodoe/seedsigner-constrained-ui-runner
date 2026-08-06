import time
import machine

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
E_PULSE = 0.00005
E_DELAY = 0.00005

class LCDI2CMPY:
    def __init__(self, i2c, i2c_addr=0x27, rows=2, cols=16):
        self.i2c_addr = i2c_addr
        self.i2c = i2c
        self.rows = rows
        self.cols = cols
        self._backlight = LCD_BACKLIGHT
        
        self.row_offsets = [LCD_LINE_1, LCD_LINE_2, LCD_LINE_3, LCD_LINE_4]
        
        self.all_bitmaps = {
            "✓": [0b00000, 0b00001, 0b00011, 0b10110, 0b11100, 0b01000, 0b00000, 0b00000], # Success
            "⚠": [0b00100, 0b01010, 0b10101, 0b10001, 0b10101, 0b11111, 0b00000, 0b00000], # Warning Triangle
            "‼": [0b01010, 0b01010, 0b01010, 0b01010, 0b00000, 0b01010, 0b01010, 0b00000], # Dire Warning
            "✕": [0b00000, 0b10001, 0b01010, 0b00100, 0b01010, 0b10001, 0b00000, 0b00000], # Cross
            "✗": [0b00000, 0b10001, 0b01010, 0b00100, 0b01010, 0b10001, 0b00000, 0b00000], # Cross alt
            "●": [0b00000, 0b00000, 0b00100, 0b01110, 0b01110, 0b01110, 0b00100, 0b00000], # Bullet
            "·": [0b00000, 0b00000, 0b00100, 0b01110, 0b01110, 0b01110, 0b00100, 0b00000], # Bullet alt
            "•": [0b00000, 0b00000, 0b00100, 0b01110, 0b01110, 0b01110, 0b00100, 0b00000], # Bullet alt
            "✎": [0b00011, 0b00101, 0b00110, 0b01100, 0b11000, 0b10000, 0b00000, 0b00000], # Pen
            "✍": [0b00011, 0b00101, 0b00110, 0b01100, 0b11000, 0b10000, 0b00000, 0b00000], # Pen alt
            "🖉": [0b00011, 0b00101, 0b00110, 0b01100, 0b11000, 0b10000, 0b00000, 0b00000], # Pen alt
            "▦": [0b11011, 0b10101, 0b11011, 0b00000, 0b10010, 0b01001, 0b11011, 0b00000], # QR Code
            "⚿": [0b01110, 0b10001, 0b01110, 0b00100, 0b00111, 0b00100, 0b00111, 0b00000], # Key
            "⚒": [0b01100, 0b10010, 0b01100, 0b00100, 0b00010, 0b00001, 0b00000, 0b00000], # Wrench
            "⚙": [0b01010, 0b01110, 0b11011, 0b01110, 0b01010, 0b00000, 0b00000, 0b00000], # Gear
            "⌨": [0b00000, 0b00000, 0b11111, 0b10101, 0b11111, 0b01110, 0b00000, 0b00000], # Keyboard
        }
        self.cgram_map = {}
        
        self.emergency_fallback = {
            "✓": "Y", "⚠": "!", "‼": "!!", "✕": "x", "✗": "x",
            "●": "*", "·": ".", "•": ".", "✎": "E", "✍": "E", "🖉": "E",
            "▦": "#", "⚿": "K", "⚒": "T", "⚙": "S", "⌨": "K"
        }
        self.ascii_fallback = {
            "⎇": "*",      # Derivation
            "₿": "B",      # Bitcoin
            "ℹ": "i",      # Info
            "@": "@",      # Fingerprint
            "…": "...",    # Ellipsis
        }
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

    def load_custom_character(self, location, charmap):
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
        self.i2c.writeto(self.i2c_addr, bytes([bits_high]))
        self._lcd_toggle_enable(bits_high)
        
        # Low bits
        self.i2c.writeto(self.i2c_addr, bytes([bits_low]))
        self._lcd_toggle_enable(bits_low)

    def _lcd_toggle_enable(self, bits):
        """Toggle enable"""
        time.sleep(E_DELAY)
        self.i2c.writeto(self.i2c_addr, bytes([bits | ENABLE]))
        time.sleep(E_PULSE)
        self.i2c.writeto(self.i2c_addr, bytes([bits & ~ENABLE]))
        time.sleep(E_DELAY)

    def clear(self):
        """Clear the display"""
        self._lcd_byte(0x01, LCD_CMD)
        time.sleep(E_DELAY)

    def write_line(self, row, text):
        """Write string to a specific line/row (0-indexed)"""
        if row >= self.rows:
            return
            
        translated_text = ""
        for char in text:
            if char in self.cgram_map:
                translated_text += chr(self.cgram_map[char])
            elif char in self.all_bitmaps:
                # Known bitmap but no CGRAM slot allocated (exceeded 8 slots)
                translated_text += self.emergency_fallback.get(char, "?")
            elif char in self.ascii_fallback:
                translated_text += self.ascii_fallback[char]
            elif ord(char) < 128:
                translated_text += char
            else:
                translated_text += "?"
                
        # Pad with spaces to clear any old characters
        translated_text = translated_text + " " * max(0, self.cols - len(translated_text))
        # Ensure we don't overflow the physical columns
        translated_text = translated_text[:self.cols]
        
        self._lcd_byte(self.row_offsets[row], LCD_CMD)
        
        for char in translated_text:
            self._lcd_byte(ord(char), LCD_CMD if char == "" else LCD_CHR)

    def write_lines(self, lines):
        """Write multiple lines to the LCD, dynamically allocating CGRAM slots."""
        # 1. Figure out which unique custom characters are needed for this frame
        needed_chars = set()
        for text in lines:
            for char in text:
                if char in self.all_bitmaps:
                    needed_chars.add(char)
        
        # 2. Re-allocate CGRAM slots if the required characters have changed
        new_cgram_map = {}
        slot = 0
        for char in needed_chars:
            if slot < 8:
                new_cgram_map[char] = slot
                # Only upload to hardware if it wasn't already in this exact slot
                if self.cgram_map.get(char) != slot:
                    self.load_custom_character(slot, self.all_bitmaps[char])
                slot += 1
                
        self.cgram_map = new_cgram_map

        # 3. Write lines to the display
        for row, text in enumerate(lines):
            self.write_line(row, text)
            
    def set_backlight(self, on):
        """Toggle backlight on/off"""
        if on:
            self._backlight = LCD_BACKLIGHT
        else:
            self._backlight = LCD_NOBACKLIGHT
        # Send a dummy command to update the backlight bit
        self._lcd_byte(0x00, LCD_CMD)
