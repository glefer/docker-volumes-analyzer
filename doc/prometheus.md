# Prometheus metrics endpoint
The following metrics are exposed by the Prometheus metrics endpoint:

- **`docker_volumes_total`**: The total number of Docker volumes currently available.
    - **Type**: Gauge
    - **Labels**: None
    - **Example**: `docker_volumes_total 42`

- **`docker_volume_size_bytes`**: The size of each Docker volume in bytes.
    - **Type**: Gauge
    - **Labels**:
        - `volume`: The name of the Docker volume.
    - **Example**: `docker_volume_size_bytes{volume="my_volume"} 104857600`

## Accessing the Metrics Endpoint

The Prometheus metrics are exposed at the `/metrics` endpoint. Depending on the mode in which the application is running, you can access the endpoint as follows:

- **Web mode**: `http://<host>:8000/metrics`
- **Gunicorn mode**: `http://<host>:8000/metrics`

Replace `<host>` with the hostname or IP address where the application is running.

## Integrating with Prometheus

To scrape the metrics exposed by the application, add the following job configuration to your Prometheus configuration file (`prometheus.yml`):

```yaml
scrape_configs:
  - job_name: "docker_volume_analyzer"
    static_configs:
      - targets: ["<host>:8000"]