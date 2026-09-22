from __future__ import annotations

import argparse
import json

from backend.migration.spec005 import migrate_finance_candidate


def main():
    parser = argparse.ArgumentParser(description="Migracao financeira SPEC-005 em candidato isolado")
    parser.add_argument("--source", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    evidence = migrate_finance_candidate(args.source, args.output)
    print(json.dumps(evidence.to_dict(), sort_keys=True))


if __name__ == "__main__":
    main()
