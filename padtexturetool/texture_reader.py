import logging
import re
import struct
import zlib
from typing import List

from .encoding import *
from .texture import Texture

encrypted_texture_magic_string = struct.pack("<5B", 0x49, 0x4F, 0x53, 0x43, 0x68)  # "IOSCh"
encrypted_texture_header_format = "<5sBxxxxxx"
encrypted_texture_header_format_size = struct.calcsize(encrypted_texture_header_format)
unencrypted_texture_magic_string = struct.pack("<3B", 0x54, 0x45, 0x58)  # "TEX"
texture_block_header_format = "<3sxB11x"
texture_block_header_size = struct.calcsize(texture_block_header_format)
texture_block_header_alignment = 16
texture_manifest_format = "<IHH24s"
texture_manifest_size = struct.calcsize(texture_manifest_format)

encodings = {
    # Encoding 0x0 is four bytes per pixel; one byte per red, green, blue and alpha channel.
    0x0: R8G8B8A8,
    # Encoding 0x2 is two bytes per pixel; five bits for the red channel, six
    # bits for the green channel, and five bits for the blue channel.
    0x2: R5G6B5,
    # Encoding 0x3 is two bytes per pixel; four bits per red, green, blue and alpha channel.
    0x3: R4G4B4A4,
    # Encoding 0x4 is two bytes per pixel; five bits per red, green, blue
    # channel, and then one bit for the alpha channel.
    0x4: R5G5B5A1,
    # Encodings 0x8 and 0x9 are one byte per pixel; they are greyscale images.
    0x8: L8,
    0x9: L8,
    # Encoding 0xB uses the PVR texture compression algorithm. In its
    # compressed form, it uses four bits per pixel, but it decompresses to an
    # RGBA image.
    0xB: PVRTC4BPP,
    # Encoding 0xC uses the PVR texture compression algorithm. In its
    # compressed form, it uses two bits per pixel, but it decompresses to an
    # RGBA image.
    0xC: PVRTC2BPP,
    # Encoding 0xD is used for raw file data. Typically this JPEG data, but in
    # theory it could be anything.
    0xD: RAW,
}


def decrypt_and_decompress_binary_blob(binary_blob: bytes) -> bytes:
    magic_string, decryption_key = struct.unpack_from(encrypted_texture_header_format, binary_blob)

    if magic_string != encrypted_texture_magic_string:
        return binary_blob

    # XOR each byte using the decryption key
    binary_blob = bytearray(byte ^ decryption_key
                            for byte in bytearray(binary_blob[encrypted_texture_header_format_size:]))

    # Inflate
    decompress = zlib.decompressobj(-zlib.MAX_WBITS)
    binary_blob = decompress.decompress(bytes(binary_blob))
    binary_blob += decompress.flush()

    return binary_blob


def extract_textures_from_binary_blob(binary_blob: bytes) -> List[Texture]:
    binary_blob = decrypt_and_decompress_binary_blob(binary_blob)

    offset = 0x0
    textures = []
    is_animated = False
    while (offset + texture_block_header_size) < len(binary_blob):
        magic_string, number_of_textures_in_block = struct.unpack_from(texture_block_header_format, binary_blob, offset)
        if magic_string == unencrypted_texture_magic_string:
            texture_block_header_start = offset
            texture_block_header_end = texture_block_header_start + texture_block_header_size

            for texture_manifest_index in range(0, number_of_textures_in_block):
                texture_manifest_start = texture_block_header_end + (texture_manifest_size * texture_manifest_index)
                texture_manifest_end = texture_manifest_start + texture_manifest_size

                starting_offset, width, height, name = struct.unpack(
                    texture_manifest_format, binary_blob[texture_manifest_start:texture_manifest_end])

                encoding_identifier = (width >> 12)
                width = width & 0x0FFF
                height = height & 0x0FFF

                if encoding_identifier in encodings:
                    encoding = encodings[encoding_identifier]
                else:
                    encoding = RAW
                    logging.warning("{name} is encoded with unrecognized encoding \"{encoding}\".".format(
                        name=name, encoding=re.sub(r'^(-?0X)', lambda x: x.group(1).lower(),
                                                   hex(encoding_identifier).upper())))

                byte_count = 0
                if (encoding != RAW):
                    byte_count = (width * height * encoding.stride_in_bits) // 8
                else:
                    name, byte_count = struct.unpack("<20sI", name)

                if byte_count <= 0:
                    logging.warning(f"{name} has no associated image data.")

                name = name.rstrip(b'\0').decode(encoding='UTF-8')

                image_data_start = texture_block_header_start + starting_offset

                # PVR encodings are prefixed by a 52-byte header whose purpose is not yet clear.
                if encoding == PVRTC4BPP or encoding == PVRTC2BPP:
                    image_data_start += 52

                image_data_end = image_data_start + byte_count
                offset = max(offset, image_data_end & ~(texture_block_header_alignment - 1))

                # PVR encodings are followed by a 12-byte footer whose purpose is not yet clear.
                if encoding == PVRTC4BPP or encoding == PVRTC2BPP:
                    offset += 12

                # MONS images mostly have size data in their footer, use this for trimming
                given_width, given_height = 0, 0
                if encoding == R4G4B4A4 and len(binary_blob) >= offset + 16:
                    # 8 bytes of idk perhaps image size | img width | img height | # of frames | idk maybe palette related
                    _, given_width, given_height, _, _ = struct.unpack('<8sHHHH', binary_blob[offset:offset + 16])
                if not given_width or not given_height:
                    # if either dimension is 0, use the full image size instead
                    given_width, given_height = width, height
                textures.append(Texture(width, height, name, binary_blob[image_data_start:image_data_end], encoding,
                                        min(width, given_width), min(height, given_height)))
        elif magic_string == "ISC":
            is_animated = True
        offset += texture_block_header_alignment
    return textures, is_animated
