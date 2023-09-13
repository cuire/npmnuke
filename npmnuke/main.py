import argparse
import logging
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

import click
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

    dialog_settings = DialogSettings(
        verbose=args.verbose,
        skip_calculating_size=args.skip_calculating_size,
    )

    if args.non_interactive:
        non_interactive_dialog(dialog_settings)
    else:
        interactive_dialog(target_dir)


@dataclass
class DialogSettings:
    """
    Settings for the interactive dialog.
    """

    verbose: bool = False
    skip_calculating_size: bool = False


def interactive_dialog(options: DialogSettings) -> None:
    raise NotImplementedError()


def non_interactive_dialog(options: DialogSettings) -> None:
    print(f"> npmnuke 💥 {__version__}")

    print(f"Scanning '{options.target_dir}' for '{NODE_MODULES}' folders")

    with Halo(text="Loading", spinner="dots", enabled=not options.verbose):
        node_modules_dirs = find_node_modules_dirs(options.target_dir)

    print(f"Found {len(node_modules_dirs)} '{NODE_MODULES}' folders")

    if not node_modules_dirs:
        return

    calculated_size = None
    if not options.skip_calculating_size:
        with click.progressbar(
            node_modules_dirs, label="Calculating size"
        ) as dirs_queue:
            calculated_size = [calculate_size(dir) for dir in dirs_queue]

    total_cleaned_mb = start_remove_dialog(node_modules_dirs, calculated_size)

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


def start_remove_dialog(
    node_modules_dirs: list[Path],
    calculated_size: list[float] | None = None,
) -> float:
    """
    Start the dialog with the user. Ask the user which node_modules
    folders to delete and delete them.
    Return the total amount of MB deleted.
    """
    print("Which node_modules folders do you want to delete?")
    print("Enter a comma separated list of numbers to delete them.")
    print("Enter 'all' to delete all folders.")

    for i, dir in enumerate(node_modules_dirs):
        size_str = f"{calculated_size[i]} MB" if calculated_size else ""
        print(f"{i + 1}: {dir} {size_str}")

    print("")

    while True:
        user_input = input("> ")

        if user_input == "all":
            break

        try:
            indexes = [int(i) - 1 for i in user_input.split(",")]
        except ValueError:
            print("Invalid input")
            continue

        if not all([0 <= i < len(node_modules_dirs) for i in indexes]):
            print("Invalid input")
            continue

        break

    if user_input == "all":
        indexes = range(len(node_modules_dirs))

    total_cleaned_mb = 0


def calculate_size(dir: Path) -> float:
    """
    Calculate the size of the given directory in MB.
    """
    return 0.0


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
    parser.add_argument(
        "--skip-calculating-size",
        action="store_true",
        help="skip calculating the size of the node_modules folders",
        default=False,
    )

    return parser.parse_args()


if __name__ == "__main__":
    main()
