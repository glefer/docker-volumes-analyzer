from flask import Flask, Response
from prometheus_client import CollectorRegistry, Gauge, generate_latest

from docker_volume_analyzer.docker_client import DockerClient
from docker_volume_analyzer.volume_manager import VolumeManager

app = Flask(__name__)

registry = CollectorRegistry()

docker_volumes_total = Gauge(
    "docker_volumes_total", "Total number of Docker volumes", registry=registry
)
docker_volume_size_bytes = Gauge(
    "docker_volume_size_bytes",
    "Size of individual Docker volumes in bytes",
    ["name"],
    registry=registry,
)

docker_client = DockerClient()


@app.route("/")
def index():
    return (
        "<p>Docker Volume Analyzer Metrics Endpoint.<br/> "
        "Visit <a href='/metrics'>/metrics</a> for Prometheus metrics.</p>"
    )


@app.route("/metrics")
def metrics():
    volume_manager = VolumeManager(docker_client=docker_client)
    volumes = volume_manager.get_volumes(human_readable=False)
    docker_volumes_total.set(len(volumes))
    for volume_name, volume_info in volumes.items():
        docker_volume_size_bytes.labels(name=volume_name).set(
            volume_info["size"]
        )

    # Return metrics in Prometheus format
    return Response(generate_latest(registry), mimetype="text/plain")


def main():
    app.run(host="0.0.0.0", port=8000)  # pragma: no cover
