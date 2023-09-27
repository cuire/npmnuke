import argparse
import logging
import sys
from pathlib import Path

import click

from npmnuke.cli import non_interactive_dialog
from npmnuke.logger import log
from npmnuke.models import DialogSettings


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
        default=False,
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
