#!/usr/bin/env python3
"""Verifica que el diagrama ER de AGENTS/contrato.md coincida con database/schema.sql.

Compara, tabla por tabla, los nombres de columnas y sus tipos. Sale con codigo 1 si hay
diferencias. Solo necesita el paquete `pglast` (parser real de PostgreSQL):

    pip install pglast
    python database/check_contract_er.py

Es una herramienta de desarrollo; no forma parte de la aplicacion.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import pglast
    from pglast import ast
except ImportError:  # pragma: no cover
    sys.exit("Falta pglast: pip install pglast")

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "database" / "schema.sql"
CONTRACT = ROOT / "AGENTS" / "contrato.md"

# Nombre interno de PostgreSQL -> nombre usado en el diagrama
TYPE_ALIASES = {
    "int8": "bigint", "int4": "int", "int2": "smallint", "bool": "boolean",
    "bpchar": "char",
}


def tables_from_sql(path: Path) -> dict[str, dict[str, str]]:
    tables: dict[str, dict[str, str]] = {}
    for raw in pglast.parse_sql(path.read_text(encoding="utf-8")):
        stmt = raw.stmt
        if not isinstance(stmt, ast.CreateStmt):
            continue
        cols: dict[str, str] = {}
        for elt in stmt.tableElts or ():
            if isinstance(elt, ast.ColumnDef):
                base = elt.typeName.names[-1].sval
                base = TYPE_ALIASES.get(base, base)
                cols[elt.colname] = base + ("[]" if elt.typeName.arrayBounds else "")
        tables[stmt.relation.relname] = cols
    return tables


def tables_from_mermaid(path: Path) -> dict[str, dict[str, str]]:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"```mermaid\s+erDiagram(.*?)```", text, re.S)
    if not match:
        sys.exit("No se encontro un bloque mermaid erDiagram en " + str(path))
    tables: dict[str, dict[str, str]] = {}
    current = None
    for line in match.group(1).splitlines():
        line = line.strip()
        head = re.match(r'^"?([a-z_]+)"?\s*\{$', line)
        if head:
            current = head.group(1)
            tables[current] = {}
        elif line == "}":
            current = None
        elif current and line:
            type_, name = line.split()[:2]
            tables[current][name] = type_
    return tables


def main() -> int:
    sql = tables_from_sql(SCHEMA)
    doc = tables_from_mermaid(CONTRACT)
    problems = 0
    for table in sorted(set(sql) | set(doc)):
        if table not in doc:
            print(f"[{table}] esta en schema.sql pero no en el diagrama")
            problems += 1
            continue
        if table not in sql:
            print(f"[{table}] esta en el diagrama pero no en schema.sql")
            problems += 1
            continue
        only_sql = sorted(set(sql[table]) - set(doc[table]))
        only_doc = sorted(set(doc[table]) - set(sql[table]))
        wrong = [(c, sql[table][c], doc[table][c])
                 for c in sql[table] if c in doc[table] and sql[table][c] != doc[table][c]]
        if only_sql or only_doc or wrong:
            problems += 1
            print(f"[{table}]")
            if only_sql:
                print("  solo en schema.sql:", only_sql)
            if only_doc:
                print("  solo en el diagrama:", only_doc)
            for col, a, b in wrong:
                print(f"  tipo distinto en {col}: schema.sql={a} diagrama={b}")
    if problems:
        print(f"\n{problems} tabla(s) con diferencias.")
        return 1
    print(f"OK: {len(sql)} tablas y todas sus columnas coinciden entre schema.sql y contrato.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
