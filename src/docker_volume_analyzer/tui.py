import os

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import DataTable, Footer, Header, Static

from docker_volume_analyzer.volume_manager import VolumeManager


class DockerTUI(App):
    """
    DockerTUI is a Textual UI application for managing Docker volumes.
    It provides a graphical interface to view and interact with Docker volumes.
    """

    BINDINGS = [
        ("t", "toggle_dark", "Toggle dark mode"),
        ("ctrl+q", "quit", "Quit"),
        ("i", "information", "Show information"),
    ]
    CSS_PATH = "tui.tcss"

    def __init__(self):
        super().__init__()
        app_version = os.getenv("APP_VERSION", None)
        self.title = (
            f"Docker Volume Analyzer (v{app_version})"
            if app_version
            else "Docker Volume Analyzer"
        )
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

    def action_information(self):
        """
        An action to show information about the selected volume.
        """
        table = self.query_one(DataTable)
        selected_row = table.cursor_row

        if selected_row is None:
            return
        volume_name = table.get_row_at(selected_row)
        volume_information = self.volumes.get(volume_name[0])
        self.push_screen(VolumeDetailScreen(volume_information))


class VolumeDetailScreen(ModalScreen):
    """
    VolumeDetailScreen is a screen that displays detailed
    information about a Docker volume.
    It is a modal screen that overlays the main application screen.

    Args:
        ModalScreen (ModalScreen): The base class for modal screens.
    """

    BINDINGS = [
        ("b", "back", "Back"),
    ]

    def __init__(self, volume_info: dict):
        super().__init__()
        self.volume_info = volume_info

    def compose(self) -> ComposeResult:
        """
        Generate the UI components for the volume detail screen.

        Returns:
            ComposeResult: Components to be displayed in the app.

        Yields:
            Iterator[ComposeResult]: Components to be displayed in the app.
        """
        self.title = f"Volume Details: {self.volume_info.get('name', 'N/A')}"
        yield Header(
            show_clock=True,
        )
        container_names = [
            rf"- \[id: {container.get('short_id', 'N/A')}] "
            f"{container.get('container_name', 'Unknown')}"
            for container in self.volume_info.get("containers", [])
        ]
        container_list = (
            "\n".join(container_names) if container_names else "- None"
        )

        with Container(id="volume-details", classes="box"):
            with Vertical(id="volume-info", classes="info-panel"):
                yield Static(
                    f"[b]Name[/b]: {self.volume_info.get('name', 'N/A')}"
                )
                yield Static(
                    f"[b]Size[/b]: {self.volume_info.get('size', 'N/A')}"
                )
                yield Static(
                    f"[b]Created[/b]: "
                    f"{self.volume_info.get('created_at', 'N/A')}"
                )
                yield Static(
                    f"[b]Mountpoint[/b]: "
                    f"{self.volume_info.get('mountpoint', 'N/A')}"
                )
                yield Static(f"[b]Containers[/b]:\n{container_list}")

        yield Footer()

    def action_back(self) -> None:
        """An action to go back to the previous screen."""
        self.app.pop_screen()
        self.app.refresh()


if __name__ == "__main__":  # pragma: no cover
    DockerTUI().run()
