import asyncio
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.reactive import var
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
    """

    loading = var(True)

    def __init__(self, path: Path, **kwargs):
        super().__init__(**kwargs)
        self._result_queue: asyncio.Queue[Path] = asyncio.Queue()
        self._calculate_size_queue: asyncio.Queue[Path] = asyncio.Queue()
        self.path = path

    async def on_mount(self) -> None:
        await self._start_tasks()

    async def _start_tasks(self) -> None:
        log.debug("START ALL TASKS")

        self.run_worker(self._load_node_modules(), thread=True, exclusive=True)
        self.run_worker(self._node_results.start_consumer(self._result_queue))

        log.debug("TASKS CREATED")

    async def _load_node_modules(self) -> None:
        log.debug("Loading node_modules")

        self.loading = True
        self._timer.start()

        for path in find_node_modules_dirs(self.path):
            await self._result_queue.put(path)
            await self._calculate_size_queue.put(path)

        self._timer.stop()
        self._progress_bar.update(total=1, progress=1)
        self.loading = False

        log.debug("Finished loading node_modules")

    def watch_loading(self, loading: bool) -> None:
        log.debug(f"Loading changed: {loading}")
        if not loading:
            self._progress_bar

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
