from enum import Enum
import sys
import tty
import termios

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

    def read_event(self) -> InputEvent:
        """Blocks until a mapped key is pressed, then returns the InputEvent."""
        while True:
            ch = sys.stdin.read(1)
            
            # Arrow keys are escape sequences: \x1b[A etc.
            if ch == '\x1b':
                # We use a non-blocking read for the rest of the sequence
                # to differentiate between ESC key and Arrow keys.
                # In raw mode, sys.stdin.read(1) blocks.
                ch2 = sys.stdin.read(1)
                if ch2 == '[':
                    ch3 = sys.stdin.read(1)
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
