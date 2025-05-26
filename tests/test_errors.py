import pytest

from docker_volume_analyzer.errors import DockerNotAvailableError

EXCEPTIONS = [
    (
        DockerNotAvailableError,
        "Docker is not available. "
        "Please ensure Docker is installed and running.",
    ),
]


@pytest.mark.parametrize("exception_class, default_message", EXCEPTIONS)
def test_custom_exceptions_default_message(exception_class, default_message):
    with pytest.raises(exception_class) as exc_info:
        raise exception_class()
    assert str(exc_info.value) == default_message


@pytest.mark.parametrize("exception_class, _", EXCEPTIONS)
def test_custom_exceptions_custom_message(exception_class, _):
    msg = f"Custom message for {exception_class.__name__}"
    with pytest.raises(exception_class) as exc_info:
        raise exception_class(msg)
    assert str(exc_info.value) == msg
