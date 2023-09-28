import asyncio

from textual.timer import Timer
from textual.widgets import Static

from npmnuke.logger import log


class Spinner(Static):
    states = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    _index = 0
    _delay = 0.1
    _auto_start = True

    def __init__(
        self,
        auto_start: bool = True,
        delay: float = 0.1,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        self._auto_start = auto_start
        self._delay = max(delay, 0)

        self._spin: Timer | None = None

    def on_mount(self) -> None:
        self._spin = self.set_interval(1 / 60, self.spin, pause=not self._auto_start)

    async def spin(self) -> None:
        states = self.states
        self._index += 1

        if self._index >= len(states):
            self._index = 0

        self.update(self.states[self._index])

        await asyncio.sleep(self._delay)

    def start(self) -> None:
        self._spin.resume()

    def stop(self) -> None:
        try:
            self._spin.pause()
        except AttributeError as e:
            # timer not started but already stopped
            ...

        self._index = 0
        self.update("")
