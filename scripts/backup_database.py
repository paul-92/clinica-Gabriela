from datetime import datetime
from pathlib import Path
from shutil import copy2


BASE_DIR = Path(__file__).resolve().parents[1]
source = BASE_DIR / "data" / "clinica_psicologia.db"
backup_dir = BASE_DIR / "backups"
backup_dir.mkdir(exist_ok=True)

if not source.exists():
    raise SystemExit("Banco de dados ainda nao existe. Execute python main.py primeiro.")

target = backup_dir / f"clinica_psicologia_{datetime.now():%Y%m%d_%H%M%S}.db"
copy2(source, target)
print(f"Backup criado em: {target}")
