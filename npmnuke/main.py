import argparse
import logging
import sys
from pathlib import Path

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

    print(LOGO)

    print(f"Scanning '{target_dir}' for '{NODE_MODULES}' folders")

    node_modules_dirs = find_node_modules_dirs(target_dir)

    print(f"Found {len(node_modules_dirs)} '{NODE_MODULES}' folders")

    total_cleaned_mb = start_remove_dialog(node_modules_dirs)

    print(f"Cleaned {total_cleaned_mb} MB")


def find_node_modules_dirs(target_dir: Path) -> list[Path]:
    """
    Find all folders that contain a node_modules folder.
    Not search for nested node_modules folders.
    """
    raise NotImplementedError()


def start_remove_dialog(node_modules_dirs: list[Path]) -> float:
    """
    Start the dialog with the user. Ask the user which node_modules
    folders to delete and delete them.
    Return the total amount of MB deleted.
    """
    raise NotImplementedError()


def remove_node_modules(dir: Path) -> float:
    """
    Remove the node_modules folder from the given directory.
    Return the amount of MB deleted.
    """
    raise NotImplementedError()


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "directory",
        type=str,
        help="directory to scan",
        default=".",
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()