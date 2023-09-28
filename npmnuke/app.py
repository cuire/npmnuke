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
from npmnuke.models import NodeFolder
from npmnuke.widgets import NodeResultsList, Timer


class NPMNuke(App):
    """Textual code browser app."""

    # CSS_PATH = "code_browser.tcss"
    BINDINGS = [
        ("q", "quit", "Quit"),
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
    """

    def __init__(self, path: Path, **kwargs):
        super().__init__(**kwargs)
        self._result_queue: asyncio.Queue[Path] = asyncio.Queue()
        self._result_size_queue: asyncio.Queue[tuple[Path, float]] = asyncio.Queue()

        self._calculate_size_queue: asyncio.Queue[Path] = asyncio.Queue()

        self.path = path

    async def on_mount(self) -> None:
        await self._start_tasks()

    async def _start_tasks(self) -> None:
        log.debug("START ALL TASKS")

        self.run_worker(self._load_node_modules(), thread=True, exclusive=True)
        self.run_worker(self._node_results.start_consumer(self._result_queue))
        self.run_worker(self._node_results.start_size_consumer(self._result_size_queue))

        log.debug("TASKS CREATED")

    async def _load_node_modules(self) -> None:
        log.debug("Loading node_modules")

        self._timer.start()

        for path in find_node_modules_dirs(self.path):
            await self._result_queue.put(path)
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

    def compose(self) -> ComposeResult:
        """Compose our UI."""
        log.debug("COMPOSE UI")
        self._node_results = NodeResultsList()
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
