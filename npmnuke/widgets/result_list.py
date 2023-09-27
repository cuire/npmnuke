import asyncio
import typing
from pathlib import Path

from textual.widgets import Label, ListItem, ListView

from npmnuke.logger import log
from npmnuke.models import NodeFolder


class NodeResultListItem(ListItem):
    path: Path

    def __init__(self, node_folder: NodeFolder) -> None:
        self.path = node_folder

        super().__init__(
            Label(str(node_folder.path)),
            Label(node_folder.size or "-"),
        )


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

    async def _append(self, node_result: Path) -> None:
        node_folder = NodeFolder(path=node_result)
        list_item = NodeResultListItem(node_folder)

        async with self.lock:
            self.node_results[node_result] = node_folder
            self.append(list_item)

    def on_node_result_list_item_click(self, item: NodeResultListItem) -> None:
        log.debug(f"Clicked {item.path}")
