# Build the bit-depth conversion table
import io
import itertools
import os
import png

from crc import Calculator, Crc32

from .encoding import *

CRC32 = Calculator(Crc32.CRC32.value)

bit_depth_conversion_table = [[[0 for i in range(256)] for j in range(9)] for k in range(9)]
for current_bit_depth in range(1, 9):
    for new_bit_depth in range(current_bit_depth, 9):
        for value in range(2 ** current_bit_depth):
            bit_depth_conversion_table[current_bit_depth][new_bit_depth][value] = int(
                round(value * (float((2 ** new_bit_depth) - 1) / float((2 ** current_bit_depth) - 1))))

software_text = b'Exported using the Puzzle & Dragons Texture Tool! (https://github.com/TsubakiBotPad/padtexturetool)'


def trim_transparent_edges(flat_pixel_array, width, height, channels, given_width, given_height):
    channels_per_pixel = len(channels)

    # Isolate the image's alpha channel
    alpha_channel = flat_pixel_array[(channels_per_pixel - 1)::channels_per_pixel]

    get_row = (
        lambda row_index, pixel_array, row_stride: pixel_array[row_index * row_stride:(row_index + 1) * row_stride])
    get_column = (lambda column_index, pixel_array, row_stride: pixel_array[column_index::row_stride])
    is_transparent = (lambda row_or_column: sum(row_or_column) == 0)

    def find_trim_edges(min_index, max_index, get_slice):
        while (min_index <= max_index) and is_transparent(get_slice(min_index, alpha_channel, width)):
            min_index += 1
        while (min_index <= max_index) and is_transparent(get_slice(max_index, alpha_channel, width)):
            max_index -= 1
        return min_index, max_index

    top, bottom = find_trim_edges(0, given_height - 1, get_row)
    left, right = find_trim_edges(0, given_width - 1, get_column)

    trimmed_width = (right - left) + 1
    trimmed_height = (bottom - top) + 1

    row_edges = (left, left + trimmed_width)
    row_offsets = (row_index * width for row_index in range(top, top + trimmed_height))
    row_boundaries = (tuple(((edge + offset) * channels_per_pixel)
                            for edge in row_edges) for offset in row_offsets)
    trimmed_rows = (flat_pixel_array[row_start: row_end] for row_start, row_end in row_boundaries)
    trimmed_pixels = list(itertools.chain(*trimmed_rows))

    return trimmed_width, trimmed_height, trimmed_pixels


def blacken_transparent_pixels(flat_pixel_array, width, height, channels):
    channels_per_pixel = len(channels)

    alpha_channel_index = (channels_per_pixel - 1)
    for pixel_index in range(width * height):
        channel_index = pixel_index * channels_per_pixel
        if flat_pixel_array[channel_index + alpha_channel_index] == 0x0:
            for i in range(channel_index, channel_index + channels_per_pixel - 1):
                flat_pixel_array[i] = 0

    return flat_pixel_array


def unpack_pixels(texture, target_bit_depth):
    bits_per_channel = texture.encoding.channels

    bit_shifts = [sum(bits_per_channel[channel_index + 1:])
                  for channel_index, channel_bit_count in enumerate(bits_per_channel)]
    bit_masks = [(((2 ** bit_count) - 1) << bit_shift)
                 for bit_count, bit_shift in zip(bits_per_channel, bit_shifts)]
    conversion_tables = [bit_depth_conversion_table[current_bit_count][target_bit_depth]
                         for current_bit_count in bits_per_channel]

    return [conversion_table[(packed_pixel_value & bit_mask) >> bit_shift]
            for packed_pixel_value in texture.packed_pixels
            for bit_shift, bit_mask, conversion_table in zip(bit_shifts, bit_masks, conversion_tables)]


def export_to_image_file(texture, output_file_path, settings):
    binary_file_data = bytes()
    if texture.encoding is RAW:
        binary_file_data = texture.buffer

    else:
        width, height = texture.width, texture.height
        target_bit_depth = 8
        flat_pixel_array = unpack_pixels(texture, target_bit_depth)

        if texture.encoding.has_alpha:
            if settings.trimming_enabled:
                width, height, flat_pixel_array = trim_transparent_edges(
                    flat_pixel_array, width, height, texture.encoding.channels, texture.given_width,
                    texture.given_height)
            if settings.blackening_enabled:
                flat_pixel_array = blacken_transparent_pixels(
                    flat_pixel_array, width, height, texture.encoding.channels)

        if any(flat_pixel_array):
            # Create an in-memory stream to which we can write the png data.
            png_stream = io.BytesIO()

            # Attempt to create a palette
            channels_per_pixel = len(texture.encoding.channels)
            pixels = list(zip(*(flat_pixel_array[i::channels_per_pixel]
                                for i in range(channels_per_pixel))))
            palette = list(set(pixels))

            # Palettes cannot contain more than 256 colors. Also, using palettes for
            # greyscale images typically takes more memory, not less.
            if len(palette) <= (2 ** 8) and not texture.encoding.is_greyscale:
                def get_alpha_value(color):
                    return color[channels_per_pixel - 1]

                palette.sort(key=get_alpha_value)
                color_to_index = dict((color, palette_index)
                                      for palette_index, color in enumerate(palette))
                palette_index_array = [color_to_index[color] for color in pixels]

                # Remove alpha from opaque pixels
                if texture.encoding.has_alpha:
                    palette = [(color if get_alpha_value(color) < 0xFF else color[:-1])
                               for color in palette]
                elif texture.encoding.is_greyscale:
                    palette = [(color[0],) * 3 for color in palette]

                # Write the png data to the stream.
                png_writer = png.Writer(width, height, palette=palette, bitdepth=target_bit_depth)
                png_writer.write_array(png_stream, palette_index_array)

            else:
                # Write the png data to the stream.
                png_writer = png.Writer(width, height, alpha=texture.encoding.has_alpha,
                                        greyscale=texture.encoding.is_greyscale,
                                        bitdepth=target_bit_depth, planes=len(texture.encoding.channels))
                png_writer.write_array(png_stream, flat_pixel_array)

            # Add the penultimate chunk.
            final_chunk_size = 12
            png_file_byte_array = bytearray(png_stream.getvalue())
            # Turn the text into a PNG tEXt chunk (size + data + checksum)
            data = b'tEXtSoftware\0' + software_text
            penultimate_chunk = (len(data)-4).to_bytes(4, 'big') + data + CRC32.checksum(data).to_bytes(4, 'big')
            binary_file_data = bytes(
                png_file_byte_array[:-final_chunk_size]) + penultimate_chunk + bytes(
                png_file_byte_array[-final_chunk_size:])

    if any(binary_file_data):
        output_directory = os.path.dirname(output_file_path)
        if not os.path.isdir(output_directory):
            os.makedirs(output_directory)
        with open(output_file_path, 'wb') as output_file_handle:
            output_file_handle.write(binary_file_data)
