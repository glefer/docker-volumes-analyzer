from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from textual.widgets import Button, DataTable

from docker_volume_analyzer.tui import (
    ConfirmationScreen,
    DockerTUI,
    ErrorScreen,
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
            await pilot.pause()  # Wait for the interface to initialize

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
            table.cursor_type = 0  # Move the cursor to the first row

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

            # Patch cursor_row to simulate no row being selected
            with patch.object(
                type(table), "cursor_row", new_callable=PropertyMock
            ) as mock_cursor_row:
                mock_cursor_row.return_value = None

                app.action_information()

                # Assertions: no new screen was pushed
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

    # Création d'un mock pour app avec les méthodes pop_screen et refresh
    mock_app = MagicMock()

    # Patch la propriété 'app' du screen pour retourner mock_app
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

            # Patch cursor_row to simulate no row being selected
            with patch.object(
                type(table), "cursor_row", new_callable=PropertyMock
            ) as mock_cursor_row:
                mock_cursor_row.return_value = None

                app.action_delete_volume()

                # Assertions: no new screen was pushed
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
                mock_cursor_row.return_value = (
                    0  # Simulate the cursor on the first row
                )

            app.action_delete_volume()

            # Assertions: an error screen was pushed
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

            # Simulate user confirming the deletion
            app.action_delete_volume()
            confirmation_screen = app.screen_stack[-1]
            assert isinstance(confirmation_screen, ConfirmationScreen)

            # Simulate pressing "Yes" on the confirmation screen
            confirmation_screen.on_button_pressed(
                Button.Pressed(Button("Yes", id="yes_button"))
            )

            # Assertions
            mock_manager.delete_volume.assert_called_once_with("volume1")
            assert len(table.rows) == 0  # Volume was removed from the table


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

            # Simulate user confirming the deletion
            app.action_delete_volume()
            confirmation_screen = app.screen_stack[-1]
            assert isinstance(confirmation_screen, ConfirmationScreen)

            # Simulate pressing "No" on the confirmation screen
            confirmation_screen.on_button_pressed(
                Button.Pressed(Button("No", id="no_button"))
            )

            # Assertions
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

            # Simulate user confirming the deletion
            app.action_delete_volume()
            confirmation_screen = app.screen_stack[-1]
            assert isinstance(confirmation_screen, ConfirmationScreen)

            # Simulate pressing "Yes" on the confirmation screen
            confirmation_screen.on_button_pressed(
                Button.Pressed(Button("Yes", id="yes_button"))
            )

            # Assertions: an error screen was pushed
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

    # Create a mock app to test screen behavior
    mock_app = MagicMock()

    # Patch the 'app' property of the screen to return the mock app
    with patch.object(
        type(screen), "app", new_callable=PropertyMock
    ) as mock_app_prop:
        mock_app_prop.return_value = mock_app

        # Call the action_back method
        screen.action_back()

        # Assert that the screen was popped
        mock_app.pop_screen.assert_called_once()
