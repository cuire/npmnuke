import asyncio
from pathlib import Path

from textual import work
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Footer, Header, ProgressBar

from npmnuke.files import (
    NODE_MODULES,
    calculate_size,
    find_node_modules_dirs,
    remove_node_modules,
)
from npmnuke.logger import log
from npmnuke.models import DialogSettings, NodeFolder
from npmnuke.widgets import NodeResultsList, Timer


class NPMNuke(App):
    """Textual code browser app."""

    # CSS_PATH = "code_browser.tcss"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("space", "remove_selected", "Remove selected"),
    ]

    # add a css to progress
    CSS = """
    .progress-bar-container {
        height: 1;
    }

    .timer {
        margin: 0 0 0 1;
    }
    .result-list-item {
        content-align: right top;
    }
    .result-list-item-label {
        width: 92vw;
    }
    .result-list-item-removed {
        color: red;
    }
    """

    def __init__(self, settings: DialogSettings, **kwargs):
        super().__init__(**kwargs)
        self._result_queue: asyncio.Queue[Path] = asyncio.Queue()
        self._result_size_queue: asyncio.Queue[tuple[Path, float]] = asyncio.Queue()
        self._removed_queue: asyncio.Queue[NodeFolder] = asyncio.Queue()

        self._calculate_size_queue: asyncio.Queue[Path] = asyncio.Queue()

        self._settings = settings

    async def on_mount(self) -> None:
        await self._start_tasks()

    async def _start_tasks(self) -> None:
        log.debug("START ALL TASKS")

        self.run_worker(self._load_node_modules(), thread=True, exclusive=True)
        self.run_worker(self._node_results.start_consumer(self._result_queue))
        if not self._settings.skip_calculating_size:
            self.run_worker(
                self._node_results.start_size_consumer(self._result_size_queue)
            )
        self.run_worker(self._node_results.start_removed_consumer(self._removed_queue))

        log.debug("TASKS CREATED")

    async def _load_node_modules(self) -> None:
        log.debug("Loading node_modules")

        self._timer.start()

        for path in find_node_modules_dirs(
            self._settings.target_dir,
            ignore_dot=self._settings.ignore_dot,
            ignore_set=self._settings.ignore_set,
        ):
            await self._result_queue.put(path)

            if not self._settings.skip_calculating_size:
                self._calculate_size(path)

        self._timer.stop()
        self._progress_bar.update(total=1, progress=1)

        log.debug("Finished loading node_modules")

    @work(thread=True)
    async def _calculate_size(self, path: Path) -> None:
        log.debug(f"Calculating size of {path}")

        size = calculate_size(path)
        await self._result_size_queue.put((path, size))

        log.debug(f"Finished calculating size of {path}")

    async def action_remove_selected(self) -> None:
        log.debug("Removing selected")

        item = self._node_results.highlighted_child

        if item is None:
            return

        node_folder = item.node_folder

        if node_folder.removed or (
            not self._settings.skip_calculating_size and node_folder.size is None
        ):
            self.bell()
            return

        self._remove_node_modules(node_folder)

    @work(group="remove")
    async def _remove_node_modules(self, node_folder: Path) -> None:
        path = node_folder.path

        log.debug(f"Removing {path}")

        if not self._settings.dry_run:
            remove_node_modules(path)

        log.debug(f"Finished removing {path}")

        await self._removed_queue.put(node_folder)

    def compose(self) -> ComposeResult:
        """Compose our UI."""
        log.debug("COMPOSE UI")
        self._node_results = NodeResultsList(
            skip_calculating_size=self._settings.skip_calculating_size
        )
        self._progress_bar = ProgressBar(show_percentage=False, show_eta=False)
        self._timer = Timer(classes="timer")
        yield Header()
        yield Horizontal(
            self._progress_bar,
            self._timer,
            classes="progress-bar-container",
        )
        yield self._node_results
        yield Footer()
