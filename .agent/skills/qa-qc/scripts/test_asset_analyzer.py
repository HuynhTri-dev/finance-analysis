#!/usr/bin/env python3
"""
name: test_asset_analyzer.py
description: Multi-language static AST analyzer for automated test code quality assessment.
             Scans Dart, TypeScript/JavaScript, and Python test files to extract
             quantitative metrics: assertion count, assertion density, AAA pattern
             compliance, zero-assertion detection, and test smell identification.
             Outputs results as structured JSON for consumption by the QA-QC agent.

Usage:
    python3 test_asset_analyzer.py --path <file_or_directory> [--format json|table] [--lang auto|dart|ts|py]

Parameters:
    --path     : Path to a single test file or directory to scan recursively.
    --format   : Output format. 'json' for machine-readable (default), 'table' for human-readable.
    --lang     : Language hint. 'auto' detects by file extension (default).
    --threshold: Assertion Density Index warning threshold (default: 1.0).
    --verbose  : Print per-assertion details in addition to summary.

Returns:
    JSON object (or formatted table) with:
      - summary: overall metrics (total_tests, total_assertions, adi, zero_assert_count)
      - files: per-file breakdown
      - violations: list of AAA violations and test smells with file:line references
"""

import ast
import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class TestFunction:
    """
    Represents a single test function extracted from a source file.

    Attributes:
        name         : The function/test name.
        file         : Absolute path of the source file.
        start_line   : First line number of the test block.
        end_line     : Last line number of the test block.
        language     : Detected language ('dart', 'typescript', 'python').
        assertion_count   : Number of meaningful assertions found.
        has_arrange  : Whether an ARRANGE phase was detected.
        has_act      : Whether an ACT phase was detected.
        has_assert   : Whether an ASSERT phase was detected.
        aaa_violation: The AAA violation code, if any.
        smells       : List of test smell names detected.
        trivial_assertions: Count of trivial/weak assertions.
    """
    name: str
    file: str
    start_line: int
    end_line: int
    language: str
    assertion_count: int = 0
    has_arrange: bool = False
    has_act: bool = False
    has_assert: bool = False
    aaa_violation: Optional[str] = None
    smells: list = field(default_factory=list)
    trivial_assertions: int = 0


@dataclass
class FileAnalysisResult:
    """
    Aggregated analysis result for a single test file.

    Attributes:
        file         : Absolute path of the analyzed file.
        language     : Detected programming language.
        total_tests  : Total number of test functions in the file.
        total_assertions   : Total meaningful assertions across all tests.
        zero_assert_tests  : Tests with zero assertions (The Liar pattern).
        aaa_violations     : List of AAA violation details.
        smells             : List of test smells with location info.
        assertion_density  : ADI = total_assertions / total_tests.
        test_functions     : Detailed per-test breakdown.
    """
    file: str
    language: str
    total_tests: int = 0
    total_assertions: int = 0
    zero_assert_tests: int = 0
    aaa_violations: list = field(default_factory=list)
    smells: list = field(default_factory=list)
    assertion_density: float = 0.0
    test_functions: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# Language Detection
# ---------------------------------------------------------------------------

def detect_language(file_path: str) -> Optional[str]:
    """
    Detects the programming language from file extension.

    Args:
        file_path: Absolute or relative path to the source file.

    Returns:
        Language string ('dart', 'typescript', 'python') or None if unsupported.
    """
    ext = Path(file_path).suffix.lower()
    mapping = {
        '.dart': 'dart',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.py': 'python',
    }
    return mapping.get(ext)


def is_test_file(file_path: str) -> bool:
    """
    Heuristically determines whether a file is a test file.

    Applies naming convention checks common across ecosystems:
    - Python: prefixed with test_ or suffixed with _test.py
    - Dart: suffixed with _test.dart
    - TypeScript/JS: suffixed with .test.ts, .spec.ts, .test.js, .spec.js

    Args:
        file_path: Path to the source file.

    Returns:
        True if the file appears to be a test file.
    """
    name = Path(file_path).name.lower()
    patterns = [
        r'test_.*\.py$',
        r'.*_test\.py$',
        r'.*_test\.dart$',
        r'.*\.test\.(ts|tsx|js|jsx)$',
        r'.*\.spec\.(ts|tsx|js|jsx)$',
    ]
    return any(re.match(p, name) for p in patterns)


# ---------------------------------------------------------------------------
# Python Analyzer (AST-based)
# ---------------------------------------------------------------------------

# Assertion function/method names considered meaningful in Python
PYTHON_MEANINGFUL_ASSERT_NAMES = {
    'assertEqual', 'assertNotEqual', 'assertIs', 'assertIsNot',
    'assertTrue', 'assertFalse', 'assertIn', 'assertNotIn',
    'assertIsNone', 'assertIsNotNone', 'assertRaises', 'assertRaisesRegex',
    'assertAlmostEqual', 'assertNotAlmostEqual', 'assertGreater',
    'assertGreaterEqual', 'assertLess', 'assertLessEqual',
    'assert_called', 'assert_called_once', 'assert_called_with',
    'assert_called_once_with', 'assert_any_call', 'assert_has_calls',
    'assert_not_called', 'assert_awaited', 'assert_awaited_once',
    'assert_awaited_with', 'assert_awaited_once_with', 'assert_any_await',
    'assert_has_awaits', 'assert_not_awaited', 'raises',
}

# Trivial assertion patterns (regex on raw assertion text)
PYTHON_TRIVIAL_PATTERNS = [
    r'^assert\s+\w+\s+is\s+not\s+None$',
    r'^assert\s+isinstance\(\w+,\s*\w+\)$',
    r'^assert\s+len\(\w+\)\s*[>!]=?\s*0$',
    r'^assert\s+\w+$',                          # assert result (truthiness only)
]


def _is_trivial_assert(node: ast.stmt) -> bool:
    """
    Checks if a Python assert statement is a trivial/weak assertion.

    Args:
        node: An AST statement node of type ast.Assert.

    Returns:
        True if the assertion is considered trivially weak.
    """
    try:
        src = ast.unparse(node)
    except Exception:
        return False
    for pattern in PYTHON_TRIVIAL_PATTERNS:
        if re.match(pattern, src.strip(), re.IGNORECASE):
            return True
    return False


def _has_silent_catcher(func_node: ast.FunctionDef) -> bool:
    """
    Detects a 'silent catcher' test smell: a try/except block that swallows
    exceptions without re-asserting any outcome.

    Args:
        func_node: An AST FunctionDef node representing the test function.

    Returns:
        True if a silent catcher pattern is detected.
    """
    for node in ast.walk(func_node):
        if isinstance(node, ast.ExceptHandler):
            # Handler body contains only 'pass' or empty
            non_pass = [s for s in node.body if not isinstance(s, ast.Pass)]
            if not non_pass:
                return True
    return False


def analyze_python_file(file_path: str) -> FileAnalysisResult:
    """
    Performs AST-based static analysis on a Python test file.

    Extracts all test functions (prefixed 'test_'), counts assertions,
    detects AAA violations, and identifies test smells.

    Args:
        file_path: Absolute path to the Python test file.

    Returns:
        A FileAnalysisResult with per-function metrics.
    """
    result = FileAnalysisResult(file=file_path, language='python')
    source = Path(file_path).read_text(encoding='utf-8')

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        result.smells.append({'smell': 'PARSE_ERROR', 'detail': str(e), 'line': 0})
        return result

    lines = source.splitlines()

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not node.name.startswith('test'):
            continue

        tf = TestFunction(
            name=node.name,
            file=file_path,
            start_line=node.lineno,
            end_line=node.end_lineno or node.lineno,
            language='python',
        )

        meaningful = 0
        trivial = 0
        has_act_candidate = False

        for child in ast.walk(node):
            # Count assert statements
            if isinstance(child, ast.Assert):
                if _is_trivial_assert(child):
                    trivial += 1
                else:
                    meaningful += 1

            # Count pytest.raises or unittest assertRaises calls
            if isinstance(child, ast.Call):
                func_name = ''
                if isinstance(child.func, ast.Attribute):
                    func_name = child.func.attr
                elif isinstance(child.func, ast.Name):
                    func_name = child.func.id
                if func_name in PYTHON_MEANINGFUL_ASSERT_NAMES:
                    meaningful += 1
                # Detect ACT candidate: any function call that isn't assert/setup
                if func_name not in ('setUp', 'tearDown', 'Mock', 'patch', 'fixture'):
                    has_act_candidate = True

        # Check for AAA phase markers in comments
        func_src_lines = lines[node.lineno - 1:node.end_lineno]
        has_arrange_comment = any('arrange' in l.lower() for l in func_src_lines)
        has_act_comment = any('# act' in l.lower() for l in func_src_lines)
        has_assert_comment = any('# assert' in l.lower() for l in func_src_lines)

        tf.assertion_count = meaningful
        tf.trivial_assertions = trivial
        tf.has_arrange = has_arrange_comment
        tf.has_act = has_act_comment or has_act_candidate
        tf.has_assert = meaningful > 0

        # Classify AAA violations
        if meaningful == 0:
            tf.aaa_violation = 'AAA_MISSING_ASSERT'
            tf.smells.append('The Liar')
            result.zero_assert_tests += 1
            result.aaa_violations.append({
                'test': tf.name, 'file': file_path, 'line': tf.start_line,
                'violation': 'AAA_MISSING_ASSERT'
            })

        # Detect silent catcher
        if _has_silent_catcher(node):
            tf.smells.append('The Silent Catcher')
            result.smells.append({
                'smell': 'The Silent Catcher', 'test': tf.name,
                'file': file_path, 'line': tf.start_line
            })

        result.total_assertions += meaningful
        result.total_tests += 1
        result.test_functions.append(asdict(tf))

    result.assertion_density = (
        round(result.total_assertions / result.total_tests, 2)
        if result.total_tests > 0 else 0.0
    )
    return result


# ---------------------------------------------------------------------------
# Dart / TypeScript / JavaScript Analyzers (Regex-based)
# ---------------------------------------------------------------------------

# Assertion patterns by language
LANG_ASSERTION_PATTERNS = {
    'dart': [
        r'\bexpect\s*\(',
        r'\bexpectLater\s*\(',
        r'\bthrowsA\s*\(',
        r'\bmatches\s*\(',
        r'\bpredicate\s*\(',
    ],
    'typescript': [
        r'\bexpect\s*\(',
        r'\bshould\.',
        r'\bassert\.',
        r'\btoThrow\b',
        r'\btoEqual\b',
        r'\btoBe\b',
    ],
    'javascript': [
        r'\bexpect\s*\(',
        r'\bshould\.',
        r'\bassert\.',
        r'\btoThrow\b',
        r'\btoEqual\b',
        r'\btoBe\b',
    ],
}

LANG_TRIVIAL_PATTERNS = {
    'dart': [
        r'expect\s*\(\s*\w+,\s*isNotNull\s*\)',
        r'expect\s*\(\s*\w+,\s*isNotEmpty\s*\)',
        r'expect\s*\(\s*\w+,\s*isTrue\s*\)',
        r'expect\s*\(\s*\w+,\s*isFalse\s*\)',
    ],
    'typescript': [
        r'expect\s*\(\s*\w+\s*\)\.toBeDefined\s*\(\s*\)',
        r'expect\s*\(\s*\w+\s*\)\.toBeTruthy\s*\(\s*\)',
        r'expect\s*\(\s*\w+\s*\)\.not\.toBeNull\s*\(\s*\)',
    ],
    'javascript': [
        r'expect\s*\(\s*\w+\s*\)\.toBeDefined\s*\(\s*\)',
        r'expect\s*\(\s*\w+\s*\)\.toBeTruthy\s*\(\s*\)',
    ],
}

# Regex patterns to identify test function/block starts
LANG_TEST_BLOCK_PATTERNS = {
    'dart': r"^\s*(test|testWidgets)\s*\(\s*['\"](.+?)['\"]",
    'typescript': r"^\s*(it|test)\s*\(\s*['\"`](.+?)['\"`]",
    'javascript': r"^\s*(it|test)\s*\(\s*['\"`](.+?)['\"`]",
}

SILENT_CATCHER_PATTERNS = {
    'dart': r'catch\s*\(.*?\)\s*\{?\s*\}',
    'typescript': r'catch\s*\(.*?\)\s*\{\s*\}',
    'javascript': r'catch\s*\(.*?\)\s*\{\s*\}',
    'python': None,  # handled by AST
}


def analyze_generic_file(file_path: str, language: str) -> FileAnalysisResult:
    """
    Performs regex-based static analysis for Dart and TypeScript/JavaScript files.

    Scans for test blocks, counts assertions, checks for AAA comment markers,
    and identifies common test smells using pattern matching.

    Args:
        file_path: Absolute path to the source file.
        language : Detected language ('dart', 'typescript', 'javascript').

    Returns:
        A FileAnalysisResult with per-function metrics.
    """
    result = FileAnalysisResult(file=file_path, language=language)
    source = Path(file_path).read_text(encoding='utf-8')
    lines = source.splitlines()

    test_pattern = re.compile(LANG_TEST_BLOCK_PATTERNS.get(language, r'^\s*test\s*\('))
    assert_patterns = [re.compile(p) for p in LANG_ASSERTION_PATTERNS.get(language, [])]
    trivial_patterns = [re.compile(p) for p in LANG_TRIVIAL_PATTERNS.get(language, [])]
    silent_pattern = SILENT_CATCHER_PATTERNS.get(language)
    silent_re = re.compile(silent_pattern) if silent_pattern else None

    i = 0
    while i < len(lines):
        line = lines[i]
        m = test_pattern.match(line)
        if m:
            test_name = m.group(2) if m.lastindex >= 2 else f'test_at_line_{i+1}'
            start_line = i + 1
            # Find closing brace heuristically (track depth)
            depth = line.count('{') - line.count('}')
            j = i + 1
            test_body_lines = [line]
            while j < len(lines) and (depth > 0 or j == i + 1):
                test_body_lines.append(lines[j])
                depth += lines[j].count('{') - lines[j].count('}')
                j += 1
            end_line = j

            body = '\n'.join(test_body_lines)
            body_lower = body.lower()

            # Count assertions
            meaningful = 0
            trivial = 0
            for ap in assert_patterns:
                for al in test_body_lines[1:]:
                    if ap.search(al):
                        # Check if trivial
                        is_triv = any(tp.search(al) for tp in trivial_patterns)
                        if is_triv:
                            trivial += 1
                        else:
                            meaningful += 1

            # Detect AAA comment markers
            has_arrange = 'arrange' in body_lower
            has_act = '// act' in body_lower or '/* act' in body_lower
            has_assert = meaningful > 0

            tf = TestFunction(
                name=test_name, file=file_path,
                start_line=start_line, end_line=end_line,
                language=language,
                assertion_count=meaningful,
                trivial_assertions=trivial,
                has_arrange=has_arrange,
                has_act=has_act,
                has_assert=has_assert,
            )

            # AAA violation classification
            if meaningful == 0:
                tf.aaa_violation = 'AAA_MISSING_ASSERT'
                tf.smells.append('The Liar')
                result.zero_assert_tests += 1
                result.aaa_violations.append({
                    'test': test_name, 'file': file_path,
                    'line': start_line, 'violation': 'AAA_MISSING_ASSERT'
                })

            # Detect silent catcher
            if silent_re and silent_re.search(body):
                tf.smells.append('The Silent Catcher')
                result.smells.append({
                    'smell': 'The Silent Catcher', 'test': test_name,
                    'file': file_path, 'line': start_line
                })

            result.total_assertions += meaningful
            result.total_tests += 1
            result.test_functions.append(asdict(tf))
            i = j
            continue
        i += 1

    result.assertion_density = (
        round(result.total_assertions / result.total_tests, 2)
        if result.total_tests > 0 else 0.0
    )
    return result


# ---------------------------------------------------------------------------
# Dispatcher & Directory Walker
# ---------------------------------------------------------------------------

def analyze_file(file_path: str) -> Optional[FileAnalysisResult]:
    """
    Dispatches file analysis to the appropriate language analyzer.

    Args:
        file_path: Path to the test source file.

    Returns:
        FileAnalysisResult if the file is a supported test file, else None.
    """
    lang = detect_language(file_path)
    if not lang:
        return None
    if not is_test_file(file_path):
        return None

    if lang == 'python':
        return analyze_python_file(file_path)
    elif lang in ('dart', 'typescript', 'javascript'):
        return analyze_generic_file(file_path, lang)
    return None


def walk_directory(directory: str) -> list[FileAnalysisResult]:
    """
    Recursively walks a directory and analyzes all test files found.

    Skips non-test files, build artifacts (build/, dist/, node_modules/,
    .dart_tool/), and hidden directories.

    Args:
        directory: Absolute or relative path to the root directory.

    Returns:
        List of FileAnalysisResult objects, one per analyzed file.
    """
    skip_dirs = {'build', 'dist', 'node_modules', '.dart_tool', '.git',
                 '__pycache__', '.pytest_cache', 'coverage'}
    results = []
    for root, dirs, files in os.walk(directory):
        # Prune skipped directories in-place
        dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]
        for fname in files:
            fpath = os.path.join(root, fname)
            result = analyze_file(fpath)
            if result:
                results.append(result)
    return results


# ---------------------------------------------------------------------------
# Aggregate Summary Builder
# ---------------------------------------------------------------------------

def build_summary(file_results: list[FileAnalysisResult]) -> dict:
    """
    Aggregates per-file analysis results into a portfolio-level summary.

    Args:
        file_results: List of FileAnalysisResult from all analyzed files.

    Returns:
        Dictionary with aggregate metrics:
          - total_files, total_tests, total_assertions
          - portfolio_adi, zero_assert_count, aaa_violation_count
          - overall_grade (A/B/C/D/F based on ADI and zero-assert ratio)
    """
    total_tests = sum(r.total_tests for r in file_results)
    total_assertions = sum(r.total_assertions for r in file_results)
    zero_asserts = sum(r.zero_assert_tests for r in file_results)
    aaa_violations = sum(len(r.aaa_violations) for r in file_results)
    all_smells = []
    for r in file_results:
        all_smells.extend(r.smells)

    adi = round(total_assertions / total_tests, 2) if total_tests > 0 else 0.0
    zero_ratio = (zero_asserts / total_tests) if total_tests > 0 else 0.0

    # Heuristic grade
    if adi >= 1.0 and zero_ratio == 0:
        grade = 'A'
    elif adi >= 0.8 and zero_ratio < 0.05:
        grade = 'B'
    elif adi >= 0.5 and zero_ratio < 0.15:
        grade = 'C'
    elif adi >= 0.2:
        grade = 'D'
    else:
        grade = 'F'

    return {
        'total_files': len(file_results),
        'total_tests': total_tests,
        'total_assertions': total_assertions,
        'portfolio_adi': adi,
        'zero_assert_count': zero_asserts,
        'zero_assert_ratio_pct': round(zero_ratio * 100, 1),
        'aaa_violation_count': aaa_violations,
        'smell_count': len(all_smells),
        'overall_grade': grade,
    }


# ---------------------------------------------------------------------------
# Output Formatters
# ---------------------------------------------------------------------------

def format_table(summary: dict, file_results: list[FileAnalysisResult]) -> str:
    """
    Formats analysis results as a human-readable ASCII table.

    Args:
        summary     : Aggregate summary dict from build_summary().
        file_results: Per-file FileAnalysisResult list.

    Returns:
        Multi-line string suitable for terminal display.
    """
    lines = []
    lines.append('=' * 70)
    lines.append('  QA-QC Test Asset Analyzer — Results Summary')
    lines.append('=' * 70)
    lines.append(f"  Total Files Analyzed   : {summary['total_files']}")
    lines.append(f"  Total Test Functions   : {summary['total_tests']}")
    lines.append(f"  Total Assertions       : {summary['total_assertions']}")
    lines.append(f"  Portfolio ADI          : {summary['portfolio_adi']:.2f}  (Target: 1.0 – 3.0)")
    lines.append(f"  Zero-Assertion Tests   : {summary['zero_assert_count']} ({summary['zero_assert_ratio_pct']}%)")
    lines.append(f"  AAA Violations         : {summary['aaa_violation_count']}")
    lines.append(f"  Test Smells Detected   : {summary['smell_count']}")
    lines.append(f"  Overall Grade (Heuristic): {summary['overall_grade']}")
    lines.append('')
    lines.append(f"  {'FILE':<45} {'TESTS':>5} {'ASSERTS':>7} {'ADI':>5} {'LIAR':>5} {'GRADE':>6}")
    lines.append('  ' + '-' * 68)
    for r in file_results:
        grade_char = (
            'A' if r.assertion_density >= 1.0 and r.zero_assert_tests == 0 else
            'B' if r.assertion_density >= 0.8 else
            'C' if r.assertion_density >= 0.5 else
            'D' if r.assertion_density >= 0.2 else 'F'
        )
        short_path = os.path.basename(r.file)
        lines.append(
            f"  {short_path:<45} {r.total_tests:>5} {r.total_assertions:>7} "
            f"{r.assertion_density:>5.2f} {r.zero_assert_tests:>5} {grade_char:>6}"
        )
    lines.append('=' * 70)
    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def main():
    """
    CLI entry point for the QA-QC Test Asset Analyzer.

    Parses arguments, walks the target path, runs analysis, and outputs
    results to stdout in the requested format (JSON or ASCII table).

    Exit codes:
        0 — Success, no critical issues found.
        1 — Critical issues detected (zero-assertion tests found).
        2 — Input path error.
    """
    parser = argparse.ArgumentParser(
        prog='test_asset_analyzer',
        description=(
            'QA-QC Test Asset Analyzer — Static analysis for Dart, TypeScript, '
            'JavaScript, and Python test files. Outputs assertion density, AAA '
            'compliance, and test smell detection.'
        ),
    )
    parser.add_argument(
        '--path', required=True,
        help='Path to a single test file or a directory to scan recursively.'
    )
    parser.add_argument(
        '--format', choices=['json', 'table'], default='json',
        help='Output format: "json" for machine-readable (default), "table" for human-readable.'
    )
    parser.add_argument(
        '--lang', choices=['auto', 'dart', 'typescript', 'javascript', 'python'],
        default='auto',
        help='Language hint. "auto" detects by file extension (default).'
    )
    parser.add_argument(
        '--threshold', type=float, default=1.0,
        help='Assertion Density Index warning threshold (default: 1.0).'
    )
    parser.add_argument(
        '--verbose', action='store_true',
        help='Include per-test-function details in output.'
    )

    args = parser.parse_args()
    target = Path(args.path)

    if not target.exists():
        print(f'[ERROR] Path not found: {args.path}', file=sys.stderr)
        sys.exit(2)

    # Collect and analyze files
    if target.is_file():
        result = analyze_file(str(target))
        file_results = [result] if result else []
    else:
        file_results = walk_directory(str(target))

    if not file_results:
        print('[INFO] No test files found or supported at the given path.', file=sys.stderr)
        sys.exit(0)

    summary = build_summary(file_results)

    if args.format == 'table':
        print(format_table(summary, file_results))
    else:
        output = {'summary': summary}
        if args.verbose:
            output['files'] = [asdict(r) for r in file_results]
        else:
            output['files'] = [
                {
                    'file': r.file,
                    'language': r.language,
                    'total_tests': r.total_tests,
                    'total_assertions': r.total_assertions,
                    'assertion_density': r.assertion_density,
                    'zero_assert_tests': r.zero_assert_tests,
                    'aaa_violations': r.aaa_violations,
                    'smells': r.smells,
                }
                for r in file_results
            ]
        print(json.dumps(output, indent=2))

    # Exit with code 1 if critical issues exist
    if summary['zero_assert_count'] > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()
