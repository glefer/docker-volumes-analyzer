from unittest.mock import patch

from docker_volume_analyzer.main import VolumeManagerApp, main


def test_volume_manager_app_run():
    """Test that VolumeManagerApp.run() calls DockerTUI.run()."""
    with patch("docker_volume_analyzer.main.DockerTUI") as MockDockerTUI:
        app = VolumeManagerApp()
        app.run()
        MockDockerTUI.return_value.run.assert_called_once()


def test_main():
    """Test that the main() function initializes and runs the application."""
    with patch("docker_volume_analyzer.main.VolumeManagerApp") as MockApp:
        main()
        MockApp.return_value.run.assert_called_once()
