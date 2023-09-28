import asyncio
import typing
from pathlib import Path

from textual.containers import Horizontal
from textual.widgets import Label, ListItem, ListView

from npmnuke.logger import log
from npmnuke.models import NodeFolder
from npmnuke.widgets.spinner import Spinner


class NodeResultListItem(ListItem):
    def __init__(self, node_folder: NodeFolder, **kwargs) -> None:
        super().__init__(
            Horizontal(
                Label(
                    str(node_folder.path), id="path", classes="result-list-item-label"
                ),
                Label(id="size"),
                Spinner(id="spinner"),
            ),
            classes="result-list-item",
            **kwargs,
        )

    def update(self, *, path: Path, size: float | None) -> None:
        self.children[0].text = str(path)
        if size is not None:
            self.query_one("#size").update(f"{size:.2f} MB")
            self.query_one("#spinner").stop()


class NodeResultsList(ListView):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.node_results: typing.Dict[Path, NodeFolder] = {}
        self.lock = asyncio.Lock()

    async def start_consumer(self, queue: asyncio.Queue[Path]) -> None:
        while True:
            node_result = await queue.get()

            if node_result is None:
                asyncio.sleep(0.1)

            await self._append(node_result)

    async def start_size_consumer(
        self, queue: asyncio.Queue[tuple[Path, float]]
    ) -> None:
        while True:
            node_result, size = await queue.get()

            if node_result is None:
                asyncio.sleep(0.1)

            log.debug(f"SizeUpdate: {node_result} {size}")

            await self._update_size(node_result, size)

    async def _append(self, node_result: Path) -> None:
        node_folder = NodeFolder(path=node_result)
        id = NodeResultsList.path_to_id(node_result)
        list_item = NodeResultListItem(node_folder, id=id)

        async with self.lock:
            self.node_results[node_result] = node_folder
            self.append(list_item)

    async def _update_size(self, node_result: Path, size: float) -> None:
        async with self.lock:
            if node_result not in self.node_results:
                log.error(f"SizeUpdate: Node result {node_result} not found")
                return

            self.node_results[node_result].size = size

            await self._update_list_item(node_result)

    async def _update_list_item(self, node_result: Path) -> None:
        id = NodeResultsList.path_to_id(node_result)
        list_item = typing.cast(NodeResultListItem, self.query_one(f"#{id}"))

        node_folder = self.node_results[node_result]

        list_item.update(path=node_folder.path, size=node_folder.size)

    def on_node_result_list_item_click(self, item: NodeResultListItem) -> None:
        log.debug(f"Clicked {item.path}")

    @staticmethod
    def path_to_id(path: Path) -> str:
        return str(path).replace("/", "-").replace("\\", "-").replace(".", "-")
