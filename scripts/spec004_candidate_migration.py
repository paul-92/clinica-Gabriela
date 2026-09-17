import argparse
import hashlib
import json
import shutil
from pathlib import Path

from backend.migration.spec004 import migrate_spec004


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True); parser.add_argument("--output", required=True)
    args = parser.parse_args(); source = Path(args.source).resolve(strict=True); output = Path(args.output).resolve()
    if output.exists(): raise SystemExit("output ja existe")
    output.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(source, output)
    result = migrate_spec004(output)
    result.update({"source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "candidate_sha256": hashlib.sha256(output.read_bytes()).hexdigest(), "privacy_safe": True})
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__": main()
