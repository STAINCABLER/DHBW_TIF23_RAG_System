import os

def get_relative_file_path(path: str) -> str:
    script_dir = os.path.dirname(__file__)
    return os.path.join(script_dir, "..", path)
