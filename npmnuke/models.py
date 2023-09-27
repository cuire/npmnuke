import typing
from dataclasses import dataclass
from pathlib import Path

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
