#!/usr/bin/env python3
"""Relay project bootstrapper and integrity checker.

The runtime intentionally uses only the Python standard library so it can be
used on a fresh machine before any project dependencies are installed.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import sys
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parent
TEMPLATE_ROOT = REPO_ROOT / "templates"
VERSION_FILE = REPO_ROOT / "VERSION"
VERSION = VERSION_FILE.read_text(encoding="utf-8").strip() if VERSION_FILE.exists() else "dev"


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def home_agents() -> Path:
    return Path.home() / ".agents"


def profile_for(path: Path) -> str:
    """Choose a conservative profile from observable repository signals."""
    if (path / "AI_START_HERE.md").exists() or (path / "docs" / "product-boundary.md").exists():
        return "heavy"
    entries = list(path.iterdir()) if path.exists() else []
    file_count = sum(1 for item in path.rglob("*") if item.is_file()) if path.exists() else 0
    if file_count <= 8 and len(entries) <= 12:
        return "lite"
    return "standard"


def files_for(profile: str) -> list[tuple[Path, Path]]:
    common = [
        (TEMPLATE_ROOT / "AGENTS.md", Path("AGENTS.md")),
    ]
    if profile in {"standard", "heavy"}:
        common += [
            (TEMPLATE_ROOT / "ARCHITECTURE.md", Path("ARCHITECTURE.md")),
            (TEMPLATE_ROOT / "CONTEXT.md", Path("CONTEXT.md")),
            (TEMPLATE_ROOT / ".agents" / "cd-weekly-log.md", Path(".agents/cd-weekly-log.md")),
            (TEMPLATE_ROOT / ".agents" / "proper-nouns.md", Path(".agents/proper-nouns.md")),
            (TEMPLATE_ROOT / ".agents" / "cloud-archive.md", Path(".agents/cloud-archive.md")),
        ]
    if profile == "heavy":
        common += [
            (TEMPLATE_ROOT / "AI_START_HERE.md", Path("AI_START_HERE.md")),
            (TEMPLATE_ROOT / "docs" / "product-boundary.md", Path("docs/product-boundary.md")),
            (
                TEMPLATE_ROOT / ".agents" / "skills" / "domain-skill-template" / "SKILL.md",
                Path(".agents/skills/domain-skill-template/SKILL.md"),
            ),
        ]
    return common


def package_files() -> list[Path]:
    """Return all files required for a source-package integrity check."""
    required = [REPO_ROOT / "VERSION", REPO_ROOT / "PHILOSOPHY.md", REPO_ROOT / "relay.py"]
    required += [REPO_ROOT / "custodian" / "projects.md", REPO_ROOT / "custodian" / "ai-agents.md"]
    for directory in (REPO_ROOT / "skills", REPO_ROOT / "templates"):
        required.extend(item for item in directory.rglob("*") if item.is_file())
    return required


def registry_path() -> Path:
    return home_agents() / "custodian" / "projects.json"


def read_registry(registry: Path) -> list[dict[str, object]]:
    if not registry.exists():
        return []
    try:
        loaded = json.loads(registry.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid project registry {registry}: {error}") from error
    if not isinstance(loaded, list):
        raise ValueError(f"project registry must be a JSON array: {registry}")
    return [item for item in loaded if isinstance(item, dict)]


def relpath(path: Path) -> str:
    return path.as_posix()


def copy_file(source: Path, destination: Path, force: bool, dry_run: bool) -> str:
    if destination.exists() and not destination.is_file():
        return f"conflict {relpath(destination)} (destination is not a file; preserved)"
    if destination.exists() and not force:
        if source.read_bytes() == destination.read_bytes():
            return f"unchanged {relpath(destination)}"
        return f"conflict {relpath(destination)} (preserved; use --force to replace)"
    if not dry_run:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    return f"write {relpath(destination)}"


def update_registry(project: Path, profile: str, dry_run: bool) -> Path:
    root = home_agents() / "custodian"
    registry = root / "projects.json"
    if dry_run:
        return registry
    root.mkdir(parents=True, exist_ok=True)
    records = read_registry(registry)
    record = {
        "path": str(project),
        "profile": profile,
        "ledger": str(project / ".agents" / "cd-weekly-log.md"),
        "updated_at": now(),
        "status": "active",
    }
    records = [item for item in records if item.get("path") != record["path"]]
    records.append(record)
    registry.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return registry


def init_project(path: Path, profile: str, force: bool, dry_run: bool, register: bool) -> int:
    path = path.expanduser().resolve()
    if register:
        try:
            read_registry(registry_path())
        except ValueError as error:
            print(f"error: {error}", file=sys.stderr)
            return 2
    if not path.exists():
        if dry_run:
            print(f"would create project directory: {path}")
        else:
            path.mkdir(parents=True)
    if not path.is_dir() and not (dry_run and not path.exists()):
        print(f"error: target is not a directory: {path}", file=sys.stderr)
        return 2
    selected = profile_for(path) if profile == "auto" else profile
    if selected not in {"lite", "standard", "heavy"}:
        print(f"error: unsupported profile: {selected}", file=sys.stderr)
        return 2
    print(f"Relay {VERSION}: init {path} ({selected})")
    conflicts = 0
    for source, relative in files_for(selected):
        if not source.exists():
            print(f"error: missing package asset: {source}", file=sys.stderr)
            return 2
        result = copy_file(source, path / relative, force, dry_run)
        print(result)
        conflicts += result.startswith("conflict ")
    if conflicts:
        print("init incomplete: metadata and project registry were not updated", file=sys.stderr)
        return 2
    metadata = path / ".agents" / "relay.json"
    if selected == "lite":
        metadata = path / ".relay.json"
    if metadata.exists() and not metadata.is_file():
        print(f"conflict {relpath(metadata)} (destination is not a file; preserved)")
        conflicts += 1
    elif metadata.exists() and not force:
        print(f"unchanged {relpath(metadata)}")
    elif dry_run:
        print(f"would write {relpath(metadata)}")
    else:
        metadata.parent.mkdir(parents=True, exist_ok=True)
        metadata.write_text(
            json.dumps({"version": VERSION, "profile": selected, "initialized_at": now()}, ensure_ascii=False, indent=2)
            + "\n",
            encoding="utf-8",
        )
    if register:
        registry = update_registry(path, selected, dry_run)
        print(("would update " if dry_run else "updated ") + str(registry))
    return 0


def expected_for(path: Path) -> list[Path]:
    metadata = path / ".agents" / "relay.json"
    if not metadata.exists():
        metadata = path / ".relay.json"
    if not metadata.exists():
        return []
    try:
        profile = json.loads(metadata.read_text(encoding="utf-8-sig")).get("profile")
    except (OSError, json.JSONDecodeError, AttributeError):
        return []
    return [path / destination for _, destination in files_for(profile)] if profile in {"lite", "standard", "heavy"} else []


def audit(path: Path) -> int:
    path = path.expanduser().resolve()
    expected = expected_for(path)
    if not expected:
        print(f"FAIL {path}: no valid Relay metadata (.relay.json or .agents/relay.json)")
        return 1
    missing = [str(item) for item in expected if not item.exists()]
    if missing:
        print(f"FAIL {path}: missing {len(missing)} asset(s)")
        for item in missing:
            print(f"  - {item}")
        return 1
    print(f"OK {path}: {len(expected)} assets present")
    return 0


def audit_result(path: Path) -> tuple[str, str]:
    path = path.expanduser()
    if not path.exists() or not path.is_dir():
        return "path-missing", "project directory does not exist"
    expected = expected_for(path)
    if not expected:
        return "not-initialized", "no valid Relay metadata"
    missing = [relpath(item.relative_to(path)) for item in expected if not item.exists()]
    if missing:
        return "incomplete", "missing: " + ", ".join(missing)
    return "healthy", f"{len(expected)} assets present"


def sweep(dry_run: bool, report_path: Path | None = None) -> int:
    registry = registry_path()
    if not registry.exists():
        print(f"No project registry found: {registry}")
        return 0
    try:
        records = read_registry(registry)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    checked: list[tuple[dict[str, object], str, str]] = []
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("path"), str):
            continue
        status, detail = audit_result(Path(record["path"]))
        record["status"] = status
        record["last_audit_at"] = now()
        checked.append((record, status, detail))
    stamp = dt.datetime.now().strftime("%G-W%V")
    destination = report_path or (home_agents() / "custodian" / "reports" / f"{stamp}.md")
    lines = [
        "# Relay Custodian Report",
        "",
        f"Generated: {now()}",
        "",
        "| Project | Status | Detail |",
        "| :--- | :--- | :--- |",
    ]
    for record, status, detail in checked:
        lines.append(f"| `{record['path']}` | `{status}` | {detail} |")
    report = "\n".join(lines) + "\n"
    print(f"Relay sweep: {len(checked)} project(s)")
    for record, status, detail in checked:
        print(f"{status}: {record['path']} ({detail})")
    print(("would write " if dry_run else "report ") + str(destination))
    if not dry_run:
        registry.parent.mkdir(parents=True, exist_ok=True)
        registry.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(report, encoding="utf-8")
    return 0 if all(status == "healthy" for _, status, _ in checked) else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="relay", description="Deterministic Relay project bootstrapper")
    parser.add_argument("--version", action="version", version=VERSION)
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init", help="install a Relay profile into a project")
    init.add_argument("path", nargs="?", default=".")
    init.add_argument("--profile", choices=["auto", "lite", "standard", "heavy"], default="auto")
    init.add_argument("--force", action="store_true", help="overwrite existing managed assets")
    init.add_argument("--dry-run", action="store_true", help="show changes without writing")
    init.add_argument("--no-register", action="store_true", help="skip the global project registry")
    check = commands.add_parser("audit", help="verify a Relay project")
    check.add_argument("path", nargs="?", default=".")
    sweep_parser = commands.add_parser("sweep", help="audit registered projects and write a report")
    sweep_parser.add_argument("--dry-run", action="store_true", help="show results without updating registry or report")
    sweep_parser.add_argument("--report", type=Path, help="write the report to this path")
    commands.add_parser("version", help="print the Relay version")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "version":
        print(VERSION)
        return 0
    if args.command == "init":
        return init_project(Path(args.path), args.profile, args.force, args.dry_run, not args.no_register)
    if args.command == "audit":
        return audit(Path(args.path))
    if args.command == "sweep":
        return sweep(args.dry_run, args.report)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
