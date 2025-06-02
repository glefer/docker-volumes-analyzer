# pragma: no cover
from docker_volume_analyzer.web import app

application = app

if __name__ == "__main__":
    app.run()
