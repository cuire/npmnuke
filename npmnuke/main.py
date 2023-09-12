import argparse
import logging
import shutil
import sys
from pathlib import Path

from halo import Halo

__version__ = "0.1.0"

NODE_MODULES = "node_modules"

log = logging.getLogger(__name__)


LOGO = r"""
     .-') _   _ (`-.  _   .-')         .-') _             .-. .-')     ('-.   
    (    ) ) ( (    )( '.(    )_      (    ) )            \  (    )  _(    )  
,--./ ,--,' _.`     \ ,--.   ,--.),--./ ,--,' ,--. ,--.   ,--. ,--. (,------. 
|   \ |  |\(__...--'' |   `.'   | |   \ |  |\ |  | |  |   |  .'   /  |  .---' 
|    \|  | )|  /  | | |         | |    \|  | )|  | | .-') |      /,  |  |     
|  .     |/ |  |_.' | |  |\./|  | |  .     |/ |  |_|(    )|     ' _)(|  '--.  
|  |\    |  |  .___.' |  |   |  | |  |\    |  |  | | `   /|  .   \   |  .--'  
|  | \   |  |  |      |  |   |  | |  | \   | ('  '-'(_.-' |  |\   \  |  `---. 
`--'  `--'  `--'      `--'   `--' `--'  `--'   `-----'    `--' '--'  `------' 
"""


def main() -> None:
    args = get_args()

    target_dir = Path(args.directory)

    if not target_dir.exists() or not target_dir.is_dir():
        log.error(f"Directory {target_dir} does not exist")
        sys.exit(1)

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    if args.non_interactive:
        non_interactive_dialog(target_dir, verbose=args.verbose)
    else:
        interactive_dialog(target_dir)


def interactive_dialog(target_dir: Path) -> None:
    raise NotImplementedError()


def non_interactive_dialog(target_dir: Path, verbose=False) -> None:
    print(f"> npmnuke 💥 {__version__}")

    print(f"Scanning '{target_dir}' for '{NODE_MODULES}' folders")

    with Halo(text="Loading", spinner="dots", enabled=not verbose):
        node_modules_dirs = find_node_modules_dirs(target_dir)

    print(f"Found {len(node_modules_dirs)} '{NODE_MODULES}' folders")

    total_cleaned_mb = start_remove_dialog(node_modules_dirs)

    print(f"Cleaned {total_cleaned_mb} MB")


def _find_node_modules_dirs(target_dir: Path) -> list[Path]:
    if not target_dir.exists() or not target_dir.is_dir():
        raise ValueError(f"Directory {target_dir} does not exist")

    dirs = []

    log.debug(f"Scanning {target_dir}...")

    for dir in target_dir.iterdir():
        if not dir.is_dir():
            continue

        if dir.name == NODE_MODULES:
            dirs.append(dir.parent)
        else:
            dirs.extend(find_node_modules_dirs(dir))

    return dirs


def find_node_modules_dirs(target_dir: Path, raises=False) -> list[Path]:
    """
    Find all folders that contain a node_modules folder.
    Not search for nested node_modules folders.
    """
    try:
        return _find_node_modules_dirs(target_dir)
    except OSError as e:
        if raises:
            log.error(e)
            raise e
        else:
            log.warning(e)

    return []


def start_remove_dialog(node_modules_dirs: list[Path]) -> float:
    """
    Start the dialog with the user. Ask the user which node_modules
    folders to delete and delete them.
    Return the total amount of MB deleted.
    """
    raise NotImplementedError()


def remove_node_modules(dir: Path) -> None:
    """
    Remove the node_modules folder from the given directory.
    """
    node_modules_dir = dir / NODE_MODULES

    if not node_modules_dir.exists():
        raise ValueError(f"Directory {dir} does not contain a {NODE_MODULES} folder")

    shutil.rmtree(node_modules_dir)


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "directory",
        type=str,
        help="directory to scan",
        default=".",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="do not start the interactive dialog (simplified command line interface)",
        default=True,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="show verbose output",
        default=False,
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
