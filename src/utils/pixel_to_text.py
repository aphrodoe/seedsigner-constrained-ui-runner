class PixelToTextAdapter:
    """Maps pixel display dimensions to (cols, rows) for TextRenderer."""
    
    # Common font sizes for monospace rendering on pixel displays
    FONT_PROFILES = {
        "tiny":   (4, 6),   # 4x6 pixel font
        "small":  (6, 8),   # 6x8 pixel font (default)
        "medium": (8, 12),  # 8x12 pixel font
    }
    
    @classmethod
    def map(cls, pixel_width: int, pixel_height: int, 
            font_profile: str = "small") -> tuple[int, int]:
        """Returns (cols, rows) for a given pixel display and font size."""
        fw, fh = cls.FONT_PROFILES.get(font_profile, cls.FONT_PROFILES["small"])
        cols = pixel_width // fw
        rows = pixel_height // fh
        return (cols, rows)
