---
name: test-asset-quality-assessment
description: >
  Evaluates the quality and completeness of software testing assets — both manual
  test cases and automated test code. Activates when the user requests a QA audit,
  test case review, automation test quality check, assertion density analysis,
  mutation testing evaluation, or any ISO 29119-3 / ISTQB compliance assessment.
  Produces a structured scorecard with actionable recommendations. Supports test
  files in Dart, TypeScript, JavaScript, and Python.
triggers:
  - "audit test case"
  - "review test case"
  - "đánh giá test case"
  - "kiểm tra kịch bản kiểm thử"
  - "review automation test"
  - "đánh giá automation test"
  - "assertion density"
  - "mật độ assertion"
  - "mutation testing"
  - "kiểm thử đột biến"
  - "mutation score"
  - "AAA pattern"
  - "arrange act assert"
  - "test quality assessment"
  - "đánh giá chất lượng kiểm thử"
  - "kiểm thử chất lượng test"
  - "ISO 29119"
  - "ISTQB equivalence partitioning"
  - "boundary value analysis"
  - "phân vùng tương đương"
  - "phân tích giá trị biên"
  - "test coverage quality"
  - "test smell"
  - "liar test"
---

# Skill: Test Asset Quality Assessment (QA-QC)

## Overview

This skill provides a **systematic, evidence-based framework** for evaluating the quality of a software project's entire test portfolio. It is grounded in internationally recognized standards and measurement techniques:

- **ISO/IEC/IEEE 29119-3** — Structure and completeness standard for test case documentation.
- **ISTQB Foundation Level Syllabus** — Test Design Techniques: Equivalence Partitioning (EP) and Boundary Value Analysis (BVA).
- **SWEBOK v3** — Software Engineering Body of Knowledge: Arrange-Act-Assert (AAA) unit test structure.
- **Mutation Testing** (Wikipedia: *Mutation testing*) — Resilience scoring for automation test suites.

## When to Use This Skill
- Use when want to eval the quality and completeness of software testing assets — both manual test cases and automated test code. 
- **Do NOT use** this skill when the user simply asks to "generate" or "write" new test cases from scratch without an existing test asset to evaluate

## Core Knowledge Base

### Module A — Manual Test Case Standards (ISO/IEC/IEEE 29119-3 & ISTQB)

#### A.1 Mandatory Structural Fields (ISO 29119-3)

Every test case document **MUST** contain the following fields. Missing any is a **Critical Defect**:

| Field | Description | Disqualifying Defect if Missing |
|---|---|---|
| **Test Case ID** | Unique, traceable identifier (e.g., `TC-AUTH-001`) | Yes — prevents bidirectional RTM |
| **Title / Objective** | One-sentence statement of what is being validated | Yes — causes ambiguity |
| **Pre-conditions** | System state, data, and environment required before test execution | Yes — makes test non-reproducible |
| **Test Steps** | Numbered, atomic, unambiguous action steps | Yes — test is unexecutable |
| **Expected Results** | Measurable, observable outcome for each step or overall | Yes — no pass/fail criterion |
| **Traceability Tag** | Link to the requirement ID (e.g., `REQ-LOGIN-003`, User Story ID) | Yes — orphan test / coverage gap |

#### A.2 ISTQB Test Design Technique Coverage (EP & BVA)

For each input field or system condition under test, evaluate whether the tester applied:

**Equivalence Partitioning (EP):**
- At least one test case per **valid** partition (happy path).
- At least one test case per **invalid** partition (rejection logic, error handling).
- Flag: Missing invalid partitions = **Major Defect**.

**Boundary Value Analysis (BVA) — 3-Value Method:**
Ensure coverage of these 7 boundary points for each range-constrained input:

```
Min-1 (invalid) | Min (valid) | Min+1 (valid) | Nominal | Max-1 (valid) | Max (valid) | Max+1 (invalid)
```

- Minimum acceptable BVA coverage: `Min`, `Max`, and at least one of `Min±1` or `Max±1`.
- Missing **all boundary tests** for a range input = **Critical Defect**.
- Missing only `±1` tests = **Minor Defect**.

#### A.3 Requirement Traceability Matrix (RTM)

- Cross-reference all test case `Traceability Tags` against the requirements/specification document.
- **Under-coverage** (requirements with no linked test cases) = **Critical Defect**.
- **Over-coverage** (test cases with no matching requirement = orphan tests) = **Major Defect** (wasted effort/noise).

---

### Module B — Automation Test Code Standards (SWEBOK v3, Mutation Testing)

#### B.1 Arrange-Act-Assert (AAA) Pattern

A well-structured unit test MUST be visually and logically divided into exactly 3 phases:

```
// ARRANGE: Set up the test data, dependencies, and expected state
// ACT:     Execute the single unit of behavior under test
// ASSERT:  Verify the outcome matches the expected result
```

**Language-specific patterns to identify:**

| Language | Arrange | Act | Assert |
|---|---|---|---|
| **Dart** | Variable declarations, `setUp()` | Function call under test | `expect(actual, matcher)`, `expectLater()` |
| **TypeScript/JS** | `const`, `let`, `mock()`, `beforeEach` | `const result = sut.method()` | `expect(result).toBe()`, `expect(result).toEqual()` |
| **Python** | Variable setup, `@pytest.fixture`, `Mock()` | `result = function_under_test()` | `assert result == expected`, `mock.assert_called_with()` |

**AAA Violation Categories:**

- `AAA_MERGED` — Arrange and Act are interleaved (no clear separation).
- `AAA_MISSING_ACT` — No identifiable action/invocation (tests a mock, not the SUT).
- `AAA_MISSING_ASSERT` — The test runs code but never verifies any outcome. **This is the highest-severity defect.**

#### B.2 Assertion Density & Quality

**Formula:**
```
Assertion Density (AD) = Total Meaningful Assertions / Total Test Functions
```

**Thresholds:**

| AD Score | Classification | Action |
|---|---|---|
| `0` | 🔴 **Critical: The Liar Test** | Flag immediately. Zero-assertion tests are worse than no tests. |
| `0.1 – 0.9` | 🔴 **Critical: Severely Under-Asserted** | Test runs code but verifies almost nothing. |
| `1 – 3` | ✅ **Optimal** | Recommended range for focused unit tests. |
| `4 – 7` | ⚠️ **Warning: Possibly a Giant Test** | Review if one test covers multiple independent behaviors. |
| `> 7` | 🔴 **Critical: Giant Test Anti-Pattern** | Likely violates Single Responsibility. Refactor required. |

**Trivial Assertion Detection (NOT counted as meaningful):**
```python
# Examples of trivial assertions to flag:
assert result is not None           # Too weak — does not validate value
expect(value, isTrue)               # Tautology if value is never False
expect(list, isNotEmpty)            # Weak — does not verify content
```

#### B.3 Mutation Testing — Score & Interpretation

**Mutation Score formula:**
```
Mutation Score (MS) = (Killed Mutants / Total Mutants) × 100%
```

**Score Interpretation:**

| Mutation Score | Grade | Meaning |
|---|---|---|
| `> 85%` | A — Excellent | Test suite is highly resilient. |
| `70 – 85%` | B — Good | Minor gaps, review surviving mutants. |
| `50 – 70%` | C — Acceptable | Notable gaps; improve assertion specificity. |
| `< 50%` | F — Failing | Tests cannot reliably catch regressions. |

**Common Surviving Mutant Patterns (Static Heuristics):**

| Mutant Type | Code Change | Indicator of Weak Assertion |
|---|---|---|
| `ROR` (Relational Operator Replacement) | `>` → `>=`, `==` → `!=` | Assertions don't check exact boundary values |
| `AOR` (Arithmetic Operator Replacement) | `+` → `-`, `*` → `/` | Assertions check only type, not computed value |
| `LCR` (Logical Connector Replacement) | `&&` → `\|\|` | No tests for combined false conditions |
| `SVR` (Statement Void/Return Replacement) | `return result` → `return null` | No test verifies the return value directly |

---

### Module C — Test Smell Catalog

Before generating the report, scan for these anti-patterns and cite them by name:

| # | Smell Name | Signature | Severity |
|---|---|---|---|
| 1 | **The Liar** | Test function with 0 assertions | 🔴 Critical |
| 2 | **The Silent Catcher** | `try/catch` that swallows exceptions without re-asserting | 🔴 Critical |
| 3 | **The Overspecified Mock** | Tests that assert on mock call counts without verifying actual output | 🔴 High |
| 4 | **The Giant** | Single test with > 7 assertions covering multiple behaviors | 🟠 Major |
| 5 | **The Flaky Environment Dependant** | Test depends on current time, random values, or network without mocking | 🟠 Major |
| 6 | **The Duplicate** | Identical test logic with different names | 🟡 Minor |
| 7 | **The Missing BVA** | No boundary value cases for a range-typed parameter | 🟡 Minor |

---

## Step-by-Step Workflow

### Step 1 — Ingestion & Static AST Scanning

**Goal:** Extract quantitative metrics from source files before qualitative analysis.

**Actions:**
1. Identify input assets provided by the user:
   - `[TYPE_A]` Manual test case files: `.md`, `.csv`, `.json`, `.xlsx`.
   - `[TYPE_B]` Automation test code files: `.dart`, `.ts`, `.js`, `.py`.
2. For **TYPE_B** files, invoke the analyzer script (black-box, run with `--help` first):
   ```bash
   python3 .agent/skills/qa-qc/scripts/test_asset_analyzer.py \
     --path <test_file_or_directory> \
     --format json
   ```
3. For **TYPE_A** files, invoke the validator:
   ```bash
   python3 .agent/skills/qa-qc/scripts/test_case_validator.py \
     --path <test_case_file> \
     --format json
   ```
4. Parse the JSON output. Note: `assertion_density`, `zero_assert_count`, `aaa_violations`, `missing_fields`.
5. Read the detailed rubrics from:
   - `@.agent/skills/qa-qc/resources/iso_29119_rubric.md`
   - `@.agent/skills/qa-qc/resources/automation_quality_rubric.md`

---

### Step 2 — Manual Test Case Audit (ISO 29119-3 & ISTQB)

**Goal:** Score each test case against the structured quality rubric.

**Actions:**
1. For each test case, verify presence of all **6 mandatory ISO 29119-3 fields** (Module A.1).
2. Group test cases by functional area/feature. For each input domain:
   - Identify which **EP partitions** (valid/invalid) are covered.
   - Apply the **7-point BVA checklist** (Min-1 through Max+1).
3. Cross-reference all `Traceability Tags` against the provided requirements document (RTM).
   - Produce a list of: (a) Uncovered Requirements, (b) Orphan Tests.
4. Assign scores using `@iso_29119_rubric.md` weighting table.

---

### Step 3 — Automation Test Code Audit (AAA & Assertion Density)

**Goal:** Evaluate structural quality and verification completeness of each test function.

**Actions:**
1. Review the JSON output from `test_asset_analyzer.py` (Step 1).
2. For each test function, classify its AAA compliance (Module B.1 categories).
3. Check each assertion against the **Trivial Assertion** list (Module B.2).
4. Calculate overall **Assertion Density (AD)** score for the file/module.
5. Apply the **Test Smell Catalog** (Module C) — log each smell found with its file and line reference.

---

### Step 4 — Mutation Testing Evaluation

**Goal:** Assess the test suite's ability to catch real regressions.

**Decision Tree:**

- **If** the user provides a mutation report file (Stryker, Mutmut, or Pitest output):
  → Parse the report and compute actual `Mutation Score`. Grade per Module B.3 table.

- **If** no mutation report is available:
  → Apply **Static Mutation Heuristics**: Scan assertions for patterns vulnerable to ROR, AOR, LCR, SVR mutations (Module B.3). List specific test functions at high risk.

---

### Step 5 — Scorecard Generation & Recommendations

**Goal:** Produce a comprehensive, actionable quality report.

**Actions:**
1. Load the report template: `@.agent/skills/qa-qc/resources/qa_assessment_report_template.md`.
2. Populate:
   - **Overall Health Score** (weighted average of all module scores → Grade A/B/C/F).
   - **Manual Test Case Scorecard Table** (ISO 29119-3 fields + EP/BVA + RTM gaps).
   - **Automation Test Scorecard Table** (AAA compliance %, AD score, Test Smells found).
   - **Mutation Score** (actual or heuristic-estimated grade).
   - **Critical Warnings** list (all 🔴 Critical and 🟠 Major smells).
3. Generate **Concrete Recommendations**:
   - For each Critical/Major defect: Provide a specific, rewritable example of the fix.
   - List **Missing Test Scenarios** the tester should add (specific BVA boundary cases, missing invalid partitions, missing requirement links).
4. Output the final report as a Markdown file.

---

## Accompanying Scripts & Resources

| Asset | Purpose | Usage |
|---|---|---|
| `scripts/test_asset_analyzer.py` | AST-based automation test analyzer (Dart, TS/JS, Python) | `python3 <path> --help` |
| `scripts/test_case_validator.py` | ISO 29119-3 field checker for manual test case files | `python3 <path> --help` |
| `resources/iso_29119_rubric.md` | Detailed scoring rubric for manual test cases | Read on demand in Step 2 |
| `resources/automation_quality_rubric.md` | Detailed AAA, Assertion Density, and Anti-pattern rules | Read on demand in Step 3 |
| `resources/qa_assessment_report_template.md` | Final report template | Load in Step 5 |
