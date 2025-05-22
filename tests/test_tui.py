from unittest.mock import MagicMock, patch

import pytest
from textual.widgets import DataTable

from docker_volume_analyzer.tui import DockerTUI


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
