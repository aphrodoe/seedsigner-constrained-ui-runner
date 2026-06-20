import threading
from src.drivers.buzzer_pwm import BuzzerPWM
from src.screen_state import ScreenState

class AudioRenderer:
    """A semantic audio renderer that provides acoustic feedback for UI interactions."""
    def __init__(self, pin: int = 18):
        self.buzzer = BuzzerPWM(pin)
        
    def _play_async(self, frequency: float, duration: float):
        threading.Thread(target=self.buzzer.play_tone, args=(frequency, duration), daemon=True).start()
        
    def play_move(self):
        """Short low chirp for D-PAD navigation."""
        self._play_async(440.0, 0.05)  # A4
        
    def play_select(self):
        """Medium chirp for selection (ENTER)."""
        self._play_async(880.0, 0.05)  # A5
        
    def play_success(self):
        """Ascending chord for success status."""
        def sequence():
            self.buzzer.play_tone(523.25, 0.1)  # C5
            self.buzzer.play_tone(659.25, 0.1)  # E5
            self.buzzer.play_tone(783.99, 0.2)  # G5
        threading.Thread(target=sequence, daemon=True).start()
        
    def play_error(self):
        """Low buzz for error/dire_warning."""
        def sequence():
            self.buzzer.play_tone(150.0, 0.1)
            self.buzzer.play_tone(100.0, 0.3)
        threading.Thread(target=sequence, daemon=True).start()
        
    def play_warning(self):
        """Double beep for warning."""
        def sequence():
            self.buzzer.play_tone(440.0, 0.1)
            self.buzzer.play_tone(0.0, 0.05) # pause
            self.buzzer.play_tone(440.0, 0.1)
        threading.Thread(target=sequence, daemon=True).start()

    def render_state(self, state: ScreenState):
        """Plays the appropriate status tone if a new status screen is rendered."""
        # Note: This should only be called when the screen FIRST loads to avoid spamming the audio
        status = state.context.get("status_type", "")
        if status == "success":
            self.play_success()
        elif status == "warning":
            self.play_warning()
        elif status in ["error", "dire_warning"]:
            self.play_error()
