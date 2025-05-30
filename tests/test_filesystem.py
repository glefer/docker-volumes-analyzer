from datetime import datetime

import pytest

from docker_volume_analyzer.filesystem import (
    FileNode,
    FileSystem,
    parse_find_output,
)


@pytest.fixture
def now():
    """Fixture for the current datetime."""
    return datetime.now()


@pytest.fixture
def make_file(now):
    """Fixture to create a FileNode."""

    def _make(name, path, size):
        return FileNode(
            name=name,
            path=path,
            size=size,
            mtime=now,
            mode="-rw-r--r--",
            user="user",
            group="group",
            is_directory=False,
        )

    return _make


@pytest.fixture
def fs():
    """Fixture to create an empty FileSystem."""
    return FileSystem()


@pytest.fixture
def sample_output():
    """Sample output from the 'find' command."""
    return (
        "directory|/mnt/docker_volume/dir1|4096"
        "|drwxr-xr-x|user|group|1633024800\n"
        "file|/mnt/docker_volume/dir1/file1.txt|1024"
        "|-rw-r--r--|user|group|1633024800\n"
        "file|/mnt/docker_volume/dir1/file2.txt|2048"
        "|-rw-r--r--|user|group|1633024800"
    )


def test_add_node_to_filesystem(fs, make_file):
    """Test adding a node to the FileSystem."""
    node = make_file("file.txt", "dir1/file.txt", 1024)

    fs.add_node(node)

    assert "dir1" in fs.index
    assert "dir1/file.txt" in fs.index
    assert fs.index["dir1"].is_directory
    assert fs.index["dir1/file.txt"].size == 1024


def test_compute_directory_sizes(fs, make_file):
    """Test computing directory sizes in the FileSystem."""
    fs.add_node(make_file("file1.txt", "dir1/file1.txt", 1024))
    fs.add_node(make_file("file2.txt", "dir1/file2.txt", 2048))

    fs.compute_directory_sizes()

    assert fs.index["dir1"].size == 3072


def test_parse_find_output(sample_output):
    """Test parsing valid output from the 'find' command."""
    fs = parse_find_output(sample_output)

    assert "dir1" in fs.index
    assert "dir1/file1.txt" in fs.index
    assert "dir1/file2.txt" in fs.index
    assert fs.index["dir1"].is_directory
    assert fs.index["dir1/file1.txt"].size == 1024
    assert fs.index["dir1/file2.txt"].size == 2048


@pytest.mark.parametrize(
    "output,strip_prefix,expected_keys",
    [
        (
            "directory|/mnt/docker_volume/dir1|4096"
            "|drwxr-xr-x|user|group|1633024800\n"
            "file|/mnt/docker_volume/dir1/file1.txt|1024"
            "|-rw-r--r--|user|group|1633024800",
            "/mnt/docker_volume",
            {"dir1", "dir1/file1.txt"},
        ),
        (
            "directory|/mnt/docker_volume/dir2|4096"
            "|drwxr-xr-x|user|group|1633024800",
            "/mnt/docker_volume",
            {"dir2"},
        ),
    ],
)
def test_parse_find_output_with_strip_prefix(
    output, strip_prefix, expected_keys
):
    """Test parsing output with a strip prefix."""
    fs = parse_find_output(output, strip_prefix=strip_prefix)

    non_root_keys = {key for key in fs.index.keys() if key != ""}
    assert non_root_keys == expected_keys


def test_parse_find_output_malformed_line():
    """Test parsing output with a malformed line."""
    output = (
        "directory|/mnt/docker_volume/dir1|4096"
        "|drwxr-xr-x|user|group|1633024800\n"
        "malformed_line"
    )

    fs = parse_find_output(output)

    assert "dir1" in fs.index
    assert len(fs.index) == 2


def test_parse_find_output_empty():
    """Test parsing an empty output."""
    fs = parse_find_output("")

    assert len(fs.index) == 1
