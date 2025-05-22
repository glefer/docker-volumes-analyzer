from pathlib import Path

from textual.binding import Binding
from textual.widgets import DirectoryTree

from docker_volume_analyzer.volume_manager import VolumeManager


class VirtualDirectoryTree(DirectoryTree):

    BINDINGS = DirectoryTree.BINDINGS + [
        Binding("d", "delete_file", "Delete selected file"),
    ]

    def __init__(
        self, tree_dict: dict, manager: VolumeManager, name: str = "Root"
    ):
        super().__init__(Path(f"/{name}"))
        self.tree_dict = tree_dict
        self.root.label = name
        self.manager = manager

    def on_mount(self) -> None:
        """Build the virtual tree when the widget is mounted."""
        self.build_virtual_tree(self.root, self.tree_dict)

    def build_virtual_tree(self, node, data: dict) -> None:
        """
        Recursively build the virtual tree structure from a dictionary.

        Args:
            node: The current node in the tree.
            data: The dictionary representing the tree structure.

        Returns:
            None: No return value.
        """
        for name, content in data.items():
            if content is None:
                node.add_leaf(name)
            else:
                folder_node = node.add(name, expand=False)
                self.build_virtual_tree(folder_node, content)
        self.root.expand()

    def update_virtual_tree(self, new_tree_dict: dict, root_name: str) -> None:
        """
        Update the virtual tree with a new dictionary structure.

        Args:
            new_tree_dict: The new dictionary representing the tree structure.
            root_name: The name of the root node.

        Returns:
            None: No return value.
        """
        self.tree_dict = new_tree_dict
        self.root.label = root_name
        self.clear()
        self.build_virtual_tree(self.root, self.tree_dict)
        self.refresh()

    def action_delete_file(self) -> None:
        """
        Delete the selected file or folder.
        This method is triggered when the user presses the 'd' key.

        Returns:
            None: No return value.
        """

        selected_node = self.cursor_node
        if selected_node is None:
            self.app.log("No node selected to delete.")
            return

        table = self.parent.query_one("#volumes_table")
        cursor_row = table.cursor_row
        if cursor_row is None:
            self.app.log("No volume selected.")
            return

        file_path = []
        node = selected_node
        while node and node.parent is not None:
            file_path.append(str(node.label))
            node = node.parent
        file_path = "/".join(reversed(file_path))

        current_row = table.get_row_at(cursor_row)

        if not selected_node.children:
            result = self.manager.delete_file_from_volume(
                current_row[0], file_path
            )
            if result:
                self.app.log(f"File {file_path} deleted successfully.")
                selected_node.remove()

            else:
                self.app.log(f"Failed to delete file {file_path}.")
