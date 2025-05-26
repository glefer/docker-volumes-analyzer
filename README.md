# Docker volume analyzer

![Banner](./doc/assets/icon.webp)

Docker Volume Analyzer is a tool designed to simplify the management of Docker volumes. It provides features to:

- Visualize the containers associated with each volume.
- Explore the contents of volumes and delete files if needed.
- Retrieve basic information about volumes, such as size and usage.
- Streamline volume management tasks for improved efficiency.

This project aims to make Docker volume management more intuitive and user-friendly.

[![Build Status](https://github.com/glefer/docker-volumes-analyzer/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/glefer/docker-volumes-analyzer/actions)
[![codecov](https://codecov.io/gh/glefer/docker-volumes-analyzer/branch/main/graph/badge.svg?token=JRjmc0emjT)](https://codecov.io/gh/glefer/docker-volumes-analyzer)
![Python](https://img.shields.io/badge/python-3.13-blue)


## Installation

### Prérequis

- **Python** `>=3.13,<4.0.0`
- **Poetry** `>=2.1.2` installé globalement ([lien d’installation](https://python-poetry.org/docs/#installation))
- Docker en local (si tu veux analyser des volumes)

---

### 1. Cloner le projet

```bash
git clone https://github.com/glefer/docker-volumes-analyzer.git
cd docker-volumes-analyzer
```

### 2. Installer les dépendances

```bash
poetry install
```

### 3. Lancer l'application

```bash
poetry run start
```

> ⚠️ L'application utilise le socket Docker à l'emplacement standard : `/var/run/docker.sock`

---

## 🐳 Utilisation via Docker 

Pas envie d’installer Python ? Utilise simplement l’image Docker :

```bash
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -ti glefer/docker-volumes-analyzer:latest
```

###  Utiliser une version spécifique

```bash
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -ti glefer/docker-volumes-analyzer:0.1.0
```

---

## Lancer les tests

```bash
poetry run pytest
```

Avec couverture :

```bash
poetry run pytest --cov=docker_volume_analyzer
```

---

## 🛠 Développement

Lance un shell virtuel :

```bash
poetry shell
```

Formatage et vérifications :

```bash
poetry run pre-commit run --all-files
```

---

## 🔧 Structure du projet

```
.
├── src/
│   └── docker_volume_analyzer/
│       └── main.py   # Point d’entrée
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

## 📝 Licence

Ce projet est sous licence **MIT** — voir le fichier [LICENSE](./LICENSE).

---

## 👨‍💻 Auteur
[github.com/glefer](https://github.com/glefer)