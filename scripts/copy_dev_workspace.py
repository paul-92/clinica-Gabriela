"""Copy only development source files into an isolated workspace."""

from pathlib import Path
import shutil
import sys


SOURCE = Path(__file__).resolve().parents[1]
TARGET = Path(sys.argv[1]).resolve()
ALLOWED = {
    "app": {".py"},
    "backend": {".py"},
    "scripts": {".py", ".ps1"},
    "tests": {".py"},
    "frontend/src": {".js", ".jsx", ".css"},
    "frontend/electron": {".js", ".cjs"},
    "frontend/test": {".js"},
}
FILES = (
    "requirements.txt",
    "main.py",
    "constraints-dev.txt",
    "requirements-dev.lock",
    "frontend/package.json",
    "frontend/package-lock.json",
    "frontend/index.html",
    "frontend/vite.config.js",
    "docs/audit/spec005-20260922-human-legacy-data-decision.json",
)


def copy_file(path: Path) -> None:
    if path.is_symlink() or not path.is_file():
        raise RuntimeError(f"Fonte ausente ou link recusado: {path}")
    relative = path.relative_to(SOURCE)
    destination = TARGET / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, destination)


def main() -> None:
    for name, extensions in ALLOWED.items():
        directory = SOURCE / name
        if directory.is_symlink() or not directory.is_dir():
            raise RuntimeError(f"Diretorio fonte invalido: {directory}")
        for path in directory.rglob("*"):
            if path.is_symlink():
                raise RuntimeError(f"Link na fonte recusado: {path}")
            if path.is_file() and path.suffix in extensions:
                copy_file(path)
    for name in FILES:
        copy_file(SOURCE / name)
    print(f"WORKSPACE_DEV_READY: {TARGET}")


if __name__ == "__main__":
    main()
