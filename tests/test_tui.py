from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from textual.events import Key
from textual.widgets import Button, DataTable, Static

from docker_volume_analyzer.tui import (
    ConfirmationScreen,
    DockerTUI,
    ErrorScreen,
    VolumeBrowserScreen,
    VolumeDetailScreen,
)


@pytest.mark.asyncio
async def test_on_mount():
    """
    Test that the on_mount method populates
    the DataTable with volume data.
    """
    mock_manager = MagicMock()
    mock_manager.get_volumes.return_value = {
        0: {
            "name": "volume1",
            "size": "10GB",
            "containers": [{"container_name": "container1"}],
            "created_at": "2023-01-01T00:00:00Z",
        },
        1: {
            "name": "volume2",
            "size": "20GB",
            "containers": [],
            "created_at": "2023-01-02T00:00:00Z",
        },
    }

    with patch(
        "docker_volume_analyzer.tui.VolumeManager", return_value=mock_manager
    ):
        async with DockerTUI().run_test() as pilot:
            await pilot.pause()

            app = pilot.app
            table: DataTable = app.query_one(
                "#volumes_table", expect_type=DataTable
            )

            rows = [table.get_row(row_key) for row_key in table.rows]

            assert len(rows) == 2
            assert rows[0] == ["volume1", "10GB", 1, "2023-01-01T00:00:00Z"]
            assert rows[1] == ["volume2", "20GB", 0, "2023-01-02T00:00:00Z"]


def test_action_toggle_dark():
    """Test that the action_toggle_dark method toggles the theme."""
    app = DockerTUI()
    app.theme = "textual-light"

    app.action_toggle_dark()
    assert app.theme == "textual-dark"

    app.action_toggle_dark()
    assert app.theme == "textual-light"


@pytest.mark.asyncio
async def test_action_information():
    """
    Test that the action_information method displays the correct
    volume details.
    """
    mock_manager = MagicMock()
    mock_manager.get_volumes.return_value = {
        "volume1": {
            "name": "volume1",
            "size": "10GB",
            "containers": [
                {"short_id": "abc123", "container_name": "container1"}
            ],
            "created_at": "2023-01-01T00:00:00Z",
            "mountpoint": "/var/lib/docker/volumes/volume1",
        },
        "volume2": {
            "name": "volume2",
            "size": "20GB",
            "containers": [],
            "created_at": "2023-01-02T00:00:00Z",
            "mountpoint": "/var/lib/docker/volumes/volume2",
        },
    }

    with patch(
        "docker_volume_analyzer.tui.VolumeManager", return_value=mock_manager
    ):
        async with DockerTUI().run_test() as pilot:
            await pilot.pause()

            app = pilot.app
            table: DataTable = app.query_one(
                "#volumes_table", expect_type=DataTable
            )
            table.add_row("volume1", "10GB", 1, "2023-01-01T00:00:00Z")
            table.cursor_type = 0

            app.action_information()
            assert isinstance(app.screen_stack[-1], VolumeDetailScreen)

            screen = app.screen_stack[-1]
            assert screen.volume_info["name"] == "volume1"
            assert screen.volume_info["size"] == "10GB"
            assert screen.volume_info["created_at"] == "2023-01-01T00:00:00Z"
            assert (
                screen.volume_info["mountpoint"]
                == "/var/lib/docker/volumes/volume1"
            )
            assert len(screen.volume_info["containers"]) == 1
            assert (
                screen.volume_info["containers"][0]["container_name"]
                == "container1"
            )
            assert screen.volume_info["containers"][0]["short_id"] == "abc123"


@pytest.mark.asyncio
async def test_action_information_no_selection():
    """
    Test that the action_information method does nothing
    when no row is selected in the DataTable.
    """
    mock_manager = MagicMock()
    mock_manager.get_volumes.return_value = {
        "volume1": {
            "name": "volume1",
            "size": "10GB",
            "containers": [
                {"short_id": "abc123", "container_name": "container1"}
            ],
            "created_at": "2023-01-01T00:00:00Z",
            "mountpoint": "/var/lib/docker/volumes/volume1",
        }
    }

    with patch(
        "docker_volume_analyzer.tui.VolumeManager", return_value=mock_manager
    ):
        async with DockerTUI().run_test() as pilot:
            await pilot.pause()

            app = pilot.app
            table: DataTable = app.query_one(
                "#volumes_table", expect_type=DataTable
            )

            with patch.object(
                type(table), "cursor_row", new_callable=PropertyMock
            ) as mock_cursor_row:
                mock_cursor_row.return_value = None

                app.action_information()

                assert len(app.screen_stack) == 1
                assert not isinstance(app.screen_stack[-1], VolumeDetailScreen)


@pytest.mark.asyncio
async def test_action_previous_removes_screen_and_refreshes():
    volume_info = {
        "name": "volume1",
        "size": "10GB",
        "created_at": "2023-01-01",
        "mountpoint": "/mnt/volume1",
        "containers": [{"short_id": "abc123", "container_name": "container1"}],
    }

    screen = VolumeDetailScreen(volume_info)

    mock_app = MagicMock()

    with patch.object(
        type(screen), "app", new_callable=PropertyMock
    ) as mock_app_prop:
        mock_app_prop.return_value = mock_app

        screen.action_back()

        mock_app.pop_screen.assert_called_once()
        mock_app.refresh.assert_called_once()


@pytest.mark.asyncio
async def test_action_delete_volume_with_no_selection():
    """
    Test that the action_delete_volume method does nothing
    when no row is selected in the DataTable.
    """
    mock_manager = MagicMock()
    mock_manager.get_volumes.return_value = {
        "volume1": {
            "name": "volume1",
            "size": "10GB",
            "containers": [],
            "created_at": "2023-01-01T00:00:00Z",
        }
    }

    with patch(
        "docker_volume_analyzer.tui.VolumeManager", return_value=mock_manager
    ):
        async with DockerTUI().run_test() as pilot:
            await pilot.pause()

            app = pilot.app
            table: DataTable = app.query_one(
                "#volumes_table", expect_type=DataTable
            )

            with patch.object(
                type(table), "cursor_row", new_callable=PropertyMock
            ) as mock_cursor_row:
                mock_cursor_row.return_value = None

                app.action_delete_volume()

                assert len(app.screen_stack) == 1


@pytest.mark.asyncio
async def test_action_delete_volume_with_attached_containers():
    """
    Test that the action_delete_volume method shows an error screen
    when the selected volume has attached containers.
    """
    mock_manager = MagicMock()
    mock_manager.get_volumes.return_value = {
        "volume1": {
            "name": "volume1",
            "size": "10GB",
            "containers": [{"container_name": "container1"}],
            "created_at": "2023-01-01T00:00:00Z",
        }
    }

    with patch(
        "docker_volume_analyzer.tui.VolumeManager", return_value=mock_manager
    ):
        async with DockerTUI().run_test() as pilot:
            await pilot.pause()

            app = pilot.app
            table: DataTable = app.query_one(
                "#volumes_table", expect_type=DataTable
            )
            table.add_row("volume1", "10GB", 1, "2023-01-01T00:00:00Z")
            with patch.object(
                type(table), "cursor_row", new_callable=PropertyMock
            ) as mock_cursor_row:
                mock_cursor_row.return_value = 0

            app.action_delete_volume()

            assert isinstance(app.screen_stack[-1], ErrorScreen)
            assert (
                app.screen_stack[-1].message
                == "Cannot delete volume with attached containers."
            )


@pytest.mark.asyncio
async def test_action_delete_volume_success():
    """
    Test that the action_delete_volume method deletes the selected volume
    when confirmed.
    """
    mock_manager = MagicMock()
    mock_manager.get_volumes.return_value = {
        "volume1": {
            "name": "volume1",
            "size": "10GB",
            "containers": [],
            "created_at": "2023-01-01T00:00:00Z",
        }
    }

    with patch(
        "docker_volume_analyzer.tui.VolumeManager", return_value=mock_manager
    ):
        async with DockerTUI().run_test() as pilot:
            await pilot.pause()

            app = pilot.app
            table: DataTable = app.query_one(
                "#volumes_table", expect_type=DataTable
            )
            table.cursor_type = 0

            app.action_delete_volume()
            confirmation_screen = app.screen_stack[-1]
            assert isinstance(confirmation_screen, ConfirmationScreen)

            confirmation_screen.on_button_pressed(
                Button.Pressed(Button("Yes", id="yes_button"))
            )

            mock_manager.delete_volume.assert_called_once_with("volume1")
            assert len(table.rows) == 0


@pytest.mark.asyncio
async def test_action_delete_volume_not_confirmed():
    """
    Test that the action_delete_volume method does not delete the volume
    when the user does not confirm.
    """
    mock_manager = MagicMock()
    mock_manager.get_volumes.return_value = {
        "volume1": {
            "name": "volume1",
            "size": "10GB",
            "containers": [],
            "created_at": "2023-01-01T00:00:00Z",
        }
    }

    with patch(
        "docker_volume_analyzer.tui.VolumeManager", return_value=mock_manager
    ):
        async with DockerTUI().run_test() as pilot:
            await pilot.pause()

            app = pilot.app
            table: DataTable = app.query_one(
                "#volumes_table", expect_type=DataTable
            )
            table.cursor_type = 0

            app.action_delete_volume()
            confirmation_screen = app.screen_stack[-1]
            assert isinstance(confirmation_screen, ConfirmationScreen)

            confirmation_screen.on_button_pressed(
                Button.Pressed(Button("No", id="no_button"))
            )

            mock_manager.delete_volume.assert_not_called()
            assert len(table.rows) == 1


@pytest.mark.asyncio
async def test_action_delete_volume_throw_exception():
    """
    Test that the action_delete_volume method handles exceptions
    when trying to delete a volume.
    """
    mock_manager = MagicMock()
    mock_manager.get_volumes.return_value = {
        "volume1": {
            "name": "volume1",
            "size": "10GB",
            "containers": [],
            "created_at": "2023-01-01T00:00:00Z",
        }
    }
    mock_manager.delete_volume.side_effect = Exception("Docker error")

    with patch(
        "docker_volume_analyzer.tui.VolumeManager", return_value=mock_manager
    ):
        async with DockerTUI().run_test() as pilot:
            await pilot.pause()

            app = pilot.app
            table: DataTable = app.query_one(
                "#volumes_table", expect_type=DataTable
            )
            table.cursor_type = 0

            app.action_delete_volume()
            confirmation_screen = app.screen_stack[-1]
            assert isinstance(confirmation_screen, ConfirmationScreen)

            confirmation_screen.on_button_pressed(
                Button.Pressed(Button("Yes", id="yes_button"))
            )

            assert isinstance(app.screen_stack[-1], ErrorScreen)
            assert (
                app.screen_stack[-1].message
                == "Error deleting volume: Docker error"
            )


@pytest.mark.asyncio
async def test_error_screen_action_back():
    """
    Test that the action_back method pops the ErrorScreen.
    """
    error_message = "This is an error message."
    screen = ErrorScreen(error_message)

    mock_app = MagicMock()

    with patch.object(
        type(screen), "app", new_callable=PropertyMock
    ) as mock_app_prop:
        mock_app_prop.return_value = mock_app

        screen.action_back()

        mock_app.pop_screen.assert_called_once()


@pytest.mark.asyncio
async def test_action_browse():
    """
    Test that the action_browse method pushes the VolumeBrowserScreen
    with the correct volume name.
    """
    mock_manager = MagicMock()
    mock_manager.get_volumes.return_value = {
        "volume1": {
            "name": "volume1",
            "size": "10GB",
            "containers": [],
            "created_at": "2023-01-01T00:00:00Z",
        }
    }

    with patch(
        "docker_volume_analyzer.tui.VolumeManager", return_value=mock_manager
    ):
        async with DockerTUI().run_test() as pilot:
            app = pilot.app

            app.query_one("#volumes_table", expect_type=DataTable).add_row(
                "volume1", "10GB", 0, "2023-01-01T00:00:00Z"
            )
            app.action_browse()
            await pilot.pause()

            screen = app.screen_stack[-1]
            assert isinstance(screen, VolumeBrowserScreen)
            assert screen.volume_name == "volume1"
            assert screen.volume_manager == mock_manager
            assert (
                screen.query_one(
                    "#current_path", expect_type=Static
                ).renderable
                == "[b]Current path:[/b] /"
            )


@pytest.mark.asyncio
async def test_volume_browser_screen_initialization():
    """
    Test that the VolumeBrowserScreen initializes correctly
    with the given volume name and manager.
    """
    mock_manager = MagicMock()
    mock_manager.get_volume_tree.return_value = MagicMock(index={})

    screen = VolumeBrowserScreen(mock_manager, "test_volume")

    assert screen.volume_name == "test_volume"
    assert screen.volume_manager == mock_manager
    assert screen.current_path == ""
    assert screen.volume_tree == mock_manager.get_volume_tree.return_value


@pytest.mark.asyncio
async def test_volume_browser_screen_load_data_empty_directory():
    """
    Test that the VolumeBrowserScreen displays
    a message when the directory is empty.
    """
    mock_manager = MagicMock()
    mock_manager.get_volume_tree.return_value = MagicMock(index={})

    screen = VolumeBrowserScreen(mock_manager, "test_volume")

    with patch.object(
        screen, "query_one", return_value=MagicMock()
    ) as mock_query:
        screen.compose()
        screen.load_data()

        mock_query.assert_called_with(DataTable)
        mock_query.return_value.clear.assert_called_once()
        mock_query.return_value.add_row.assert_called_once_with(
            "No files found in this directory."
        )


@pytest.mark.asyncio
async def test_volume_browser_screen_load_data_with_files():
    """
    Test that the VolumeBrowserScreen loads
    and displays files and directories correctly.
    """
    mock_manager = MagicMock()
    mock_node = MagicMock()
    mock_node.is_directory = True
    mock_node.size = 0
    mock_node.mtime.strftime.return_value = "2023-01-01 00:00:00"

    mock_manager.get_volume_tree.return_value = MagicMock(
        index={
            "": MagicMock(
                childrens={
                    "folder1": mock_node,
                    "file1.txt": MagicMock(
                        is_directory=False,
                        size=1024,
                        mtime=MagicMock(
                            strftime=lambda fmt: "2023-01-01 00:00:00"
                        ),
                    ),
                }
            )
        }
    )

    screen = VolumeBrowserScreen(mock_manager, "test_volume")

    mock_table = MagicMock()
    mock_current_path = MagicMock()
    with patch.object(
        screen,
        "query_one",
        side_effect=lambda selector: (
            mock_table if selector == DataTable else mock_current_path
        ),
    ) as mock_query:
        screen.load_data()

        mock_query.assert_any_call(DataTable)
        mock_table.clear.assert_called_once()
        mock_table.add_row.assert_any_call(
            "📁 ", "folder1", "0 bytes", "2023-01-01 00:00:00"
        )
        mock_table.add_row.assert_any_call(
            "📄 ", "file1.txt", "1024 bytes", "2023-01-01 00:00:00"
        )

        mock_query.assert_any_call("#current_path")
        mock_current_path.update.assert_called_once_with(
            "[b]Current path:[/b] /"
        )


@pytest.mark.asyncio
async def test_volume_browser_screen_action_back():
    """
    Test that the action_back method pops the screen and refreshes the app.
    """
    mock_app = MagicMock()
    screen = VolumeBrowserScreen(MagicMock(), "test_volume")

    with patch.object(
        type(screen), "app", new_callable=PropertyMock
    ) as mock_app_prop:
        mock_app_prop.return_value = mock_app

        screen.action_back()

        mock_app.pop_screen.assert_called_once()
        mock_app.refresh.assert_called_once()


@pytest.mark.asyncio
async def test_volume_browser_screen_on_key_enter_directory():
    """
    Test that pressing 'enter' navigates into a directory.
    """
    mock_manager = MagicMock()
    mock_node = MagicMock(is_directory=True)
    mock_manager.get_volume_tree.return_value = MagicMock(
        index={
            "": MagicMock(childrens={"folder1": mock_node}),
            "folder1": MagicMock(childrens={}),
        }
    )

    screen = VolumeBrowserScreen(mock_manager, "test_volume")
    screen.current_path = ""

    with patch.object(
        screen, "query_one", return_value=MagicMock()
    ) as mock_query:
        mock_query.return_value.cursor_row = 0
        mock_query.return_value.get_row_at.return_value = ["📁 ", "folder1"]

        screen.on_key(Key("enter", None))

        assert screen.current_path == "folder1"
        mock_query.return_value.clear.assert_called_once()


@pytest.mark.asyncio
async def test_volume_browser_screen_on_key_backspace():
    """
    Test that pressing 'backspace' navigates to the parent directory.
    """
    mock_manager = MagicMock()
    mock_manager.get_volume_tree.return_value = MagicMock(index={})

    screen = VolumeBrowserScreen(mock_manager, "test_volume")
    screen.current_path = "folder1/subfolder"

    with patch.object(
        screen, "query_one", return_value=MagicMock()
    ) as mock_query:
        screen.on_key(Key("backspace", None))

        assert screen.current_path == "folder1"
        mock_query.return_value.clear.assert_called_once()


@pytest.mark.asyncio
async def test_on_key_enter_invalid_selection():
    """
    Test that pressing 'enter' does nothing if the selected item is invalid.
    """
    mock_manager = MagicMock()
    mock_manager.get_volume_tree.return_value = MagicMock(index={})

    screen = VolumeBrowserScreen(mock_manager, "test_volume")
    screen.current_path = ""

    mock_node = MagicMock()
    mock_node.childrens = {}
    screen.volume_tree.index = {"": mock_node}

    with patch.object(
        screen, "query_one", return_value=MagicMock()
    ) as mock_query:
        mock_query.return_value.cursor_row = 0
        mock_query.return_value.get_row_at.return_value = [
            "📄 ",
            "invalid_item",
        ]

        screen.on_key(Key("enter", None))

        assert screen.current_path == ""
        mock_query.return_value.clear.assert_not_called()


@pytest.mark.asyncio
async def test_on_key_other_key():
    """
    Test that pressing a key other than 'enter' or 'backspace' does nothing.
    """
    mock_manager = MagicMock()
    mock_manager.get_volume_tree.return_value = MagicMock(index={})

    screen = VolumeBrowserScreen(mock_manager, "test_volume")
    screen.current_path = "folder1/subfolder"

    with patch.object(
        screen, "query_one", return_value=MagicMock()
    ) as mock_query:
        screen.on_key(Key("space", None))

        assert screen.current_path == "folder1/subfolder"
        mock_query.return_value.clear.assert_not_called()


@pytest.mark.asyncio
async def test_volume_browser_screen_on_key_delete_file_error():
    """
    Test that pressing 'delete' shows an error screen if deleting a file fails.
    """
    mock_manager = MagicMock()
    mock_node = MagicMock(is_directory=False, path="folder1/file1.txt")
    mock_manager.get_volume_tree.return_value = MagicMock(
        index={"folder1": MagicMock(childrens={"file1.txt": mock_node})}
    )
    mock_manager.delete_volume_file.side_effect = Exception("Delete error")

    screen = VolumeBrowserScreen(mock_manager, "test_volume")
    screen.current_path = "folder1"

    with (
        patch.object(
            screen, "query_one", return_value=MagicMock()
        ) as mock_query,
        patch.object(
            type(screen), "app", new_callable=PropertyMock
        ) as mock_app_prop,
    ):
        mock_app = MagicMock()
        mock_app_prop.return_value = mock_app
        mock_query.return_value.cursor_row = 0
        mock_query.return_value.get_row_at.return_value = ["📄 ", "file1.txt"]

        screen.on_key(Key("delete", None))

        mock_manager.delete_volume_file.assert_called_once_with(
            "test_volume", "folder1/file1.txt"
        )
        screen.volume_tree.delete_node.assert_not_called()
        mock_app.push_screen.assert_called_once()
        assert isinstance(mock_app.push_screen.call_args[0][0], ErrorScreen)
        assert (
            mock_app.push_screen.call_args[0][0].message
            == "Error deleting file: Delete error"
        )


@pytest.mark.asyncio
async def test_volume_browser_screen_on_key_delete_file_success():
    """
    Test that pressing 'delete' successfully deletes a file and updates the UI.
    """
    mock_manager = MagicMock()
    mock_node = MagicMock(is_directory=False, path="folder1/file1.txt")
    mock_manager.get_volume_tree.return_value = MagicMock(
        index={"folder1": MagicMock(childrens={"file1.txt": mock_node})}
    )

    screen = VolumeBrowserScreen(mock_manager, "test_volume")
    screen.current_path = "folder1"

    with patch.object(
        screen, "query_one", return_value=MagicMock()
    ) as mock_query:
        mock_query.return_value.cursor_row = 0
        mock_query.return_value.get_row_at.return_value = ["📄 ", "file1.txt"]

        screen.on_key(Key("delete", None))

        screen.volume_tree.delete_node.assert_called_once_with(
            "folder1/file1.txt"
        )

        mock_manager.delete_volume_file.assert_called_once_with(
            "test_volume", "folder1/file1.txt"
        )


@pytest.mark.asyncio
async def test_volume_browser_screen_on_key_delete_invalid_node():
    """
    Test that pressing 'delete' does nothing if the selected node is invalid.
    """
    mock_manager = MagicMock()
    mock_node = MagicMock()
    mock_node.childrens = {}  # Ensure 'childrens' attribute exists
    mock_manager.get_volume_tree.return_value = MagicMock(
        index={"": mock_node}
    )

    screen = VolumeBrowserScreen(mock_manager, "test_volume")
    screen.current_path = ""

    with patch.object(
        screen, "query_one", return_value=MagicMock()
    ) as mock_query:
        mock_query.return_value.cursor_row = 0
        mock_query.return_value.get_row_at.return_value = [
            "📄 ",
            "invalid_item",
        ]

        screen.on_key(Key("delete", None))

        mock_manager.delete_volume_file.assert_not_called()
        screen.volume_tree.delete_node.assert_not_called()
        mock_query.return_value.clear.assert_not_called()
