from .extract import do_extract
from .settings import get_settings_from_command_line

do_extract(get_settings_from_command_line())
