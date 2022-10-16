from extract import do_extract
from settings import Settings


def extract(in_path: str, out_dir: str,
            trimming: bool = True, blackening: bool = True, subtextures: bool = False):
    settings = Settings(in_path, out_dir, trimming, blackening, subtextures)
    do_extract(settings)
