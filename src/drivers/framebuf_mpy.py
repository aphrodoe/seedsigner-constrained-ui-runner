class MicroPythonFramebufRenderer:
    """
    A lightweight text renderer for pixel displays (OLED, E-Paper)
    using MicroPython's built-in framebuf module instead of Pillow.
    """
    def __init__(self, display, width=128, height=64, char_width=8, char_height=8):
        self.display = display  # Must implement .text(), .fill(), and .show()
        self.width = width
        self.height = height
        self.char_width = char_width
        self.char_height = char_height
        
        self.cols = self.width // self.char_width
        self.rows = self.height // self.char_height
        
        self.ascii_fallback = {
            "✓": "Y", "⚠": "!", "‼": "!!", "✕": "x", "✗": "x",
            "●": "*", "·": ".", "•": ".", "✎": "E", "✍": "E", "🖉": "E",
            "▦": "#", "⚿": "K", "⚒": "T", "⚙": "S", "⌨": "K",
            "⎇": "*", "₿": "B", "ℹ": "i", "@": "@", "…": "...",
            "←": "<", "→": ">", "↑": "^", "↓": "v", "■": "X", "□": "O"
        }

    def _sanitize(self, text):
        res = ""
        for c in text:
            if c in self.ascii_fallback:
                res += self.ascii_fallback[c]
            elif ord(c) < 128:
                res += c
            else:
                res += "?"
        return res

    def write_lines(self, lines):
        """Write multiple lines of text to the frame buffer and flush to screen."""
        self.display.fill(0) # Clear to black
        
        for i, line in enumerate(lines):
            if i >= self.rows:
                break
                
            clean_line = self._sanitize(line)
            # MicroPython built-in font is 8x8.
            # text(string, x, y, color)
            self.display.text(clean_line, 0, i * self.char_height, 1)
            
        self.display.show()
        
    def clear(self):
        self.display.fill(0)
        self.display.show()
