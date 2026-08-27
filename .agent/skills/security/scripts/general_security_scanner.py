"""
name: general_security_scanner.py
description: A language-agnostic static analysis scanner that uses regex patterns and heuristics to
             detect hardcoded secrets, insecure configurations, and dangerous function calls across
             a project directory. Designed to be run as part of the security-architecture-blueprint
             skill verification step.

Usage:
    python scripts/general_security_scanner.py --dir <path_to_project_root>
    python scripts/general_security_scanner.py --dir . --output report.txt
    python scripts/general_security_scanner.py --dir . --severity high

Arguments:
    --dir       (required)  Path to the directory to scan.
    --output    (optional)  Path to write the report file. Defaults to stdout.
    --severity  (optional)  Minimum severity to report: critical, high, medium, low. Default: low.
    --ignore    (optional)  Comma-separated list of additional patterns to ignore.
"""

import argparse
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

# ---------------------------------------------------------------------------
# Configuration: File extensions to scan and directories to skip
# ---------------------------------------------------------------------------
SCANNABLE_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".java", ".kt",
    ".yaml", ".yml", ".json", ".env", ".sh", ".bash", ".tf",
    ".toml", ".ini", ".cfg", ".conf", ".properties", ".xml",
    ".rb", ".php", ".cs", ".cpp", ".c", ".h", ".rs",
}

SKIP_DIRS = {
    ".git", "node_modules", "venv", ".venv", "env", "__pycache__",
    "build", "dist", "target", ".next", ".nuxt", "vendor",
    "coverage", ".pytest_cache", ".mypy_cache", "bin", "obj",
    ".idea", ".vscode", "migrations",
}

# ---------------------------------------------------------------------------
# Pattern definitions
# ---------------------------------------------------------------------------
@dataclass
class SecurityPattern:
    """Represents a single security detection rule."""
    id: str
    name: str
    severity: str  # critical, high, medium, low
    category: str
    pattern: re.Pattern
    description: str
    false_positive_note: str = ""


SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

PATTERNS: List[SecurityPattern] = [
    # --- Critical: Secrets & Credentials ---
    SecurityPattern(
        id="SEC-001", name="AWS Access Key",
        severity="critical", category="Secrets & Credentials",
        pattern=re.compile(r"(?<![A-Z0-9])AKIA[0-9A-Z]{16}(?![A-Z0-9])", re.IGNORECASE),
        description="Hardcoded AWS Access Key ID detected.",
        false_positive_note="Verify it is a real key and not a test/mock value.",
    ),
    SecurityPattern(
        id="SEC-002", name="AWS Secret Access Key",
        severity="critical", category="Secrets & Credentials",
        pattern=re.compile(r"(?i)aws.{0,20}secret.{0,20}['\"][0-9a-zA-Z/+=]{40}['\"]"),
        description="Potential hardcoded AWS Secret Access Key detected.",
        false_positive_note="Verify the value is a real credential, not a placeholder.",
    ),
    SecurityPattern(
        id="SEC-003", name="Generic API Key / Token Assignment",
        severity="high", category="Secrets & Credentials",
        pattern=re.compile(
            r"(?i)(api_key|apikey|api_secret|auth_token|access_token|secret_key|private_key)\s*[=:]\s*['\"][a-zA-Z0-9\-_./+=]{16,}['\"]"
        ),
        description="Potential hardcoded API key or secret token detected in an assignment.",
        false_positive_note="Verify it is not a placeholder like 'your-api-key-here'.",
    ),
    SecurityPattern(
        id="SEC-004", name="Hardcoded Password Assignment",
        severity="critical", category="Secrets & Credentials",
        pattern=re.compile(
            r"(?i)(password|passwd|pwd)\s*[=:]\s*['\"][^'\"]{4,}['\"]"
        ),
        description="Potential hardcoded password detected.",
        false_positive_note="Exclude variables like 'is_password_valid' or test fixtures.",
    ),
    SecurityPattern(
        id="SEC-005", name="RSA / EC Private Key Block",
        severity="critical", category="Secrets & Credentials",
        pattern=re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"),
        description="A private key block was found in the file.",
    ),
    SecurityPattern(
        id="SEC-006", name="Generic Bearer Token",
        severity="high", category="Secrets & Credentials",
        pattern=re.compile(r"(?i)bearer\s+[a-zA-Z0-9\-_=.+/]{20,}"),
        description="Hardcoded Bearer token found in file.",
    ),
    SecurityPattern(
        id="SEC-007", name="Database Connection String with Credentials",
        severity="critical", category="Secrets & Credentials",
        pattern=re.compile(
            r"(?i)(postgres|mysql|mongodb|redis|sqlite):\/\/[^:]+:[^@]+@"
        ),
        description="Database connection string with embedded credentials detected.",
    ),
    # --- High: Insecure Configurations ---
    SecurityPattern(
        id="CFG-001", name="Debug Mode Enabled",
        severity="high", category="Insecure Configuration",
        pattern=re.compile(r"(?i)(DEBUG\s*=\s*True|APP_DEBUG\s*=\s*true|debug\s*:\s*true)"),
        description="Debug mode is explicitly enabled. This must not be enabled in production.",
    ),
    SecurityPattern(
        id="CFG-002", name="All-Interface Bind Address",
        severity="medium", category="Insecure Configuration",
        pattern=re.compile(r"(host\s*[=:]\s*['\"]?0\.0\.0\.0['\"]?|bind\s*=\s*0\.0\.0\.0)"),
        description="Service is configured to bind to all network interfaces (0.0.0.0).",
        false_positive_note="Acceptable inside a Docker container, but not on bare metal.",
    ),
    SecurityPattern(
        id="CFG-003", name="TLS/SSL Verification Disabled",
        severity="critical", category="Insecure Configuration",
        pattern=re.compile(r"(?i)(verify\s*=\s*False|ssl_verify\s*=\s*false|insecure\s*=\s*true|rejectUnauthorized\s*:\s*false)"),
        description="TLS/SSL certificate verification is disabled. This allows MITM attacks.",
    ),
    SecurityPattern(
        id="CFG-004", name="Wildcard CORS Origin",
        severity="high", category="Insecure Configuration",
        pattern=re.compile(r"(?i)(allow.origin\s*[=:]\s*['\"]?\*['\"]?|cors\s*\(\s*\{[^}]*origin\s*:\s*['\"]?\*['\"]?)"),
        description="CORS is configured to allow all origins (*). Restrict to known origins.",
    ),
    SecurityPattern(
        id="CFG-005", name="HTTP (Non-HTTPS) URL Hardcoded",
        severity="medium", category="Insecure Configuration",
        pattern=re.compile(r"http://(?!localhost|127\.0\.0\.1|0\.0\.0\.0|example\.com)[a-zA-Z0-9\-._]+"),
        description="Non-HTTPS URL detected. All production traffic should use HTTPS.",
    ),
    # --- High: Dangerous Functions & Patterns ---
    SecurityPattern(
        id="FN-001", name="Direct OS Shell Command Execution",
        severity="high", category="Dangerous Functions",
        pattern=re.compile(r"(?i)(os\.system\s*\(|subprocess\.call\s*\(|subprocess\.Popen\s*\()"),
        description="Direct shell command execution detected. Avoid if user input flows into this call (Command Injection risk).",
    ),
    SecurityPattern(
        id="FN-002", name="Eval / Exec with Dynamic Input",
        severity="critical", category="Dangerous Functions",
        pattern=re.compile(r"\beval\s*\(|\bexec\s*\("),
        description="Use of eval() or exec() detected. These are extremely dangerous with user-controlled input.",
        false_positive_note="Verify the argument is a hardcoded string and not derived from user input.",
    ),
    SecurityPattern(
        id="FN-003", name="Weak Hashing Algorithm",
        severity="critical", category="Dangerous Functions",
        pattern=re.compile(r"(?i)(hashlib\.md5|hashlib\.sha1|MD5\s*\(|SHA1\s*\(|DigestUtils\.md5|MessageDigest\.getInstance\(['\"]MD5|MessageDigest\.getInstance\(['\"]SHA-1)"),
        description="Weak hashing algorithm (MD5 or SHA-1) detected. Use SHA-256 or stronger.",
    ),
    SecurityPattern(
        id="FN-004", name="Deserialization of Untrusted Data",
        severity="critical", category="Dangerous Functions",
        pattern=re.compile(r"(?i)(pickle\.loads\s*\(|pickle\.load\s*\(|yaml\.load\s*\([^,)]*\)|ObjectInputStream)"),
        description="Deserialization of potentially untrusted data detected. This can lead to RCE.",
        false_positive_note="yaml.load is safe only if using yaml.safe_load. Verify the code.",
    ),
    SecurityPattern(
        id="FN-005", name="SQL String Concatenation (Potential SQLi)",
        severity="high", category="Dangerous Functions",
        pattern=re.compile(r"(?i)(execute\s*\(\s*['\"].*\+|execute\s*\(\s*f['\"])"),
        description="Potential SQL query built via string concatenation. Use parameterized queries.",
        false_positive_note="Review to confirm the concatenated value originates from user input.",
    ),
]

# ---------------------------------------------------------------------------
# Ignore list: These lines match a pattern but are known safe contexts
# ---------------------------------------------------------------------------
DEFAULT_IGNORE_STRINGS = [
    "your-api-key-here", "YOUR_API_KEY", "REPLACE_ME", "placeholder",
    "example.com", "test_", "mock_", "fake_", "# noqa", "# nosec",
    "localhost", "127.0.0.1",
]


@dataclass
class Finding:
    """Represents a single scanner finding."""
    file_path: str
    line_number: int
    line_content: str
    pattern: SecurityPattern
    snippet: str = field(default="")


def should_skip_file(file_path: Path) -> bool:
    """
    Determines if a file should be excluded from scanning.

    Parameters:
        file_path: The file path to evaluate.

    Returns:
        True if the file should be skipped, False otherwise.
    """
    if file_path.suffix.lower() not in SCANNABLE_EXTENSIONS:
        return True
    for part in file_path.parts:
        if part in SKIP_DIRS:
            return True
    return False


def is_ignored_line(line: str, extra_ignores: List[str]) -> bool:
    """
    Checks if a line should be suppressed based on known false-positive markers.

    Parameters:
        line: The source code line to evaluate.
        extra_ignores: Additional user-provided ignore strings.

    Returns:
        True if the line should be ignored, False otherwise.
    """
    all_ignores = DEFAULT_IGNORE_STRINGS + extra_ignores
    for token in all_ignores:
        if token.lower() in line.lower():
            return True
    return False


def scan_file(file_path: Path, extra_ignores: List[str], min_severity: str) -> List[Finding]:
    """
    Scans a single file against all enabled security patterns.

    Parameters:
        file_path: The file to scan.
        extra_ignores: Additional ignore strings to apply.
        min_severity: Minimum severity level to report.

    Returns:
        A list of Finding objects for each detected match.
    """
    findings: List[Finding] = []
    min_level = SEVERITY_ORDER.get(min_severity.lower(), 3)

    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except (OSError, PermissionError):
        return findings

    lines = content.splitlines()
    for line_num, line in enumerate(lines, start=1):
        if is_ignored_line(line, extra_ignores):
            continue
        for sec_pattern in PATTERNS:
            if SEVERITY_ORDER.get(sec_pattern.severity, 3) > min_level:
                continue
            if sec_pattern.pattern.search(line):
                findings.append(Finding(
                    file_path=str(file_path),
                    line_number=line_num,
                    line_content=line.strip(),
                    pattern=sec_pattern,
                ))
    return findings


def scan_directory(root_dir: Path, extra_ignores: List[str], min_severity: str) -> List[Finding]:
    """
    Recursively scans all eligible files in a directory tree.

    Parameters:
        root_dir: The root directory to start scanning from.
        extra_ignores: Additional ignore strings to apply.
        min_severity: Minimum severity level to report.

    Returns:
        A combined list of all Finding objects from every scanned file.
    """
    all_findings: List[Finding] = []
    for file_path in root_dir.rglob("*"):
        if file_path.is_file() and not should_skip_file(file_path):
            all_findings.extend(scan_file(file_path, extra_ignores, min_severity))
    return all_findings


def format_report(findings: List[Finding], root_dir: Path) -> str:
    """
    Formats the list of findings into a human-readable security report.

    Parameters:
        findings: The list of all detected findings.
        root_dir: The root directory used for relative path display.

    Returns:
        A formatted multi-line string report.
    """
    if not findings:
        return "✅ No issues detected. The scan completed without findings.\n"

    severity_icons = {
        "critical": "🔴 CRITICAL",
        "high": "🟠 HIGH",
        "medium": "🟡 MEDIUM",
        "low": "🔵 LOW",
    }

    lines = [
        "=" * 70,
        "  SECURITY SCANNER REPORT",
        f"  Root Directory: {root_dir}",
        f"  Total Findings: {len(findings)}",
        "=" * 70,
        "",
    ]

    grouped: dict = {}
    for finding in findings:
        sev = finding.pattern.severity
        grouped.setdefault(sev, []).append(finding)

    for severity in ["critical", "high", "medium", "low"]:
        if severity not in grouped:
            continue
        lines.append(f"\n{severity_icons[severity]} ({len(grouped[severity])} finding(s))")
        lines.append("-" * 70)
        for f in grouped[severity]:
            rel_path = Path(f.file_path).relative_to(root_dir)
            lines.append(f"  [{f.pattern.id}] {f.pattern.name}")
            lines.append(f"  File    : {rel_path}:{f.line_number}")
            lines.append(f"  Line    : {f.line_content[:120]}")
            lines.append(f"  Detail  : {f.pattern.description}")
            if f.pattern.false_positive_note:
                lines.append(f"  Note    : ⚠️  {f.pattern.false_positive_note}")
            lines.append("")

    lines.append("=" * 70)
    lines.append("⚠️  Review each finding carefully before marking as false positive.")
    lines.append("    Run with --severity high to filter low-priority results.")
    lines.append("=" * 70)
    return "\n".join(lines)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """
    Parses command-line arguments for the scanner.

    Parameters:
        argv: Optional list of argument strings (defaults to sys.argv).

    Returns:
        Parsed Namespace object with all argument values.
    """
    parser = argparse.ArgumentParser(
        prog="general_security_scanner",
        description="Language-agnostic static security scanner for detecting secrets, "
                    "insecure configurations, and dangerous code patterns.",
    )
    parser.add_argument("--dir", required=True, help="Path to the project directory to scan.")
    parser.add_argument("--output", default=None, help="Path to write the report. Defaults to stdout.")
    parser.add_argument(
        "--severity",
        default="low",
        choices=["critical", "high", "medium", "low"],
        help="Minimum severity level to report (default: low).",
    )
    parser.add_argument(
        "--ignore",
        default="",
        help="Comma-separated list of additional strings to suppress in results.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    """
    Main entry point for the security scanner.

    Parameters:
        argv: Optional argument list for testing.

    Returns:
        Exit code: 0 if no findings, 1 if findings were detected.
    """
    args = parse_args(argv)
    root_dir = Path(args.dir).resolve()

    if not root_dir.is_dir():
        print(f"❌ Error: '{root_dir}' is not a valid directory.", file=sys.stderr)
        return 2

    extra_ignores = [s.strip() for s in args.ignore.split(",") if s.strip()]

    print(f"🔍 Scanning directory: {root_dir}", file=sys.stderr)
    findings = scan_directory(root_dir, extra_ignores, args.severity)
    report = format_report(findings, root_dir)

    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
        print(f"📄 Report written to: {args.output}", file=sys.stderr)
    else:
        print(report)

    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
