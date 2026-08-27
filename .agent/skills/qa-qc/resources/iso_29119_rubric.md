<!--
  name: iso_29119_rubric.md
  description: Detailed scoring rubric for manual test case evaluation based on
               ISO/IEC/IEEE 29119-3 structural compliance, ISTQB Equivalence
               Partitioning (EP), Boundary Value Analysis (BVA), and Requirement
               Traceability Matrix (RTM) coverage. Used by QA-QC agent in Step 2.
-->

# Manual Test Case Quality Rubric

**Standard:** ISO/IEC/IEEE 29119-3 · ISTQB Foundation Level Syllabus  
**Purpose:** Quantitative and qualitative scoring framework for manual test case review.

---

## 1. Overall Scoring Model

The total score for a manual test suite is calculated as a weighted sum across four dimensions:

| Dimension | Weight | Max Points | Description |
|---|---|---|---|
| **A — ISO 29119-3 Structural Completeness** | 35% | 35 pts | Presence and quality of all mandatory fields per test case |
| **B — ISTQB EP/BVA Design Technique Coverage** | 35% | 35 pts | Evidence of Equivalence Partitioning and Boundary Value Analysis |
| **C — Requirement Traceability (RTM)** | 20% | 20 pts | Bidirectional linkage between test cases and requirements |
| **D — Test Case Clarity & Executability** | 10% | 10 pts | Unambiguity of steps and measurability of expected results |

**Grade Scale:**

| Score Range | Grade | Interpretation |
|---|---|---|
| `90 – 100` | **A — Excellent** | Production-ready test suite, minimal gaps |
| `75 – 89` | **B — Good** | Minor gaps, can proceed with improvement plan |
| `60 – 74` | **C — Acceptable** | Significant gaps in design technique coverage |
| `40 – 59` | **D — Poor** | Structural defects; high risk of missed defects |
| `< 40` | **F — Failing** | Critical deficiencies; major rework required |

---

## 2. Dimension A — ISO 29119-3 Structural Completeness (35 pts)

### 2.1 Mandatory Field Checklist

For each test case, verify the presence **and** quality of the following fields:

| Field | Present? (Binary) | Quality Check | Points |
|---|---|---|---|
| **Test Case ID** | ✅ / ❌ | Follows naming convention (e.g., `TC-<FEATURE>-<NNN>`) | 3 pts |
| **Title / Objective** | ✅ / ❌ | Single sentence; clearly states **what** is being validated, not **how** | 5 pts |
| **Pre-conditions** | ✅ / ❌ | Specific system state, user role, and data state defined | 7 pts |
| **Test Steps** | ✅ / ❌ | Numbered, atomic steps; each step has a single action verb | 8 pts |
| **Expected Results** | ✅ / ❌ | Measurable & observable; contains specific values, not vague terms like "works correctly" | 8 pts |
| **Traceability Tag** | ✅ / ❌ | References a specific Requirement ID, User Story, or Feature spec | 4 pts |

**Total: 35 pts**

### 2.2 Field Quality Anti-Patterns

Flag these defects in the test steps and expected results:

| Anti-Pattern | Example | Severity |
|---|---|---|
| Vague Expected Result | `"The page loads correctly."` | 🔴 Critical — not measurable |
| Multi-action step | `"Click Submit and verify the response."` | 🟠 Major — not atomic |
| Missing error state | Steps only describe happy path, no error flow tested | 🟠 Major |
| Ambiguous Pre-condition | `"User is logged in."` without specifying user role | 🟡 Minor |
| Generic title | `"Test login"` without specifying the scenario | 🟡 Minor |

---

## 3. Dimension B — ISTQB EP/BVA Design Technique Coverage (35 pts)

### 3.1 Equivalence Partitioning (EP) — 15 pts

For each **input domain** or **system state** in the feature under test:

**Step 1:** Identify all equivalence classes:

```
Input Domain Example: "Age" field (valid: 18–65, invalid: <18 or >65)

Valid Partitions:
  [P1] 18 ≤ age ≤ 65   → At least 1 test case required (e.g., age = 30)

Invalid Partitions:
  [P2] age < 18          → At least 1 test case required (e.g., age = 10)
  [P3] age > 65          → At least 1 test case required (e.g., age = 70)
  [P4] age = null/empty  → At least 1 test case required
  [P5] age = non-numeric → At least 1 test case required (e.g., age = "abc")
```

**EP Scoring:**

| Coverage | Points |
|---|---|
| All valid AND invalid partitions covered | 15 pts |
| All valid partitions covered; some invalid missing | 9 pts |
| Only valid (happy path) partitions covered | 5 pts |
| No identifiable EP analysis applied | 0 pts |

### 3.2 Boundary Value Analysis (BVA) — 20 pts

For each range-typed input, apply the **3-value BVA method**:

**7 Boundary Test Points:**

```
[Boundary Line]       [Test Point]    [Class]    [Required?]
───────────────────────────────────────────────────────────
                      Min - 1         Invalid    REQUIRED (catch off-by-one)
                      Min             Valid       REQUIRED (exact lower bound)
                      Min + 1         Valid       Required (adjacent valid)
                      Nominal         Valid       Recommended
                      Max - 1         Valid       Required (adjacent valid)
                      Max             Valid       REQUIRED (exact upper bound)
                      Max + 1         Invalid    REQUIRED (catch off-by-one)
```

**Minimum Mandatory BVA Coverage:**
- `Min`, `Max` → **absolutely required** (2 boundary tests).
- At least one of `Min-1` or `Max+1` → **required** (reject at exact boundary).
- `Min+1` and `Max-1` → **recommended** (full 3-value coverage).

**BVA Scoring:**

| Coverage | Points |
|---|---|
| All 7 boundary points covered | 20 pts |
| Min, Max, Min-1, Max+1 covered (minimum acceptable) | 14 pts |
| Only Min and Max covered | 8 pts |
| Partial boundary (only 1 boundary point) | 4 pts |
| No BVA applied to any range-typed input | 0 pts |

### 3.3 BVA Identification Worksheet

Use this table to document BVA analysis per input parameter:

| Feature | Input Parameter | Data Type | Min | Max | BVA Applied? | Missing Points |
|---|---|---|---|---|---|---|
| Login | Password Length | String | 8 chars | 128 chars | ✅ / ❌ | |
| User Registration | Age | Integer | 18 | 100 | ✅ / ❌ | |
| File Upload | File Size | Float (MB) | 0.001 MB | 25 MB | ✅ / ❌ | |

---

## 4. Dimension C — Requirement Traceability Matrix (RTM) (20 pts)

### 4.1 RTM Construction

Cross-reference every test case against the feature specification or requirements document.

**RTM Format:**

| Requirement ID | Requirement Description | Test Case ID(s) | Coverage Status |
|---|---|---|---|
| `REQ-AUTH-001` | User can log in with email + password | `TC-AUTH-001`, `TC-AUTH-002` | ✅ Covered |
| `REQ-AUTH-002` | Failed login shows error message | `TC-AUTH-003` | ✅ Covered |
| `REQ-AUTH-003` | Account locked after 5 failed attempts | *(none)* | ❌ **UNCOVERED** |

### 4.2 RTM Scoring

| Metric | Formula | Points |
|---|---|---|
| **Requirement Coverage Rate** | `Covered Requirements / Total Requirements × 100%` | 0 – 12 pts |
| **Orphan Test Rate** | Deduct points: `Orphan Tests / Total Tests × 10` | Up to -8 pts |

| Coverage Rate | Points Awarded |
|---|---|
| 100% | 12 pts |
| 90 – 99% | 10 pts |
| 75 – 89% | 7 pts |
| 60 – 74% | 5 pts |
| < 60% | 2 pts |

---

## 5. Dimension D — Clarity & Executability (10 pts)

| Criterion | Points | Evaluation Method |
|---|---|---|
| Steps are unambiguous (new tester can execute without clarification) | 4 pts | Read the first step of each test case cold; if ambiguous, deduct |
| Expected results contain specific, measurable values | 4 pts | Scan for vague terms: "correctly", "successfully", "appropriately" |
| Pre-conditions are reproducible across environments | 2 pts | Check if pre-conditions reference test data by name/ID, not just "existing user" |

---

## 6. Scoring Summary Template

```
╔══════════════════════════════════════════════════════════════════════╗
║                  MANUAL TEST CASE QUALITY SCORECARD                  ║
╠══════════════════════════════════════════════════════════════════════╣
║ Feature / Module Under Review: _____________________________          ║
║ Total Test Cases Reviewed:     _____________________________          ║
║ Reviewer (Agent):              QA-QC Skill Agent                     ║
╠═══════════════════════╦══════════════╦══════════╦════════════════════╣
║ Dimension             ║ Max Points   ║ Score    ║ Grade              ║
╠═══════════════════════╬══════════════╬══════════╬════════════════════╣
║ A. ISO 29119-3        ║ 35           ║ __/35    ║ [A/B/C/D/F]       ║
║ B. EP/BVA Techniques  ║ 35           ║ __/35    ║ [A/B/C/D/F]       ║
║ C. RTM Coverage       ║ 20           ║ __/20    ║ [A/B/C/D/F]       ║
║ D. Clarity            ║ 10           ║ __/10    ║ [A/B/C/D/F]       ║
╠═══════════════════════╬══════════════╬══════════╬════════════════════╣
║ TOTAL                 ║ 100          ║ __/100   ║ [A/B/C/D/F]       ║
╚═══════════════════════╩══════════════╩══════════╩════════════════════╝

Critical Defects Found:  [Count] → [List]
Major Defects Found:     [Count] → [List]
Uncovered Requirements:  [List]
Missing BVA Points:      [List]
```
