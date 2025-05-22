from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import DataTable, Footer, Header

from docker_volume_analyzer.volume_manager import VolumeManager


class DockerTUI(App):
    """
    DockerTUI is a Textual UI application for managing Docker volumes.
    It provides a graphical interface to view and interact with Docker volumes.
    """

    BINDINGS = [("t", "toggle_dark", "Toggle dark mode")]
    CSS_PATH = "tui.tcss"

    def __init__(self):
        super().__init__()
        self.title = "Docker Volume Analyzer"
        self.manager = VolumeManager()
        self.volumes = None

    def compose(self) -> ComposeResult:
        """Genearate the UI components for the app.

        Returns:
            ComposeResult: Components to be displayed in the app.

        Yields:
            Iterator[ComposeResult]: Components to be displayed in the app.
        """
        yield Header()
        with Horizontal(id="top"):
            yield DataTable(cursor_type="row", id="volumes_table")

        yield Footer()

    def on_mount(self) -> None:
        """Load the data into the table and tree when the app is mounted.

        Returns:
            None: No return value.
        """
        table = self.query_one(DataTable)
        table.add_columns("Name", "Size", "Containers", "Created at")

        self.volumes = self.manager.get_volumes()
        for volume in self.volumes.values():
            table.add_row(
                volume.get("name"),
                volume.get("size"),
                len(volume.get("containers", [])),
                volume.get("created_at"),
            )

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode.

        Returns:
            None: No return value.
        """
        self.theme = (
            "textual-dark"
            if self.theme == "textual-light"
            else "textual-light"
        )


if __name__ == "__main__":  # pragma: no cover
    DockerTUI().run()
