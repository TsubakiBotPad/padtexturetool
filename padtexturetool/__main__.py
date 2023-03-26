import logging

from .extract import do_extract
from .settings import get_settings_from_command_line

logging.basicConfig(level=logging.INFO)

do_extract(get_settings_from_command_line())
