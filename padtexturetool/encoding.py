class Encoding:
    """A packed pixel encoding."""

    def __init__(self, channels=None):
        super(Encoding, self).__init__()
        self.channels = channels
        if self.channels:
            self.stride_in_bits = sum(self.channels)
            self.has_alpha = (len(self.channels) == 4)
            self.is_greyscale = (len(self.channels) == 1)
        else:
            self.stride_in_bits = None
            self.has_alpha = None
            self.is_greyscale = None


R8G8B8A8 = Encoding([8, 8, 8, 8])
R5G6B5 = Encoding([5, 6, 5])
R4G4B4A4 = Encoding([4, 4, 4, 4])
R5G5B5A1 = Encoding([5, 5, 5, 1])
L8 = Encoding([8])
RAW = Encoding()
PVRTC4BPP = Encoding([4])
PVRTC2BPP = Encoding([2])

__all__ = [
    "R8G8B8A8",
    "R5G6B5",
    "R4G4B4A4",
    "R5G5B5A1",
    "L8",
    "RAW",
    "PVRTC4BPP",
    "PVRTC2BPP",
]
