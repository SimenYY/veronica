from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("veronica")
except PackageNotFoundError:
    __version__ = "dev"