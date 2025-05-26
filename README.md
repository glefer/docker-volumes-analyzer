# Docker volume analyzer

![Banner](./doc/assets/icon.webp)

Docker Volume Analyzer is a tool designed to simplify the management of Docker volumes. It provides features to:

- Visualize the containers associated with each volume.
- Explore the contents of volumes and delete files if needed.
- Retrieve basic information about volumes, such as size and usage.
- Streamline volume management tasks for improved efficiency.

This project aims to make Docker volume management more intuitive and user-friendly.

[![Python Poetry Application](https://github.com/glefer/docker-volumes-analyzer/actions/workflows/main.yml/badge.svg)](https://github.com/glefer/docker-volumes-analyzer/actions/workflows/main.yml)
[![codecov](https://codecov.io/gh/glefer/docker-volumes-analyzer/branch/main/graph/badge.svg?token=JRjmc0emjT)](https://codecov.io/gh/glefer/docker-volumes-analyzer)
![Python](https://img.shields.io/badge/python-3.13-blue)
[![Docker](https://img.shields.io/docker/pulls/glefer/docker-volumes-analyzer)](https://hub.docker.com/r/glefer/docker-volumes-analyzer)

## Installation

### Prerequisites

- **Python** `>=3.13,<4.0.0`
- **Poetry** `>=2.1.2` installed globally ([installation link](https://python-poetry.org/docs/#installation))
- Docker installed locally (if you want to analyze volumes)

---

### 1. Clone the project

```bash
git clone https://github.com/glefer/docker-volumes-analyzer.git
cd docker-volumes-analyzer
```

### 2. Install dependencies

```bash
poetry install
```

### 3. Run the application

```bash
poetry run start
```

> ⚠️ The application uses the Docker socket at the standard location: `/var/run/docker.sock`

---

## 🐳 Usage via Docker 

Don't want to install Python? Simply use the Docker image:

```bash
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -ti glefer/docker-volumes-analyzer:latest
```

### Use a specific version

```bash
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -ti glefer/docker-volumes-analyzer:0.1.0
```

---

## Run tests

```bash
poetry run pytest
```

With coverage:

```bash
poetry run pytest --cov=docker_volume_analyzer
```

---

## 🛠 Development

Start a virtual shell:

```bash
poetry shell
```

Formatting and checks:

```bash
poetry run pre-commit run --all-files
```

---

## 🔧 Project structure

```
.
├── src/
│   └── docker_volume_analyzer/
│       └── main.py   # Entry point
├── tests/
├── README.md
├── pyproject.toml
└── poetry.lock
```

## Contributing

Contributions are welcome! If you'd like to contribute, please follow these steps:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/my-feature`).
3. Commit your changes (`git commit -m 'Add some feature'`).
4. Push to the branch (`git push origin feature/my-feature`).
5. Open a pull request.

For major changes, please open an issue first to discuss what you would like to change.

---

## 📝 License

This project is licensed under the **MIT** license — see the [LICENSE](./LICENSE) file.

---

## 👨‍💻 Author
[github.com/glefer](https://github.com/glefer)