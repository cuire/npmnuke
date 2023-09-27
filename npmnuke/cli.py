from pathlib import Path

import click
from halo import Halo

from npmnuke import __version__
from npmnuke.files import (
    NODE_MODULES,
    calculate_size,
    find_node_modules_dirs,
    remove_node_modules,
)
from npmnuke.logger import log
from npmnuke.models import DialogSettings


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
