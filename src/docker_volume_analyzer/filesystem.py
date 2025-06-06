from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional


@dataclass
class FileNode:
    """
    Represents a file or directory in the file system.

    Attributes:
        name (str): The name of the file or directory.
        path (str): The full path of the file or directory.
        size (int): The size of the file in bytes.
        mtime (datetime): The last modified time of the file or directory.
        mode (str): The file mode (permissions) as a string.
        user (str): The owner of the file or directory.
        group (str): The group owner of the file or directory.
        is_directory (bool): True if the node is a directory,
        False if it is a file.
        childrens (Dict[str, "FileNode"]): A dictionary of child nodes
        where the key is the child's name.
        parent (Optional["FileNode"]): A reference to the parent node
        or None if it is the root.
    """

    name: str
    path: str
    size: int
    mtime: datetime
    mode: str
    user: str
    group: str
    is_directory: bool
    childrens: Dict[str, "FileNode"] = field(default_factory=dict)
    parent: Optional["FileNode"] = None


class FileSystem:
    """
    Represents a file system structure, allowing for the addition
    and retrieval of file nodes.

    Attributes:
        root (FileNode): The root node of the file system.
        index (Dict[str, FileNode]): A dictionary mapping relative
        paths to their corresponding FileNode.
    """

    def __init__(self):
        self.root = FileNode(
            name="",
            path="",
            size=0,
            mtime=datetime.now(),
            mode="",
            user="",
            group="",
            is_directory=True,
        )
        self.index = {"": self.root}

    def add_node(self, node: FileNode):
        parts = node.path.strip("/").split("/")
        current = self.root
        full_path = ""

        for i, part in enumerate(parts):
            full_path = "/".join(parts[: i + 1])
            if full_path not in self.index:
                is_last = i == len(parts) - 1
                n = FileNode(
                    name=part,
                    path=full_path,
                    size=node.size if is_last else 0,
                    mtime=node.mtime,
                    mode=node.mode,
                    user=node.user,
                    group=node.group,
                    is_directory=node.is_directory if is_last else True,
                    parent=current,
                )
                current.childrens[part] = n
                self.index[full_path] = n
            current = self.index[full_path]

    def delete_node(self, path: str) -> "FileSystem":
        """
        Deletes a node and its children from the file system and updates
        the sizes of parent directories.

        Args:
            path (str): The path of the node to delete.

        Returns:
            FileSystem: The updated file system after deletion.
        """
        if path not in self.index:
            raise ValueError(
                f"Path '{path}' does not exist in the file system."
            )

        node_to_delete = self.index[path]

        def delete_recursively(node: FileNode):
            for child in list(node.childrens.values()):
                delete_recursively(child)
            del self.index[node.path]

        delete_recursively(node_to_delete)

        if node_to_delete.parent:
            parent = node_to_delete.parent
            del parent.childrens[node_to_delete.name]

            size_change = node_to_delete.size
            current = parent
            while current:
                current.size -= size_change
                current = current.parent

        return self

    def compute_directory_sizes(self) -> "FileSystem":
        """
        Compute the total size of each directory by summing the sizes
        of its files, subdirectories,
        and the directory's own size (e.g., 4 KB for metadata).
        """
        for path in sorted(
            self.index.keys(), key=lambda x: x.count("/"), reverse=True
        ):
            node = self.index[path]
            if node.is_directory:
                total_size = node.size

                for child in node.childrens.values():
                    total_size += child.size

                node.size = total_size

        return self


def parse_find_output(
    output: str, strip_prefix: str = "/mnt/docker_volume"
) -> FileSystem:
    """
    Parses the output of the 'find' command with stat
    and builds a FileSystem object.

    Args:
        output (str): The output string from the 'find' command,
        strip_prefix (str): A prefix to strip from the path in the output
        default is '/mnt/docker_volume'.

    Returns:
        FileSystem: An instance of FileSystem containing the parsed file nodes.
    """
    fs = FileSystem()
    for line in output.strip().split("\n"):
        try:
            type_str, path, size, mode, user, group, mtime = line.split("|")

            path = (
                path[len(strip_prefix) :].lstrip("/")
                if path.startswith(strip_prefix)
                else path.lstrip("/")
            )

            node = FileNode(
                name=path.split("/")[-1],
                path=path,
                size=int(size),
                mtime=datetime.fromtimestamp(int(mtime)),
                mode=mode,
                user=user,
                group=group,
                is_directory=(type_str == "directory"),
            )
            fs.add_node(node)
        except Exception as e:
            print(f"Skipping malformed line: {line} ({e})")
    return fs
