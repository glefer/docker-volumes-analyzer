from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import DataTable, Footer, Header

from docker_volume_analyzer.volume_manager import VolumeManager
from docker_volume_analyzer.widgets.virtual_tree import VirtualDirectoryTree


class DockerTUI(App):
    """
    DockerTUI is a Textual UI application for managing Docker volumes.
    It provides a graphical interface to view and interact with Docker volumes.
    """

    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]
    CSS_PATH = "layout.tcss"

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
            yield VirtualDirectoryTree({}, self.manager, "Virtual Root")

        yield Footer()

    def on_mount(self) -> None:
        """Load the data into the table and tree when the app is mounted.

        Returns:
            None: No return value.
        """
        table = self.query_one(DataTable)
        table.add_columns("Nom", "Taille")

        self.volumes = self.manager.get_volumes()
        for volume_name in self.volumes.keys():
            size = "???"  # Docker ne donne pas la taille directement
            table.add_row(volume_name, size)

        table.on_event("row_")

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

    def on_data_table_row_highlighted(
        self, event: DataTable.RowHighlighted
    ) -> None:
        """Update the DirectoryTree path when a row is highlighted in
           the DataTable. This method is triggered when a row in
           the DataTable is highlighted.

        Args:
            event (DataTable.RowHighlighted): The event containing the row key
            of the highlighted row.
        """
        table = self.query_one(DataTable)
        row_key = event.row_key
        row_data = table.get_row(row_key)
        tree = self.query_one(VirtualDirectoryTree)
        tree.update_virtual_tree(
            self.manager.get_volume_files(row_data[0]), row_data[0]
        )


if __name__ == "__main__":
    DockerTUI().run()
