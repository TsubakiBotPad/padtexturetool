from .extract import do_extract as _do_extract
from .settings import Settings as _Settings


def extract(in_path: str, out_dir: str, *,
            trimming: bool = True, blackening: bool = True, animations: bool = False):
    _do_extract(_Settings(in_path, out_dir, trimming, blackening, animations))
