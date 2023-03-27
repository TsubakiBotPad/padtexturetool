import logging
import os
import re
import zipfile
from pathlib import Path

from .encoding import *
from .texture_reader import extract_textures_from_binary_blob
from .texture_writer import export_to_image_file

MONSTER_NAME_REGEX = re.compile(r'^(MONS_)(\d+)(\..+)$', flags=re.IGNORECASE)


def get_output_file_name(suggested_file_name, files_written):
    output_file_name = suggested_file_name
    # If the file is a "monster file" then pad the ID out with extra zeroes.
    match = MONSTER_NAME_REGEX.match(suggested_file_name)
    if match:
        prefix, mid, suffix = match.groups()
        output_file_name = prefix + mid.zfill(5) + suffix

    # If we've already written a file with this name then add a number to the
    # file name to prevent collisions.
    if output_file_name in files_written:
        files_written[output_file_name] += 1
        output_file_without_extension, output_file_extension = os.path.splitext(output_file_name)
        output_file_name = "{} ({}){}".format(output_file_without_extension,
                                              files_written[output_file_name],
                                              output_file_extension)
    else:
        files_written[output_file_name] = 0

    return output_file_name


def do_extract(settings):
    for input_file_path in settings.input_files:
        output_directory_path = (settings.output_directory or os.path.dirname(input_file_path))

        if zipfile.is_zipfile(input_file_path):
            with zipfile.ZipFile(input_file_path, 'r') as apk_file:
                file_contents = apk_file.read('assets/DATA001.BIN')

        else:
            with open(input_file_path, 'rb') as binary_file:
                file_contents = binary_file.read()

        logging.info("\nReading {}... ".format(input_file_path))
        textures, is_animated = list(extract_textures_from_binary_blob(file_contents))
        logging.info("{} texture{} found.\n".format(str(len(textures)) if any(textures) else "No",
                                                    "" if len(textures) == 1 else "s"))

        if not settings.animations_enabled and is_animated:
            logging.warning("Skipping; animations not enabled")
            # input_file_without_extension, _ = os.path.splitext(input_file_path)
            # Create a tag file that marks this as being animated. This is used elsewhere
            # to determine if we need to extract a video.
            # This is currently unused
            # Path(input_file_without_extension + '.isanimated').touch()
            return

        basename = os.path.basename(input_file_path)
        files_written = {}
        for c, texture in enumerate(textures, 1):
            output_file_name = get_output_file_name(texture.name, files_written)
            if is_animated and settings.rename_enabled:
                try:
                    mid = int(re.search(r'\d+', basename).group())
                except AttributeError:
                    raise ValueError(f"Unable to rename non-monster file {basename}.") from None
                output_file_name = f"MONS_{mid:04d}_{c:03d}.PNG"

            logging.info(f"Writing {output_file_name} ({texture.width} x {texture.height})...")
            if texture.encoding in (PVRTC2BPP, PVRTC4BPP):
                logging.warning(
                    f"{output_file_name} is encoded using PVR texture compression."
                    " This format is not yet supported by the Puzzle & Dragons Texture Tool.")
            output_file_path = os.path.join(output_directory_path, output_file_name)
            export_to_image_file(texture, output_file_path, settings)
