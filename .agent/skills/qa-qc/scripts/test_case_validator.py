#!/usr/bin/env python3
"""
name: test_case_validator.py
description: ISO/IEC/IEEE 29119-3 compliance linter and validator for manual test
             case documents. Supports Markdown tables, CSV, and JSON formats.
             Checks structural completeness (mandatory fields), detects orphan tests
             and uncovered requirements, and flags BVA/EP annotation gaps.
             Outputs a structured validation report as JSON or formatted table.

Usage:
    python3 test_case_validator.py --path <file_or_directory> [--format json|table]
                                   [--requirements <req_file>] [--strict]

Parameters:
    --path         : Path to a test case file (MD, CSV, JSON) or directory.
    --format       : Output format. 'json' (default) or 'table'.
    --requirements : Optional path to a requirements file (JSON or CSV) for RTM.
    --strict       : Treat Major defects as Critical (fail the process).

Returns:
    JSON object with:
      - summary: counts of total_cases, compliant, critical_defects, major_defects
      - cases: per-test-case breakdown with field compliance and defects
      - rtm: coverage report if --requirements provided
      - recommendations: list of actionable fix suggestions
"""

import argparse
import csv
import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Mandatory fields as per ISO/IEC/IEEE 29119-3
MANDATORY_FIELDS = [
    'id',
    'title',
    'preconditions',
    'steps',
    'expected_results',
    'traceability',
]

# Canonical field aliases — maps variations in column naming to canonical names
FIELD_ALIASES = {
    'id': ['id', 'test_id', 'test case id', 'tc_id', 'case id', 'testcaseid'],
    'title': ['title', 'name', 'test name', 'objective', 'description', 'summary'],
    'preconditions': ['preconditions', 'pre-conditions', 'pre_conditions',
                      'prerequisites', 'setup', 'initial state'],
    'steps': ['steps', 'test steps', 'actions', 'procedure', 'step description'],
    'expected_results': ['expected_results', 'expected result', 'expected results',
                         'expected outcome', 'pass criteria', 'acceptance criteria'],
    'traceability': ['traceability', 'requirement', 'requirement id', 'req_id',
                     'user story', 'feature id', 'linked requirement'],
}

# Patterns that indicate vague expected results
VAGUE_RESULT_PATTERNS = [
    r'\bcorrectly\b', r'\bproperly\b', r'\bsuccessfully\b',
    r'\bworks?\b', r'\bok\b', r'\bfine\b', r'\bappropriately\b',
    r'\bshould work\b', r'\bno errors?\b',
]

# BVA annotation keywords
BVA_KEYWORDS = ['min-1', 'min+1', 'max-1', 'max+1', 'boundary', 'bva', 'edge case',
                 'lower bound', 'upper bound', 'minimum', 'maximum']

# EP annotation keywords
EP_KEYWORDS = ['valid partition', 'invalid partition', 'ep', 'equivalence',
               'positive case', 'negative case', 'invalid input', 'reject']


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class TestCaseDefect:
    """
    Represents a single defect found in a test case.

    Attributes:
        case_id  : The test case ID where the defect was found.
        field    : The ISO 29119-3 field affected.
        severity : 'Critical' | 'Major' | 'Minor'.
        message  : Human-readable description of the defect.
    """
    case_id: str
    field: str
    severity: str
    message: str


@dataclass
class TestCaseResult:
    """
    Validation result for a single test case.

    Attributes:
        case_id           : The resolved test case ID.
        title             : The resolved test case title.
        is_compliant      : True if no Critical defects are found.
        missing_fields    : Fields entirely absent from the test case.
        defects           : List of TestCaseDefect objects.
        has_bva_annotation: Whether BVA annotation keywords were found.
        has_ep_annotation : Whether EP annotation keywords were found.
        traceability_tag  : The requirement ID linked, if any.
    """
    case_id: str
    title: str
    is_compliant: bool = True
    missing_fields: list = field(default_factory=list)
    defects: list = field(default_factory=list)
    has_bva_annotation: bool = False
    has_ep_annotation: bool = False
    traceability_tag: Optional[str] = None


@dataclass
class RTMResult:
    """
    Requirement Traceability Matrix result.

    Attributes:
        total_requirements : Total requirement IDs in requirements document.
        covered            : Requirement IDs that have at least one linked test.
        uncovered          : Requirement IDs with no linked test cases.
        orphan_tests       : Test case IDs with no matching requirement.
        coverage_pct       : Percentage of requirements covered.
    """
    total_requirements: int = 0
    covered: list = field(default_factory=list)
    uncovered: list = field(default_factory=list)
    orphan_tests: list = field(default_factory=list)
    coverage_pct: float = 0.0


# ---------------------------------------------------------------------------
# Field Normalization
# ---------------------------------------------------------------------------

def normalize_field_name(raw_name: str) -> Optional[str]:
    """
    Maps a raw column header name to the canonical ISO 29119-3 field name.

    Args:
        raw_name: The raw column header string from the test document.

    Returns:
        Canonical field name string, or None if no alias matches.
    """
    normalized = raw_name.strip().lower().replace('_', ' ').replace('-', ' ')
    for canonical, aliases in FIELD_ALIASES.items():
        if normalized in aliases:
            return canonical
    return None


def build_field_map(headers: list[str]) -> dict:
    """
    Constructs a mapping from canonical field names to the actual column header.

    Args:
        headers: List of raw column header strings.

    Returns:
        Dictionary of {canonical_field: raw_header_string} for matched fields.
    """
    field_map = {}
    for h in headers:
        canonical = normalize_field_name(h)
        if canonical and canonical not in field_map:
            field_map[canonical] = h
    return field_map


# ---------------------------------------------------------------------------
# Defect Detectors
# ---------------------------------------------------------------------------

def check_vague_expected_result(text: str) -> bool:
    """
    Checks if an expected result contains vague, non-measurable language.

    Args:
        text: The expected result text to evaluate.

    Returns:
        True if vague patterns are detected.
    """
    for pattern in VAGUE_RESULT_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def check_bva_annotation(text: str) -> bool:
    """
    Detects BVA-related annotation keywords in test case fields.

    Args:
        text: Combined text of test case fields (title + steps + notes).

    Returns:
        True if BVA keywords are found.
    """
    combined = text.lower()
    return any(kw in combined for kw in BVA_KEYWORDS)


def check_ep_annotation(text: str) -> bool:
    """
    Detects EP-related annotation keywords in test case fields.

    Args:
        text: Combined text of test case fields.

    Returns:
        True if EP keywords are found.
    """
    combined = text.lower()
    return any(kw in combined for kw in EP_KEYWORDS)


# ---------------------------------------------------------------------------
# Single Test Case Validator
# ---------------------------------------------------------------------------

def validate_test_case(row: dict, field_map: dict) -> TestCaseResult:
    """
    Validates a single test case row against ISO/IEC/IEEE 29119-3 standards.

    Checks:
    - Presence of all 6 mandatory fields.
    - Quality of Expected Results (not vague).
    - Atomic Test Steps (no multi-action steps).
    - Presence of Traceability Tag.
    - BVA/EP annotations.

    Args:
        row      : Dictionary mapping column headers to cell values.
        field_map: Canonical-to-header mapping from build_field_map().

    Returns:
        A TestCaseResult with all detected defects.
    """
    # Resolve canonical field values
    def get(canonical: str) -> str:
        header = field_map.get(canonical)
        return (row.get(header) or '').strip() if header else ''

    case_id = get('id') or 'UNKNOWN'
    title = get('title') or 'UNKNOWN'
    preconditions = get('preconditions')
    steps = get('steps')
    expected = get('expected_results')
    traceability = get('traceability')

    result = TestCaseResult(case_id=case_id, title=title)
    result.traceability_tag = traceability or None

    # --- Check mandatory field presence ---
    for f in MANDATORY_FIELDS:
        val = get(f)
        if not val:
            result.missing_fields.append(f)
            severity = 'Critical' if f in ('id', 'steps', 'expected_results') else 'Major'
            result.defects.append(TestCaseDefect(
                case_id=case_id, field=f,
                severity=severity,
                message=f"Mandatory field '{f}' is missing or empty."
            ))
            result.is_compliant = False

    # --- Quality checks on Expected Results ---
    if expected and check_vague_expected_result(expected):
        result.defects.append(TestCaseDefect(
            case_id=case_id, field='expected_results',
            severity='Critical',
            message=(
                f"Expected result contains vague language: '{expected[:80]}...'. "
                "Must be specific and measurable (e.g., 'HTTP 200 with body {\"status\": \"ok\"}')."
            )
        ))
        result.is_compliant = False

    # --- Multi-action step detection ---
    if steps:
        step_lines = steps.split('\n')
        for ln, step in enumerate(step_lines, start=1):
            conjunctions = re.findall(r'\b(and then|then|and|&)\b', step, re.IGNORECASE)
            if len(conjunctions) >= 2:
                result.defects.append(TestCaseDefect(
                    case_id=case_id, field='steps',
                    severity='Major',
                    message=(
                        f"Step {ln} appears to contain multiple actions: '{step[:80]}'. "
                        "Each step must contain exactly one atomic action."
                    )
                ))

    # --- BVA/EP annotation detection ---
    combined_text = f"{title} {steps} {expected}"
    result.has_bva_annotation = check_bva_annotation(combined_text)
    result.has_ep_annotation = check_ep_annotation(combined_text)

    return result


# ---------------------------------------------------------------------------
# File Parsers
# ---------------------------------------------------------------------------

def parse_csv_file(file_path: str) -> list[TestCaseResult]:
    """
    Parses a CSV test case file and validates each row.

    Expects the first row to be headers; subsequent rows are test cases.

    Args:
        file_path: Absolute path to the CSV file.

    Returns:
        List of TestCaseResult objects.
    """
    results = []
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        field_map = build_field_map(list(headers))
        for row in reader:
            result = validate_test_case(dict(row), field_map)
            results.append(result)
    return results


def parse_json_file(file_path: str) -> list[TestCaseResult]:
    """
    Parses a JSON test case file and validates each entry.

    Expects a JSON array of test case objects at the top level.

    Args:
        file_path: Absolute path to the JSON file.

    Returns:
        List of TestCaseResult objects.
    """
    data = json.loads(Path(file_path).read_text(encoding='utf-8'))
    if not isinstance(data, list):
        data = data.get('test_cases', data.get('tests', [data]))

    results = []
    for item in data:
        headers = list(item.keys())
        field_map = build_field_map(headers)
        result = validate_test_case(item, field_map)
        results.append(result)
    return results


def parse_markdown_file(file_path: str) -> list[TestCaseResult]:
    """
    Parses a Markdown file containing a test case table.

    Detects GFM (GitHub Flavored Markdown) pipe tables and extracts rows.
    Expects a table with headers in the first row and a separator row.

    Args:
        file_path: Absolute path to the Markdown file.

    Returns:
        List of TestCaseResult objects. Returns empty list if no table found.
    """
    source = Path(file_path).read_text(encoding='utf-8')
    lines = source.splitlines()

    # Find table boundaries
    table_lines = []
    in_table = False
    for line in lines:
        if re.match(r'^\s*\|', line):
            in_table = True
            table_lines.append(line)
        elif in_table:
            break

    if len(table_lines) < 3:  # header + separator + at least 1 row
        return []

    # Parse headers
    header_line = table_lines[0]
    headers = [h.strip() for h in header_line.strip('|').split('|')]
    field_map = build_field_map(headers)

    results = []
    # Skip header row (index 0) and separator row (index 1)
    for row_line in table_lines[2:]:
        cells = [c.strip() for c in row_line.strip('|').split('|')]
        row = dict(zip(headers, cells))
        result = validate_test_case(row, field_map)
        results.append(result)
    return results


def parse_file(file_path: str) -> list[TestCaseResult]:
    """
    Dispatches file parsing to the appropriate format parser.

    Args:
        file_path: Absolute path to the test case document.

    Returns:
        List of TestCaseResult objects, or empty list for unsupported formats.
    """
    ext = Path(file_path).suffix.lower()
    if ext == '.csv':
        return parse_csv_file(file_path)
    elif ext == '.json':
        return parse_json_file(file_path)
    elif ext in ('.md', '.markdown'):
        return parse_markdown_file(file_path)
    return []


# ---------------------------------------------------------------------------
# RTM Analysis
# ---------------------------------------------------------------------------

def build_rtm(
    case_results: list[TestCaseResult],
    req_file: Optional[str]
) -> Optional[RTMResult]:
    """
    Constructs a Requirement Traceability Matrix from test results and a
    requirements document.

    Args:
        case_results: List of validated TestCaseResult objects.
        req_file    : Optional path to a JSON/CSV requirements file.
                      JSON format: [{"id": "REQ-001", "description": "..."}]
                      CSV format: id, description columns.

    Returns:
        RTMResult if req_file is provided, else None.
    """
    if not req_file:
        return None

    # Load requirements
    req_path = Path(req_file)
    requirement_ids = set()
    if req_path.suffix == '.json':
        data = json.loads(req_path.read_text(encoding='utf-8'))
        reqs = data if isinstance(data, list) else data.get('requirements', [])
        for r in reqs:
            rid = r.get('id', r.get('requirement_id', ''))
            if rid:
                requirement_ids.add(rid.strip())
    elif req_path.suffix == '.csv':
        with open(req_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                rid = row.get('id', row.get('requirement_id', '')).strip()
                if rid:
                    requirement_ids.add(rid)

    # Build covered/orphan sets
    covered = set()
    orphan_tests = []
    for tc in case_results:
        tag = tc.traceability_tag
        if tag:
            if tag in requirement_ids:
                covered.add(tag)
            else:
                orphan_tests.append(tc.case_id)
        else:
            orphan_tests.append(tc.case_id)

    uncovered = list(requirement_ids - covered)
    coverage_pct = (
        round(len(covered) / len(requirement_ids) * 100, 1)
        if requirement_ids else 0.0
    )

    return RTMResult(
        total_requirements=len(requirement_ids),
        covered=sorted(covered),
        uncovered=sorted(uncovered),
        orphan_tests=orphan_tests,
        coverage_pct=coverage_pct,
    )


# ---------------------------------------------------------------------------
# Summary Builder
# ---------------------------------------------------------------------------

def build_summary(
    case_results: list[TestCaseResult],
    rtm: Optional[RTMResult]
) -> dict:
    """
    Produces a portfolio-level summary from validated test case results.

    Args:
        case_results: List of TestCaseResult objects.
        rtm         : Optional RTMResult for traceability coverage.

    Returns:
        Dictionary with total counts, compliance rate, defect breakdown, and grade.
    """
    total = len(case_results)
    compliant = sum(1 for r in case_results if r.is_compliant)
    critical = sum(
        sum(1 for d in r.defects if d.severity == 'Critical')
        for r in case_results
    )
    major = sum(
        sum(1 for d in r.defects if d.severity == 'Major')
        for r in case_results
    )
    minor = sum(
        sum(1 for d in r.defects if d.severity == 'Minor')
        for r in case_results
    )
    with_bva = sum(1 for r in case_results if r.has_bva_annotation)
    with_ep = sum(1 for r in case_results if r.has_ep_annotation)

    compliance_pct = round(compliant / total * 100, 1) if total > 0 else 0.0
    bva_pct = round(with_bva / total * 100, 1) if total > 0 else 0.0

    # Heuristic grade
    if compliance_pct >= 95 and critical == 0:
        grade = 'A'
    elif compliance_pct >= 80 and critical <= 2:
        grade = 'B'
    elif compliance_pct >= 65:
        grade = 'C'
    elif compliance_pct >= 50:
        grade = 'D'
    else:
        grade = 'F'

    result = {
        'total_cases': total,
        'compliant_cases': compliant,
        'compliance_pct': compliance_pct,
        'critical_defects': critical,
        'major_defects': major,
        'minor_defects': minor,
        'cases_with_bva_annotation': with_bva,
        'bva_annotation_pct': bva_pct,
        'cases_with_ep_annotation': with_ep,
        'overall_grade': grade,
    }
    if rtm:
        result['rtm'] = {
            'total_requirements': rtm.total_requirements,
            'coverage_pct': rtm.coverage_pct,
            'uncovered_requirements': rtm.uncovered,
            'orphan_tests': rtm.orphan_tests,
        }
    return result


# ---------------------------------------------------------------------------
# Output Formatters
# ---------------------------------------------------------------------------

def format_table_output(
    summary: dict,
    case_results: list[TestCaseResult]
) -> str:
    """
    Formats validation results as a human-readable ASCII table.

    Args:
        summary     : Aggregate summary from build_summary().
        case_results: List of per-test-case results.

    Returns:
        Multi-line formatted string for terminal display.
    """
    lines = []
    lines.append('=' * 72)
    lines.append('  QA-QC Test Case Validator — ISO/IEC/IEEE 29119-3 Compliance Report')
    lines.append('=' * 72)
    lines.append(f"  Total Test Cases     : {summary['total_cases']}")
    lines.append(f"  Compliant Cases      : {summary['compliant_cases']} ({summary['compliance_pct']}%)")
    lines.append(f"  Critical Defects     : {summary['critical_defects']}")
    lines.append(f"  Major Defects        : {summary['major_defects']}")
    lines.append(f"  BVA Annotated Cases  : {summary['cases_with_bva_annotation']} ({summary['bva_annotation_pct']}%)")
    lines.append(f"  Overall Grade        : {summary['overall_grade']}")
    lines.append('')

    if 'rtm' in summary:
        rtm = summary['rtm']
        lines.append(f"  --- RTM Coverage ---")
        lines.append(f"  Requirements Coverage: {rtm['coverage_pct']}%")
        if rtm['uncovered_requirements']:
            lines.append(f"  Uncovered Requirements: {', '.join(rtm['uncovered_requirements'])}")
        if rtm['orphan_tests']:
            lines.append(f"  Orphan Tests: {', '.join(rtm['orphan_tests'])}")
        lines.append('')

    lines.append(f"  {'ID':<20} {'TITLE':<35} {'OK':>3} {'DEFECTS':>7} {'BVA':>4}")
    lines.append('  ' + '-' * 70)
    for r in case_results:
        ok = '✅' if r.is_compliant else '❌'
        defect_count = len(r.defects)
        bva = '✅' if r.has_bva_annotation else '  '
        lines.append(
            f"  {r.case_id:<20} {r.title[:35]:<35} {ok:>3} {defect_count:>7} {bva:>4}"
        )
    lines.append('=' * 72)
    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def main():
    """
    CLI entry point for the ISO 29119-3 Test Case Validator.

    Parses arguments, loads and validates test case files, computes RTM if
    requirements document is provided, and outputs results to stdout.

    Exit codes:
        0 — All test cases are compliant.
        1 — Critical defects found.
        2 — Input path or file format error.
    """
    parser = argparse.ArgumentParser(
        prog='test_case_validator',
        description=(
            'QA-QC Test Case Validator — ISO/IEC/IEEE 29119-3 compliance linter '
            'for manual test case documents (Markdown, CSV, JSON). Checks structural '
            'completeness, expected result quality, BVA/EP annotations, and RTM coverage.'
        ),
    )
    parser.add_argument(
        '--path', required=True,
        help='Path to a test case file (MD, CSV, JSON) or directory to scan.'
    )
    parser.add_argument(
        '--format', choices=['json', 'table'], default='json',
        help='Output format. "json" (default) or "table" for human-readable.'
    )
    parser.add_argument(
        '--requirements',
        help='Optional path to a requirements file (JSON array or CSV with "id" column) for RTM analysis.'
    )
    parser.add_argument(
        '--strict', action='store_true',
        help='Treat Major defects as Critical; return exit code 1 if any Major defect found.'
    )

    args = parser.parse_args()
    target = Path(args.path)

    if not target.exists():
        print(f'[ERROR] Path not found: {args.path}', file=sys.stderr)
        sys.exit(2)

    # Collect files to validate
    files_to_validate = []
    if target.is_file():
        files_to_validate = [str(target)]
    else:
        for root, _, files in os.walk(str(target)):
            for fname in files:
                if fname.endswith(('.md', '.markdown', '.csv', '.json')):
                    files_to_validate.append(os.path.join(root, fname))

    if not files_to_validate:
        print('[INFO] No supported test case files found (MD, CSV, JSON).', file=sys.stderr)
        sys.exit(0)

    # Validate all files
    all_results: list[TestCaseResult] = []
    for fpath in files_to_validate:
        results = parse_file(fpath)
        all_results.extend(results)

    if not all_results:
        print('[INFO] No test cases found in the provided file(s).', file=sys.stderr)
        sys.exit(0)

    rtm = build_rtm(all_results, args.requirements)
    summary = build_summary(all_results, rtm)

    if args.format == 'table':
        print(format_table_output(summary, all_results))
    else:
        output = {
            'summary': summary,
            'cases': [
                {
                    'id': r.case_id,
                    'title': r.title,
                    'is_compliant': r.is_compliant,
                    'missing_fields': r.missing_fields,
                    'defects': [asdict(d) for d in r.defects],
                    'has_bva_annotation': r.has_bva_annotation,
                    'has_ep_annotation': r.has_ep_annotation,
                    'traceability_tag': r.traceability_tag,
                }
                for r in all_results
            ],
        }
        if rtm:
            output['rtm'] = asdict(rtm)
        print(json.dumps(output, indent=2, ensure_ascii=False))

    # Exit codes
    has_critical = summary['critical_defects'] > 0
    has_major = summary['major_defects'] > 0
    if has_critical or (args.strict and has_major):
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()
