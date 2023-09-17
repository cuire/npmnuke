import argparse
import logging
import os
import shutil
import sys
import typing
from dataclasses import dataclass
from pathlib import Path

import click
from halo import Halo

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

from npmnuke import __version__

NODE_MODULES = "node_modules"

log = logging.getLogger(__name__)


def main() -> None:
    args = get_args()

    target_dir = Path(args.directory)

    if not target_dir.exists() or not target_dir.is_dir():
        log.error(f"Directory {target_dir} does not exist")
        sys.exit(1)

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    ignore_set = None
    if not args.disable_ignore:
        default_ignore_file = Path.home() / ".npmnukeignore"

        ignore_file = Path(args.ignore_file or default_ignore_file)

        if args.ignore_file and not ignore_file.exists():
            log.error(f"Ignore file {ignore_file} does not exist")
            sys.exit(1)

        if not args.ignore_file and not default_ignore_file.exists():
            log.warning(f"Ignore file {default_ignore_file} does not exist")
            ignore_file = None

        if ignore_file:
            with open(ignore_file, "r") as f:
                ignore_set = set(f.read().splitlines())

            log.debug(f"Using ignore file {ignore_file}")

    if args.ignore_dot:
        log.debug("Ignoring dot folders")

    if args.dry_run:
        log.debug("Dry run enabled")
        click.secho("⚠️ Dry run enabled ⚠️", fg="yellow", bold=True)

    dialog_settings = DialogSettings(
        target_dir=target_dir,
        verbose=args.verbose,
        skip_calculating_size=args.skip_calculating_size,
        ignore_dot=args.ignore_dot,
        ignore_set=ignore_set,
        dry_run=args.dry_run,
    )

    try:
        if args.non_interactive:
            non_interactive_dialog(dialog_settings)
        else:
            interactive_dialog(target_dir)
    except KeyboardInterrupt:
        print("\nExiting...")


IgnoreSet = typing.Set[str]


@dataclass
class DialogSettings:
    """
    Settings for the interactive dialog.
    """

    target_dir: Path
    verbose: bool = False
    skip_calculating_size: bool = False
    ignore_dot: bool = True
    ignore_set: IgnoreSet | None = None
    dry_run: bool = False


def interactive_dialog(options: DialogSettings) -> None:
    raise NotImplementedError()


def non_interactive_dialog(options: DialogSettings) -> None:
    print(f"> npmnuke 💥 {__version__}")

    print(f"Scanning '{options.target_dir}' for '{NODE_MODULES}' folders")

    with Halo(text="Loading", spinner="dots", enabled=not options.verbose):
        node_modules_dirs = list(
            find_node_modules_dirs(
                options.target_dir,
                ignore_dot=options.ignore_dot,
                ignore_set=options.ignore_set,
            )
        )

    print(f"Found {len(node_modules_dirs)} '{NODE_MODULES}' folders")

    if not node_modules_dirs:
        return

    calculated_size = None
    if not options.skip_calculating_size:
        with click.progressbar(
            node_modules_dirs, label="Calculating size"
        ) as dirs_queue:
            calculated_size = [calculate_size(dir / NODE_MODULES) for dir in dirs_queue]

    total_cleaned_mb = start_remove_dialog(
        node_modules_dirs,
        calculated_size,
        options.dry_run,
    )

    click.secho(f"Cleaned {total_cleaned_mb:.2f} MB", fg="green", bold=True)


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


def start_remove_dialog(
    node_modules_dirs: list[Path],
    calculated_size: list[float] | None = None,
    dry_run=False,
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
        size_str = f"{calculated_size[i]:.2f} MB" if calculated_size else ""
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

    with click.progressbar(indexes, label="Removing") as indexes:
        for i in indexes:
            dir = node_modules_dirs[i]
            size = calculated_size[i] if calculated_size else 0.0

            if not dry_run:
                remove_node_modules(dir)

            log.debug(f"Removed {dir} MB")

            total_cleaned_mb += size

    return total_cleaned_mb


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
    parser.add_argument(
        "--ignore-file",
        type=str,
        help="path to the ignore file, by default .npmnukeignore in home directory is used",
        default=None,
    )
    parser.add_argument(
        "--disable-ignore",
        action="store_true",
        help="do not use the .npmnukeignore file when scanning for node_modules folders",
        default=False,
    )
    parser.add_argument(
        "--ignore-dot",
        type=bool,
        help="ignore dot folders (.vscode/ .git/ etc.), by default True",
        default=True,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="do not remove any folders",
        default=False,
    )

    return parser.parse_args()


if __name__ == "__main__":
    main()
