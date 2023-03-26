import argparse
import os


class Settings:
    """A group of user-configurable settings which control how the script operates."""

    def __init__(self, input_path=None, output_dir=None, trimming=True, blackening=True, animations=False):
        self._input_files = []
        self._output_directory = None

        self.set_input_path(input_path)
        self.set_output_directory(output_dir)
        self._trimming_enabled = trimming
        self._blackening_enabled = blackening
        self._animations_enabled = animations
        self._rename_enabled = animations

    @property
    def input_files(self):
        return self._input_files

    def set_input_path(self, value):
        if value:
            value = os.path.abspath(value)
            if not os.path.exists(value):
                raise argparse.ArgumentTypeError(
                    "The input path you specified (\"{}\") does not exist.".format(value))
            elif os.path.isfile(value):
                self._input_files = [value]
            elif os.path.isdir(value):
                self._input_files = [os.path.join(root, file)
                                     for root, dirs, files in os.walk(value) for file in files]

    @property
    def output_directory(self):
        return self._output_directory

    def set_output_directory(self, value):
        if value is not None:
            self._output_directory = os.path.abspath(value)

    @property
    def trimming_enabled(self):
        return self._trimming_enabled

    def set_trimming_enabled(self, value):
        self._trimming_enabled = value

    @property
    def blackening_enabled(self):
        return self._blackening_enabled

    def set_blackening_enabled(self, value):
        self._blackening_enabled = value

    @property
    def animations_enabled(self):
        return self._animations_enabled

    def set_animations_enabled(self, value):
        self._animations_enabled = value

    @property
    def rename_enabled(self):
        return self._rename_enabled

    def set_rename_enabled(self, value):
        self._rename_enabled = value


def get_settings_from_command_line():
    settings = Settings()

    def call(function, parameter=None):
        class ActionWrapper(argparse.Action):
            def __call__(self, _parser, _namespace, values, _option_string=None):
                function(parameter or values)

        return ActionWrapper

    parser = argparse.ArgumentParser(
        description="This script extracts texture images from the binary data of the popular i_oS & Android game \"Puzzle & Dragons\".",
        add_help=False)
    input_group = parser.add_argument_group("Input")
    group = input_group.add_mutually_exclusive_group(required=True)
    group.add_argument("input_path", metavar="IN_FILE", nargs="?",
                       help="A path to a file containing Puzzle & Dragons texture data. Typically, these files end in \".bc\" however this script is also capable of extracting textures from a Puzzle & Dragons \".apk\" file.",
                       action=call(settings.set_input_path))
    group.add_argument("input_folder", metavar="IN_DIR", nargs="?",
                       help="A path to a folder containing one or more Puzzle & Dragons texture files. Each file in this folder and its sub-folders will be processed and have their textures extracted.",
                       action=call(settings.set_input_path))

    output_group = parser.add_argument_group("Output")
    output_group.add_argument("-o", "--outdir", metavar="OUT_DIR",
                              help="A path to a folder where extracted textures should be saved. This property is optional; by default, any extracted texture files will be saved in the same directory as the file from which they were extracted.",
                              action=call(settings.set_output_directory))

    features_group = parser.add_argument_group("Optional Features")
    features_group.add_argument("-nt", "--notrim", nargs=0,
                                help="Puzzle & Dragons' textures are padded with empty space, which this script automatically removes before writing the texture to disk. Use this flag to disable automatic trimming.",
                                action=call(settings.set_trimming_enabled, False))
    features_group.add_argument("-nb", "--noblacken", nargs=0,
                                help="By default, this script will \"blacken\" (i.e. set the red, green and blue channels to zero) any fully-transparent pixels of an image before exporting it. This reduces file size in a way that does not affect the quality of the image. Use this flag to disable automatic blackening.",
                                action=call(settings.set_blackening_enabled, False))
    features_group.add_argument("--animations", nargs=0, help="Enables extracting monsters with multiple textures",
                                action=call(settings.set_animations_enabled, True))
    features_group.add_argument("--rename", nargs=0, help="Rename animated files to old-style",
                                action=call(settings.set_rename_enabled, True))

    help_group = parser.add_argument_group("Help")
    help_group.add_argument("-h", "--help", action="help",
                            help="Displays this help message and exits.")
    args = parser.parse_args()

    return settings
