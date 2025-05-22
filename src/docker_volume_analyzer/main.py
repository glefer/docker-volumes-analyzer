from docker_volume_analyzer.tui import DockerTUI


class VolumeManagerApp:
    def __init__(self):
        self.tui = DockerTUI()

    def run(self):
        """Lance l'application TUI"""
        self.tui.run()


def main():
    """Point d'entrée principal de l'application"""
    app = VolumeManagerApp()
    app.run()


if __name__ == "__main__":  # pragma: no cover
    main()
