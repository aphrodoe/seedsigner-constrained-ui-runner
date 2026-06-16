from enum import Enum
import sys
import tty
import termios
import select
import os

class InputEvent(Enum):
    UP = "UP"
    DOWN = "DOWN"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    ENTER = "ENTER"
    BACK = "BACK"
    QUIT = "QUIT"

class KeyboardInput:
    def __init__(self):
        self.fd = sys.stdin.fileno()
        self.old_settings = None

    def __enter__(self):
        self.old_settings = termios.tcgetattr(self.fd)
        tty.setcbreak(self.fd)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.old_settings:
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old_settings)

    def read_event(self, timeout: float = None) -> InputEvent:
        """Blocks until a key is pressed or timeout expires. Returns None on timeout."""
        while True:
            if timeout is not None:
                rlist, _, _ = select.select([sys.stdin], [], [], timeout)
                if not rlist:
                    return None
            
            ch = os.read(self.fd, 1).decode('utf-8', errors='ignore')
            
            # Arrow keys are escape sequences: \x1b[A etc.
            if ch == '\x1b':
                # We use a non-blocking read for the rest of the sequence
                # to differentiate between ESC key and Arrow keys.
                rlist, _, _ = select.select([self.fd], [], [], 0.1)
                if not rlist:
                    return InputEvent.BACK
                    
                ch2 = os.read(self.fd, 1).decode('utf-8', errors='ignore')
                if ch2 == '[':
                    rlist, _, _ = select.select([self.fd], [], [], 0.1)
                    if not rlist:
                        return InputEvent.BACK
                        
                    ch3 = os.read(self.fd, 1).decode('utf-8', errors='ignore')
                    if ch3 == 'A':
                        return InputEvent.UP
                    elif ch3 == 'B':
                        return InputEvent.DOWN
                    elif ch3 == 'C':
                        return InputEvent.RIGHT
                    elif ch3 == 'D':
                        return InputEvent.LEFT
                # If just ESC, treat as BACK
                return InputEvent.BACK
            elif ch == '\r' or ch == '\n':
                return InputEvent.ENTER
            elif ch == 'q' or ch == '\x03': # q or Ctrl+C
                return InputEvent.QUIT
