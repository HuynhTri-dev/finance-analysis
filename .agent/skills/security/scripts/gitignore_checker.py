"""
name: gitignore_checker.py
description: Audits a project's .gitignore file for missing critical patterns and checks
             whether any sensitive files are currently tracked by Git. Provides actionable
             remediation commands when issues are found.

Usage:
    python scripts/gitignore_checker.py --dir <path_to_project_root>
    python scripts/gitignore_checker.py --dir . --output report.txt
    python scripts/gitignore_checker.py --help
"""

import argparse
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple


# ---------------------------------------------------------------------------
# Required gitignore patterns grouped by category
# ---------------------------------------------------------------------------
@dataclass
class IgnoreRule:
    """Represents a single required .gitignore rule."""
    pattern: str
    category: str
    risk_level: str  # critical, high, medium
    description: str


REQUIRED_RULES: List[IgnoreRule] = [
    # Secrets & Environment
    IgnoreRule(".env", "Secrets & Environment", "critical", "Environment variable files containing secrets."),
    IgnoreRule(".env.*", "Secrets & Environment", "critical", "Environment-specific files (e.g., .env.local, .env.production)."),
    IgnoreRule("*.pem", "Secrets & Environment", "critical", "PEM-encoded private keys and certificates."),
    IgnoreRule("*.key", "Secrets & Environment", "critical", "Private key files."),
    IgnoreRule("*.p12", "Secrets & Environment", "critical", "PKCS#12 certificate/key bundles."),
    IgnoreRule("*.pfx", "Secrets & Environment", "critical", "Personal Information Exchange certificate files."),
    IgnoreRule("secrets.*", "Secrets & Environment", "critical", "Generic secrets files (e.g., secrets.json, secrets.yaml)."),
    IgnoreRule("credentials.*", "Secrets & Environment", "critical", "Credential files (e.g., credentials.json, credentials.csv)."),
    IgnoreRule("*.token", "Secrets & Environment", "high", "Token files."),
    IgnoreRule("service-account*.json", "Secrets & Environment", "critical", "Google Cloud service account key files."),
    IgnoreRule("google-credentials.json", "Secrets & Environment", "critical", "Google application default credential files."),

    # Dependency Directories
    IgnoreRule("node_modules/", "Dependencies", "high", "Node.js packages — large, auto-reinstallable."),
    IgnoreRule("venv/", "Dependencies", "high", "Python virtual environment."),
    IgnoreRule(".venv/", "Dependencies", "high", "Python virtual environment (alternate naming)."),
    IgnoreRule("env/", "Dependencies", "medium", "Python environment directory."),
    IgnoreRule("vendor/", "Dependencies", "medium", "Go / PHP / Ruby vendored dependencies."),
    IgnoreRule("target/", "Dependencies", "medium", "Java/Rust build output directory."),
    IgnoreRule("__pycache__/", "Dependencies", "medium", "Python compiled bytecode cache."),
    IgnoreRule("*.pyc", "Dependencies", "low", "Python compiled bytecode files."),

    # Build Outputs
    IgnoreRule("dist/", "Build Outputs", "high", "Distribution build output (JS, Python packages)."),
    IgnoreRule("build/", "Build Outputs", "high", "General build output directory."),
    IgnoreRule(".next/", "Build Outputs", "medium", "Next.js build cache and output."),
    IgnoreRule(".nuxt/", "Build Outputs", "medium", "Nuxt.js build output."),
    IgnoreRule("out/", "Build Outputs", "medium", "Compiled output directory (Next.js export)."),
    IgnoreRule("bin/", "Build Outputs", "medium", "Compiled binary output directory."),
    IgnoreRule("obj/", "Build Outputs", "medium", ".NET object files."),
    IgnoreRule("*.class", "Build Outputs", "medium", "Java compiled class files."),

    # Logs
    IgnoreRule("*.log", "Logs", "high", "Application log files may contain sensitive runtime data."),
    IgnoreRule("npm-debug.log*", "Logs", "medium", "npm debug logs."),
    IgnoreRule("yarn-debug.log*", "Logs", "medium", "Yarn debug logs."),
    IgnoreRule("yarn-error.log*", "Logs", "medium", "Yarn error logs."),
    IgnoreRule("pip-log.txt", "Logs", "low", "pip install logs."),

    # IDE & OS
    IgnoreRule(".vscode/", "IDE & OS Config", "medium", "VS Code workspace settings (may contain personal configs)."),
    IgnoreRule(".idea/", "IDE & OS Config", "medium", "JetBrains IDE project settings."),
    IgnoreRule("*.suo", "IDE & OS Config", "low", "Visual Studio solution user options."),
    IgnoreRule("*.user", "IDE & OS Config", "low", "Visual Studio user-specific project files."),
    IgnoreRule(".DS_Store", "IDE & OS Config", "low", "macOS directory metadata files."),
    IgnoreRule("Thumbs.db", "IDE & OS Config", "low", "Windows Explorer thumbnail cache."),
    IgnoreRule("Desktop.ini", "IDE & OS Config", "low", "Windows folder configuration files."),

    # Test & Coverage
    IgnoreRule("coverage/", "Test Artifacts", "medium", "Code coverage report directory."),
    IgnoreRule(".nyc_output/", "Test Artifacts", "medium", "Istanbul/nyc coverage output."),
    IgnoreRule("htmlcov/", "Test Artifacts", "medium", "Python coverage HTML reports."),
    IgnoreRule(".pytest_cache/", "Test Artifacts", "low", "pytest cache directory."),
]

# Patterns that indicate a file tracked by git is sensitive
SENSITIVE_TRACKED_PATTERNS = [
    ".env", ".pem", ".key", ".p12", ".pfx", "credentials", "secrets",
    "service-account", "private_key", "id_rsa", "id_ed25519",
]

RISK_ICONS = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵"}


def load_gitignore(root_dir: Path) -> Tuple[bool, List[str]]:
    """
    Reads the .gitignore file from the project root.

    Parameters:
        root_dir: The project root directory.

    Returns:
        A tuple of (exists: bool, lines: List[str]).
    """
    gitignore_path = root_dir / ".gitignore"
    if not gitignore_path.exists():
        return False, []
    lines = gitignore_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    return True, lines


def pattern_is_covered(rule_pattern: str, gitignore_lines: List[str]) -> bool:
    """
    Checks whether a required pattern is covered by the existing .gitignore content.

    Parameters:
        rule_pattern: The pattern string to look for (e.g., '*.env', 'node_modules/').
        gitignore_lines: All lines from the .gitignore file.

    Returns:
        True if the pattern is present and not commented out.
    """
    normalized = rule_pattern.strip().lower().lstrip("/")
    for line in gitignore_lines:
        stripped = line.strip()
        if stripped.startswith("#") or not stripped:
            continue
        if stripped.lower().lstrip("/") == normalized:
            return True
    return False


def get_git_tracked_files(root_dir: Path) -> List[str]:
    """
    Retrieves the list of all files currently tracked by Git.

    Parameters:
        root_dir: The project root directory.

    Returns:
        A list of file paths (relative to root_dir) tracked by Git.
        Returns an empty list if Git is not available or the directory is not a repo.
    """
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            capture_output=True,
            text=True,
            cwd=str(root_dir),
            timeout=30,
        )
        if result.returncode != 0:
            return []
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []


def find_sensitive_tracked_files(tracked_files: List[str]) -> List[str]:
    """
    Identifies any tracked files that appear to be sensitive based on name patterns.

    Parameters:
        tracked_files: List of file paths tracked by Git.

    Returns:
        A filtered list of file paths that match known sensitive patterns.
    """
    sensitive = []
    for file_path in tracked_files:
        lower = file_path.lower()
        for pattern in SENSITIVE_TRACKED_PATTERNS:
            if pattern in lower:
                sensitive.append(file_path)
                break
    return sensitive


def format_report(
    root_dir: Path,
    gitignore_exists: bool,
    missing_rules: List[IgnoreRule],
    sensitive_tracked: List[str],
    git_available: bool,
) -> str:
    """
    Formats a comprehensive gitignore audit report.

    Parameters:
        root_dir: The project root directory.
        gitignore_exists: Whether a .gitignore file was found.
        missing_rules: Rules that are not covered in the current .gitignore.
        sensitive_tracked: Files tracked by Git that appear sensitive.
        git_available: Whether the git command was available.

    Returns:
        A formatted multi-line string report.
    """
    lines = [
        "=" * 70,
        "  GITIGNORE AUDIT REPORT",
        f"  Root Directory: {root_dir}",
        "=" * 70,
        "",
    ]

    # 1. Existence Check
    if gitignore_exists:
        lines.append("✅ .gitignore file found at project root.")
    else:
        lines.append("🔴 CRITICAL: No .gitignore file found at project root!")
        lines.append("   → Create a .gitignore file immediately before committing any files.")
        lines.append("   → Tip: Use https://www.toptal.com/developers/gitignore to generate one.")
        lines.append("")

    lines.append("")

    # 2. Missing Patterns
    if not missing_rules:
        lines.append("✅ All required patterns are present in .gitignore.")
    else:
        critical = [r for r in missing_rules if r.risk_level == "critical"]
        non_critical = [r for r in missing_rules if r.risk_level != "critical"]

        lines.append(f"⚠️  {len(missing_rules)} required pattern(s) are missing from .gitignore:\n")

        for rule in critical + non_critical:
            icon = RISK_ICONS.get(rule.risk_level, "")
            lines.append(f"  {icon} [{rule.risk_level.upper()}] {rule.pattern}")
            lines.append(f"       Category : {rule.category}")
            lines.append(f"       Reason   : {rule.description}")
            lines.append("")

        lines.append("  → Add the following lines to your .gitignore:")
        lines.append("  " + "-" * 50)

        by_category: dict = {}
        for rule in missing_rules:
            by_category.setdefault(rule.category, []).append(rule.pattern)
        for cat, patterns in by_category.items():
            lines.append(f"  # {cat}")
            for p in patterns:
                lines.append(f"  {p}")
            lines.append("")

    lines.append("")

    # 3. Git Tracked Sensitive Files
    if not git_available:
        lines.append("ℹ️  Git tracking check skipped (git command not available or not a git repo).")
    elif not sensitive_tracked:
        lines.append("✅ No sensitive files are currently tracked by Git.")
    else:
        lines.append(f"🔴 CRITICAL: {len(sensitive_tracked)} sensitive file(s) are currently tracked by Git!\n")
        for f in sensitive_tracked:
            lines.append(f"  ❗ {f}")
        lines.append("")
        lines.append("  → These files contain secrets or credentials that may have been")
        lines.append("    exposed in your repository history.")
        lines.append("")
        lines.append("  → Remediation commands (run for each file):")
        lines.append("  " + "-" * 50)
        for f in sensitive_tracked:
            lines.append(f'  git rm --cached "{f}"')
        lines.append(f'  echo "<pattern>" >> .gitignore')
        lines.append('  git commit -m "fix: remove sensitive file from Git tracking"')
        lines.append("")
        lines.append("  → ⚠️  If the file has already been pushed to a remote repository,")
        lines.append("    treat the exposed secret as compromised and rotate it immediately.")
        lines.append("    Consider using git-filter-repo to purge the file from history.")

    lines.append("")
    lines.append("=" * 70)
    return "\n".join(lines)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """
    Parses command-line arguments for the gitignore checker.

    Parameters:
        argv: Optional list of argument strings (defaults to sys.argv).

    Returns:
        Parsed Namespace object with all argument values.
    """
    parser = argparse.ArgumentParser(
        prog="gitignore_checker",
        description="Audits .gitignore coverage and detects sensitive files tracked by Git.",
    )
    parser.add_argument("--dir", required=True, help="Path to the project root directory.")
    parser.add_argument("--output", default=None, help="Path to write the report. Defaults to stdout.")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    """
    Main entry point for the gitignore checker.

    Parameters:
        argv: Optional argument list for testing.

    Returns:
        Exit code: 0 if no issues, 1 if issues were detected.
    """
    args = parse_args(argv)
    root_dir = Path(args.dir).resolve()

    if not root_dir.is_dir():
        print(f"❌ Error: '{root_dir}' is not a valid directory.", file=sys.stderr)
        return 2

    print(f"🔍 Auditing gitignore in: {root_dir}", file=sys.stderr)

    gitignore_exists, gitignore_lines = load_gitignore(root_dir)
    missing_rules = [
        rule for rule in REQUIRED_RULES
        if not pattern_is_covered(rule.pattern, gitignore_lines)
    ]

    tracked_files = get_git_tracked_files(root_dir)
    git_available = len(tracked_files) > 0 or (root_dir / ".git").exists()
    sensitive_tracked = find_sensitive_tracked_files(tracked_files)

    report = format_report(
        root_dir=root_dir,
        gitignore_exists=gitignore_exists,
        missing_rules=missing_rules,
        sensitive_tracked=sensitive_tracked,
        git_available=git_available,
    )

    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
        print(f"📄 Report written to: {args.output}", file=sys.stderr)
    else:
        print(report)

    has_issues = not gitignore_exists or bool(missing_rules) or bool(sensitive_tracked)
    return 1 if has_issues else 0


if __name__ == "__main__":
    sys.exit(main())
