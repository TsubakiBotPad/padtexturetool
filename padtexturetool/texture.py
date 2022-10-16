import struct


class Texture:
    """An instance of a texture."""

    def __init__(self, width, height, name, buffer, encoding, given_width=0, given_height=0):
        super(Texture, self).__init__()
        self.width = width
        self.height = height
        self.name = name
        self.buffer = buffer
        self.encoding = encoding
        self.packed_pixels = None
        self.given_width = given_width or self.width
        self.given_height = given_height or self.height

        if self.encoding.stride_in_bits:
            if self.encoding.stride_in_bits == 32:
                self.packed_pixels = struct.unpack(">{}L".format(self.width * self.height), self.buffer)
            elif self.encoding.stride_in_bits == 16:
                self.packed_pixels = struct.unpack("<{}H".format(self.width * self.height), self.buffer)
            elif self.encoding.stride_in_bits == 8:
                self.packed_pixels = struct.unpack("<{}B".format(self.width * self.height), self.buffer)
            elif self.encoding.stride_in_bits < 8:
                intermediate_packed_pixels = struct.unpack("<{}B".format(
                    (self.width * self.height * self.encoding.stride_in_bits) // 8), self.buffer)
                self.packed_pixels = []
                bit_mask = ((2 ** self.encoding.stride_in_bits) - 1)
                pixels_per_byte = (8 // self.encoding.stride_in_bits)
                for byte in intermediate_packed_pixels:
                    for i in range(pixels_per_byte):
                        self.packed_pixels.append(
                            (byte >> (self.encoding.stride_in_bits * (pixels_per_byte - i - 1))) & bit_mask)
