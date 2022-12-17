from extract import do_extract as _do_extract
from settings import Settings as _Settings


def extract(in_path: str, out_dir: str,
            trimming: bool = True, blackening: bool = True, subtextures: bool = False):
    settings = _Settings(in_path, out_dir, trimming, blackening, subtextures)
    _do_extract(settings)
