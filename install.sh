#!/usr/bin/env bash
# Relay 安装器（macOS / Linux）
#
# 默认行为是无损安装：同内容文件跳过，已有但不同的文件报告冲突并保留用户版本。
# 使用 --force 才会覆盖冲突；配合 --backup 可在覆盖前生成时间戳备份。
#
# 示例：
#   bash ./install.sh --dry-run
#   bash ./install.sh --force --backup
#   bash ./install.sh --check

set -Eeuo pipefail

DRY_RUN=0
FORCE=0
BACKUP=0
CHECK=0
QUIET=0
AGENTS_DIR="${HOME}/.agents"

usage() {
    cat <<'EOF'
Relay installer

Options:
  --dry-run             Show changes without writing files
  --force               Overwrite conflicting target files
  --backup              Back up files before a --force update
  --check               Validate the package without touching the target
  --agents-dir PATH     Install into PATH instead of ~/.agents
  --quiet               Suppress per-file output
  -h, --help            Show this help
EOF
}

while (($# > 0)); do
    case "$1" in
        --dry-run) DRY_RUN=1 ;;
        --force) FORCE=1 ;;
        --backup) BACKUP=1 ;;
        --check) CHECK=1 ;;
        --quiet) QUIET=1 ;;
        --agents-dir)
            shift
            (($# > 0)) || { echo "--agents-dir requires a path" >&2; exit 64; }
            AGENTS_DIR="$1"
            ;;
        -h|--help) usage; exit 0 ;;
        *) echo "Unknown option: $1" >&2; usage >&2; exit 64 ;;
    esac
    shift
done

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
VERSION_FILE="$SCRIPT_DIR/VERSION"
if [[ -f "$VERSION_FILE" ]]; then
    VERSION="$(tr -d '\r\n' < "$VERSION_FILE")"
else
    VERSION="dev"
fi

if command -v sha256sum >/dev/null 2>&1; then
    hash_file() { sha256sum "$1" | awk '{print $1}'; }
elif command -v shasum >/dev/null 2>&1; then
    hash_file() { shasum -a 256 "$1" | awk '{print $1}'; }
else
    echo "Relay requires sha256sum or shasum for conflict detection" >&2
    exit 1
fi

status() {
    ((QUIET)) || printf '%s\n' "$1"
}

required_files=(
    "VERSION"
    "relay.py"
    "PHILOSOPHY.md"
    "custodian/projects.md"
    "custodian/ai-agents.md"
    "custodian/cd-weekly-log.md"
)
for relative in "${required_files[@]}"; do
    if [[ ! -f "$SCRIPT_DIR/$relative" ]]; then
        echo "Relay package is incomplete; missing file: $SCRIPT_DIR/$relative" >&2
        exit 1
    fi
done
for directory in skills templates; do
    if [[ ! -d "$SCRIPT_DIR/$directory" ]]; then
        echo "Relay package is incomplete; missing directory: $SCRIPT_DIR/$directory" >&2
        exit 1
    fi
done

if ((CHECK)); then
    file_count=0
    while IFS= read -r -d '' _; do ((file_count += 1)); done < <(find "$SCRIPT_DIR/skills" "$SCRIPT_DIR/templates" -type f -print0)
    status "Relay package OK: version ${VERSION}, $((file_count + ${#required_files[@]})) files"
    exit 0
fi

if ((!DRY_RUN)); then
    mkdir -p "$AGENTS_DIR" "$AGENTS_DIR/custodian/reports" "$AGENTS_DIR/skills" "$AGENTS_DIR/templates"
fi

installed=0
unchanged=0
conflicts=0
backed_up=0
timestamp="$(date +%Y%m%d-%H%M%S)"

process_file() {
    local source="$1"
    local relative="$2"
    local destination="$AGENTS_DIR/$relative"
    local parent
    parent="$(dirname -- "$destination")"

    if [[ -e "$destination" || -L "$destination" ]] && [[ ! -f "$destination" ]]; then
        status "[CONFLICT] $relative (目标路径不是文件；保留目标路径)"
        ((conflicts += 1))
        return
    fi

    if [[ ! -f "$destination" ]]; then
        status "[ADD] $relative"
        if ((!DRY_RUN)); then
            mkdir -p "$parent"
            cp -p "$source" "$destination"
        fi
        ((installed += 1))
        return
    fi

    if [[ "$(hash_file "$source")" == "$(hash_file "$destination")" ]]; then
        status "[OK]  $relative"
        ((unchanged += 1))
        return
    fi

    if ((!FORCE)); then
        status "[CONFLICT] $relative (保留目标文件；使用 --force 覆盖)"
        ((conflicts += 1))
        return
    fi

    if ((BACKUP)); then
        local backup="$destination.bak.$timestamp"
        status "[BACKUP] $backup"
        if ((!DRY_RUN)); then cp -p "$destination" "$backup"; fi
        ((backed_up += 1))
    fi

    status "[UPDATE] $relative"
    if ((!DRY_RUN)); then cp -p "$source" "$destination"; fi
    ((installed += 1))
}

for relative in "${required_files[@]}"; do
    process_file "$SCRIPT_DIR/$relative" "$relative"
done

while IFS= read -r -d '' source; do
    relative="${source#"$SCRIPT_DIR/"}"
    process_file "$source" "$relative"
done < <(find "$SCRIPT_DIR/skills" "$SCRIPT_DIR/templates" -type f -print0)

status ""
suffix=""
((DRY_RUN)) && suffix=" (dry-run，未写入)"
status "Relay ${VERSION}: 新增/更新 ${installed}，未变更 ${unchanged}，备份 ${backed_up}，冲突 ${conflicts}"
status "目标目录: ${AGENTS_DIR}${suffix}"
if ((!DRY_RUN)); then
    status "CLI: python \"${AGENTS_DIR}/relay.py\" init . --profile auto"
fi

if ((conflicts > 0)); then
    status "安装未完全应用：存在冲突。确认目标文件后重新运行 --force（建议同时使用 --backup）。"
    exit 2
fi

exit 0
