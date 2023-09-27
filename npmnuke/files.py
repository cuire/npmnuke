import os
import shutil
import typing
from pathlib import Path

from npmnuke.logger import log
from npmnuke.models import IgnoreSet

NODE_MODULES = "node_modules"

if "nt" == os.name:
    # https://github.com/python/cpython/issues/67596
    # https://github.com/bleachbit/bleachbit/issues/668
    from ctypes import windll

    def is_junction(path: str) -> bool:
        FILE_ATTRIBUTE_REPARSE_POINT = 0x400
        attr = windll.kernel32.GetFileAttributesW(path)
        return bool(attr & FILE_ATTRIBUTE_REPARSE_POINT)

    path_islink = os.path.islink
    os.path.islink = lambda path: path_islink(path) or is_junction(path)


def _find_node_modules_dirs(
    target_dir: Path, ignore_dot=False, ignore_set: IgnoreSet = None
) -> typing.Iterator[Path]:
    if not target_dir.exists() or not target_dir.is_dir():
        raise ValueError(f"Directory {target_dir} does not exist")

    log.debug(f"Scanning {target_dir}...")

    for dir in target_dir.iterdir():
        if not dir.is_dir():
            continue

        if (ignore_dot and dir.name.startswith(".")) or (
            ignore_set and dir.name in ignore_set
        ):
            log.debug(f"Ignoring {dir}")
            continue

        if dir.name == NODE_MODULES:
            yield dir.parent
        else:
            yield from find_node_modules_dirs(
                dir, ignore_dot=ignore_dot, ignore_set=ignore_set
            )


def find_node_modules_dirs(
    target_dir: Path, raises=False, ignore_dot=True, ignore_set: IgnoreSet = None
) -> typing.Iterator[Path]:
    """
    Find all folders that contain a node_modules folder.
    Not search for nested node_modules folders.
    """
    try:
        yield from _find_node_modules_dirs(
            target_dir, ignore_dot=ignore_dot, ignore_set=ignore_set
        )
    except OSError as e:
        if raises:
            log.error(e)
            raise e
        else:
            log.warning(e)

    return []


def calculate_size(dir: Path, raises=False) -> float:
    """
    Calculate the size of the given directory in MB.
    """
    if not dir.exists() or not dir.is_dir():
        raise FileNotFoundError(f"Directory {dir} does not exist")

    total_size = 0.0

    for root, _, files in os.walk(dir):
        for file in files:
            total_size += os.path.getsize(os.path.join(root, file))

    return total_size / 1024 / 1024


def remove_node_modules(dir: Path) -> None:
    """
    Remove the node_modules folder from the given directory.
    """
    node_modules_dir = dir / NODE_MODULES

    if not node_modules_dir.exists():
        raise ValueError(f"Directory {dir} does not contain a {NODE_MODULES} folder")

    shutil.rmtree(node_modules_dir)
