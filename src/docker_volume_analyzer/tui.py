import os

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.events import Key
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Footer, Header, Static

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
        ("d", "delete_volume", "Delete volume"),
        ("b", "browse", "Browse volume"),
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

    def action_delete_volume(self):
        """
        An action to delete the selected volume.
        """
        table = self.query_one(DataTable)
        selected_row = table.cursor_row

        if selected_row is None:
            return
        volume_row = table.get_row_at(selected_row)
        if volume_row[2] != 0:
            self.push_screen(
                ErrorScreen("Cannot delete volume with attached containers.")
            )
            return

        def delete_callback(confirmed: bool) -> None:
            """
            Callback function to handle the confirmation of volume deletion.

            Args:
                confirmed (bool): True if the user confirmed deletion
                False otherwise.
            """
            if confirmed:
                try:
                    self.manager.delete_volume(volume_row[0])
                    row_key, _ = table.coordinate_to_cell_key(
                        table.cursor_coordinate
                    )
                    table.remove_row(row_key)
                    self.pop_screen()
                    self.refresh()
                except Exception as e:
                    self.pop_screen()
                    self.push_screen(
                        ErrorScreen(f"Error deleting volume: {e}")
                    )
            else:
                self.pop_screen()

        self.push_screen(
            ConfirmationScreen(
                f"Are you sure you want to delete volume '{volume_row[0]}'?",
                delete_callback,
            )
        )

    def action_browse(self):
        """
        An action to browse the contents of the selected volume.
        """

        table = self.query_one(DataTable)
        selected_row = table.cursor_row

        volume_row = table.get_row_at(selected_row)

        self.push_screen(VolumeBrowserScreen(self.app.manager, volume_row[0]))


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


class ErrorScreen(ModalScreen):
    """
    A simple modal screen to display a message.
    """

    def __init__(self, message: str):
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="dialog"):
            yield Static(self.message, classes="message")
        yield Footer()

    BINDINGS = [
        ("b", "back", "Back"),
    ]

    def action_back(self) -> None:
        """Go back to the previous screen."""
        self.app.pop_screen()


class ConfirmationScreen(ModalScreen):
    """
    A simple modal screen to confirm an action.
    """

    def __init__(self, message: str, callback):
        super().__init__()
        self.message = message
        self.callback = callback

    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            yield Static(self.message, classes="question")
            with Horizontal(classes="buttons"):
                yield Button("No", variant="error", id="no_button")
                yield Button("Yes", variant="success", id="yes_button")

    def on_button_pressed(self, event):
        self.callback(event.button.id == "yes_button")


class VolumeBrowserScreen(ModalScreen):
    """
    A modal screen to browse the contents of a Docker volume.
    """

    BINDINGS = [
        ("b", "back", "Back"),
        Binding("enter", "select_cursor", "Select", show=True),
    ]

    ICON_DIRECTORY = "📁 "
    ICON_FILE = "📄 "

    def __init__(self, volume_manager: VolumeManager, volume_name: str):
        super().__init__()
        self.volume_name = volume_name
        self.volume_manager = volume_manager
        self.volume_tree = self.volume_manager.get_volume_tree(volume_name)
        self.current_path = ""

    def compose(self) -> ComposeResult:
        with Container(id="dialog"):

            yield Static(
                f"[b]Browsing volume:[/b] {self.volume_name}",
                classes="title",
            )
            yield Static(
                f"[b]Current path:[/b] {self.current_path}",
                id="current_path",
            )
            yield DataTable(
                id="file_tree",
                cursor_type="row",
                show_cursor=True,
                classes="file-tree",
                zebra_stripes=True,
            )
        with Container(id="shortcuts", classes="shortcuts-container"):
            with Horizontal(classes="shortcuts-list"):
                yield Static("[b]Enter:[/b]", classes="shortcut shortcut-key")
                yield Static(
                    "Open selected directory", classes="shortcut shortcut-desc"
                )
                yield Static(
                    "[b]Backspace:[/b]", classes="shortcut shortcut-key"
                )
                yield Static(
                    "Open parent directory", classes="shortcut shortcut-desc"
                )

    def on_mount(self) -> None:
        """Load the file tree when the screen is mounted."""
        table = self.query_one(DataTable)
        table.add_columns("", "Name", "Size", "Last Modified")
        self.load_data()

    def load_data(self) -> None:

        table = self.query_one(DataTable)
        table.clear()
        directory_informations = self.volume_tree.index.get(
            self.current_path, {}
        )
        if not directory_informations:
            self.query_one(DataTable).add_row(
                "No files found in this directory."
            )
            return ()

        for name, node in directory_informations.childrens.items():
            table.add_row(
                (
                    f"{self.ICON_DIRECTORY}"
                    if node.is_directory
                    else f"{self.ICON_FILE}"
                ),
                name,
                f"{node.size} bytes",
                node.mtime.strftime("%Y-%m-%d %H:%M:%S"),
            )

        self.query_one("#current_path").update(
            f"[b]Current path:[/b] {self.current_path}/"
        )

    def action_back(self) -> None:
        """An action to go back to the previous screen."""
        self.app.pop_screen()
        self.app.refresh()

    def on_key(self, event: Key) -> None:
        table = self.query_one(DataTable)
        if event.key == "enter":
            selected = table.cursor_row
            row_data = table.get_row_at(selected)
            selected_name = row_data[1]
            selected_node = self.volume_tree.index.get(
                self.current_path, {}
            ).childrens.get(selected_name)

            if selected_node and selected_node.is_directory:
                self.current_path = (
                    f"{self.current_path}/{selected_name}".strip("/")
                )
                self.load_data()
        elif event.key == "backspace":
            self.current_path = os.path.dirname(self.current_path)
            table = self.query_one(DataTable)
            self.load_data()


if __name__ == "__main__":  # pragma: no cover
    DockerTUI().run()
