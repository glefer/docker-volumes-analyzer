from unittest.mock import MagicMock, patch

import pytest

from docker_volume_analyzer.web import app


@pytest.fixture
def client():
    """Fixture to create a test client for the Flask app."""
    with app.test_client() as client:
        yield client


@patch("docker_volume_analyzer.web.VolumeManager")
def test_metrics_endpoint(mock_volume_manager, client):
    """
    Test the /metrics endpoint to ensure it returns Prometheus metrics.
    """
    mock_volume_manager_instance = MagicMock()
    mock_volume_manager.return_value = mock_volume_manager_instance
    mock_volume_manager_instance.get_volumes.return_value = {
        "volume1": {"size": 1024},
        "volume2": {"size": 2048},
    }

    response = client.get("/metrics")

    assert response.status_code == 200

    assert b"docker_volumes_total 2" in response.data
    assert b'docker_volume_size_bytes{name="volume1"} 1024.0' in response.data
    assert b'docker_volume_size_bytes{name="volume2"} 2048.0' in response.data


def test_index_endpoint(client):
    """
    Test the / endpoint to ensure it returns the correct HTML response.
    """
    response = client.get("/")

    assert response.status_code == 200

    assert b"Docker Volume Analyzer Metrics Endpoint" in response.data
