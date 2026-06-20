import time

try:
    from gpiozero import TonalBuzzer
    from gpiozero.tones import Tone
    GPIOZERO_AVAILABLE = True
except ImportError:
    GPIOZERO_AVAILABLE = False
    TonalBuzzer = None
    Tone = None

class BuzzerPWM:
    def __init__(self, pin: int = 18):
        self.pin = pin
        self.buzzer = None
        
        if not GPIOZERO_AVAILABLE:
            print(f"Warning: gpiozero not installed. Buzzer disabled.")
            return
            
        try:
            self.buzzer = TonalBuzzer(pin, octaves=3)
        except Exception as e:
            print(f"Warning: Failed to initialize buzzer on pin {pin}: {e}")
            
    def play_tone(self, frequency: float, duration: float):
        """Play a specific frequency (Hz) for a duration (seconds). Blocks."""
        if not self.buzzer:
            return
            
        try:
            # gpiozero Tones can be specified by frequency
            self.buzzer.play(Tone(frequency=frequency))
            time.sleep(duration)
            self.buzzer.stop()
        except Exception as e:
            print(f"Buzzer error: {e}")
            if self.buzzer:
                self.buzzer.stop()
