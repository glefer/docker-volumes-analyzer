class DockerNotAvailableError(Exception):
    """Raised when Docker is not available on the system."""

    def __init__(
        self,
        message="Docker is not available. "
        "Please ensure Docker is installed and running.",
    ):
        super().__init__(message)
