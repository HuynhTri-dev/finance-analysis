<!--
  name: automation_quality_rubric.md
  description: Detailed quality rubric for automated test code evaluation.
               Covers Arrange-Act-Assert (AAA) pattern compliance, assertion
               density measurement, mutation testing heuristics, and a comprehensive
               test smell anti-pattern catalog. Used by QA-QC agent in Steps 3 & 4.
-->

# Automation Test Code Quality Rubric

**Standards:** SWEBOK v3 · Mutation Testing Theory · Clean Test Code Principles  
**Languages:** Dart · TypeScript · JavaScript · Python  
**Purpose:** Quantitative and qualitative framework for evaluating automated test code.

---

## 1. Overall Scoring Model

| Dimension | Weight | Max Points | Description |
|---|---|---|---|
| **A — AAA Pattern Compliance** | 30% | 30 pts | Structural clarity and phase separation in test functions |
| **B — Assertion Density & Quality** | 40% | 40 pts | Meaningfulness and sufficiency of verification statements |
| **C — Mutation Resilience** | 20% | 20 pts | Estimated or actual ability to catch injected code mutations |
| **D — Test Smell-Free Code** | 10% | 10 pts | Absence of known test anti-patterns |

**Grade Scale:**

| Score | Grade | Meaning |
|---|---|---|
| `90 – 100` | **A — Excellent** | High-quality test suite; minimal rework needed |
| `75 – 89` | **B — Good** | Solid foundation; improve assertion specificity |
| `60 – 74` | **C — Acceptable** | Notable gaps in verification rigor |
| `40 – 59` | **D — Poor** | Automation provides false confidence |
| `< 40` | **F — Failing** | Test suite is counterproductive; major refactor needed |

---

## 2. Dimension A — Arrange-Act-Assert (AAA) Pattern Compliance (30 pts)

### 2.1 Pattern Identification Rules

A compliant test function MUST demonstrate all three phases, either via:
- **Explicit comments** (`// ARRANGE`, `// ACT`, `// ASSERT`)
- **Structural delineation** (blank line between phases, separate variable scopes)
- **Implicit semantic structure** (setup variables → single invocation → assertion block)

### 2.2 Language-Specific Pattern Signatures

#### Dart (Flutter Test)

```dart
// ✅ COMPLIANT — Clear AAA separation
test('should return user profile when valid ID is provided', () {
  // ARRANGE
  final mockRepo = MockUserRepository();
  when(mockRepo.findById('user-123'))
      .thenReturn(User(id: 'user-123', name: 'Alice'));

  // ACT
  final result = UserService(mockRepo).getProfile('user-123');

  // ASSERT
  expect(result.name, equals('Alice'));
  expect(result.id, equals('user-123'));
});

// ❌ VIOLATION: AAA_MISSING_ASSERT — Liar Test
test('should process payment', () {
  final service = PaymentService();
  service.processPayment(amount: 100.0, currency: 'USD');
  // No expect() statements — this test proves nothing
});

// ❌ VIOLATION: AAA_MERGED — Interleaved phases
test('should update cart', () {
  final cart = Cart();
  cart.addItem(Item('A'));            // ACT begins
  expect(cart.count, equals(1));      // ASSERT in middle
  cart.addItem(Item('B'));            // ACT continues after ASSERT
  expect(cart.count, equals(2));      // Unclear test intent
});
```

#### TypeScript / JavaScript (Jest / Vitest)

```typescript
// ✅ COMPLIANT
it('should calculate discounted price correctly', () => {
  // ARRANGE
  const pricer = new PricingService({ discountRate: 0.2 });
  const originalPrice = 100;

  // ACT
  const discountedPrice = pricer.applyDiscount(originalPrice);

  // ASSERT
  expect(discountedPrice).toBe(80);
});

// ❌ VIOLATION: AAA_MISSING_ACT — Mock-only test (tests mock, not SUT)
it('should call the repository', () => {
  const mockRepo = jest.fn();
  const service = new OrderService(mockRepo);
  // Never calls service.someMethod() — tests nothing real
  expect(mockRepo).not.toHaveBeenCalled();
});
```

#### Python (pytest / unittest)

```python
# ✅ COMPLIANT
def test_calculate_tax_for_standard_rate():
    # ARRANGE
    calculator = TaxCalculator(region="US-CA")
    gross_amount = 1000.0

    # ACT
    result = calculator.compute(gross_amount)

    # ASSERT
    assert result.tax_amount == pytest.approx(92.5, rel=1e-3)
    assert result.net_amount == pytest.approx(907.5, rel=1e-3)

# ❌ VIOLATION: AAA_SILENT_CATCHER — Exception swallowed
def test_invalid_input():
    try:
        parser.parse(None)
    except Exception:
        pass  # This test always passes, even if the wrong exception fires
```

### 2.3 AAA Compliance Scoring

**Per-file scoring:**

```
AAA Compliance % = (Tests Fully Compliant / Total Tests) × 100
```

| Compliance % | Points |
|---|---|
| 95 – 100% | 30 pts |
| 80 – 94% | 23 pts |
| 65 – 79% | 16 pts |
| 50 – 64% | 10 pts |
| < 50% | 3 pts |

---

## 3. Dimension B — Assertion Density & Quality (40 pts)

### 3.1 Assertion Inventory by Language

**Count only meaningful assertions.** Use the following lookup table:

| Language | Meaningful Assertions | Trivial / Not Counted |
|---|---|---|
| **Dart** | `expect(value, specificMatcher)`, `expectLater(future, emits(...))`, `throwsA(isA<SpecificException>())` | `expect(obj, isNotNull)`, `expect(list, isNotEmpty)` alone |
| **TypeScript** | `expect(x).toBe(y)`, `.toEqual({...})`, `.toThrow(SpecificError)`, `.toMatchSnapshot()` (with review) | `.toBeTruthy()`, `.toBeDefined()` alone |
| **Python** | `assert result == expected`, `mock.assert_called_once_with(...)`, `pytest.raises(SpecificError)` | `assert result is not None`, `assert result` alone |

### 3.2 Assertion Density Index (ADI)

```
ADI = Total Meaningful Assertions / Total Test Functions
```

**Scoring Table:**

| ADI Range | Points | Classification |
|---|---|---|
| `1.0 – 3.0` | 40 pts | ✅ Optimal — focused, verifiable tests |
| `3.1 – 5.0` | 30 pts | ⚠️ Slightly over-asserted — review for Giant Test smell |
| `0.5 – 0.9` | 15 pts | 🟠 Under-asserted — tests run but barely verify |
| `0.1 – 0.4` | 5 pts | 🔴 Severely deficient — negligible verification |
| `0` | 0 pts | 🔴 Critical: The Liar — immediate refactor required |
| `> 5` | 10 pts (penalty) | 🔴 Giant Test — violates SRP; split required |

### 3.3 Trivial Assertion Red-Flag Patterns

These assertion patterns MUST be flagged as **weak** and supplemented or replaced:

```python
# Python
assert result is not None                # ❌ Only proves it returned; not what it returned
assert isinstance(result, dict)          # ❌ Only proves type; not content
assert len(result) > 0                   # ❌ Only proves non-empty; not correct content
assert result                            # ❌ Truthiness only; dangerous for falsy values

# TypeScript/JavaScript
expect(result).toBeDefined()             // ❌ Passes for undefined-to-null transition
expect(result).toBeTruthy()             // ❌ Does not catch value errors
expect(array).not.toBeNull()            // ❌ Missing content verification

# Dart
expect(result, isNotNull)               // ❌ Passes even if result = ""
expect(list, isNotEmpty)                // ❌ Does not verify list contents
```

---

## 4. Dimension C — Mutation Resilience (20 pts)

### 4.1 Actual Mutation Score (if report provided)

If the user provides output from a mutation testing tool:

| Tool | Supported Formats |
|---|---|
| **Stryker** (JS/TS) | JSON report (`mutation.json`), HTML report |
| **Mutmut** (Python) | `mutmut results`, `mutmut show <id>` output |
| **Dart mutation** | Custom runner outputs |

**Parse the Mutation Score:**
```
MS = (Killed Mutants / Total Mutants) × 100%
```

| Mutation Score | Points |
|---|---|
| `> 85%` | 20 pts |
| `70 – 85%` | 15 pts |
| `50 – 70%` | 8 pts |
| `< 50%` | 0 pts |

### 4.2 Static Mutation Heuristics (if no report available)

Scan assertions for resistance to the following synthetic mutation operators:

#### ROR — Relational Operator Replacement

Assess whether assertions would survive `>` → `>=`, `<` → `<=`, `==` → `!=`:

```python
# ❌ ROR-Vulnerable: assertion uses "truthy" — ROR mutation survives
assert result > 0                    # Mutant: result >= 0 → still passes if result=0
assert len(items) > 0                # Mutant: len(items) >= 0 → always true

# ✅ ROR-Resilient: exact boundary values asserted
assert result == 5                   # Mutant: result != 5 → fails ✅
assert len(items) == 3               # Mutant: len(items) != 3 → fails ✅
```

#### AOR — Arithmetic Operator Replacement

Assess whether assertions would survive `+` → `-`, `*` → `/`:

```typescript
// ❌ AOR-Vulnerable: only type is checked
expect(typeof result).toBe('number') // Mutant: -result → still number

// ✅ AOR-Resilient: exact computed value asserted
expect(result).toBe(150)             // Mutant: 100 - 50 = 50 → fails ✅
```

#### SVR — Statement Void/Return Replacement

Assess whether a null/void return would be detected:

```dart
// ❌ SVR-Vulnerable: side effect only
expect(mockRepo.save, wasCalled);    // Mutant: return null → not detected

// ✅ SVR-Resilient: return value verified
expect(result.userId, equals('abc')); // Mutant: return null → NullPointerException ✅
```

**Heuristic Scoring:**

| Heuristics Result | Points |
|---|---|
| Assertions are resilient to ROR, AOR, and SVR | 20 pts |
| Resilient to 2 of 3 operators | 12 pts |
| Resilient to 1 of 3 operators | 6 pts |
| Most assertions are vulnerability-prone | 0 pts |

---

## 5. Dimension D — Test Smell-Free Code (10 pts)

### 5.1 Test Smell Catalog & Detection Signatures

| # | Smell Name | Detection Signature | Severity | Point Deduction |
|---|---|---|---|---|
| 1 | **The Liar** | `assertion_count == 0` in any test function | 🔴 Critical | -10 pts per test |
| 2 | **The Silent Catcher** | `try/except: pass` or `catch(e) {}` without re-assertion | 🔴 Critical | -8 pts |
| 3 | **The Overspecified Mock** | `verify(mock.method()).called(exactly(1))` without asserting actual output | 🔴 High | -6 pts |
| 4 | **The Giant** | Single test with > 7 meaningful assertions | 🟠 Major | -4 pts |
| 5 | **The Flaky** | Direct use of `DateTime.now()`, `random()`, or live network calls without mocking | 🟠 Major | -4 pts |
| 6 | **The Duplicate** | Identical logic block in ≥ 2 test functions | 🟡 Minor | -2 pts |
| 7 | **The Slow** | Test functions marked with direct I/O, sleep, or delays > 100ms | 🟡 Minor | -1 pt |

### 5.2 Smell-Free Scoring

Start at 10 points. Apply deductions from 5.1. Minimum score: 0.

---

## 6. Automation Test Scorecard Template

```
╔══════════════════════════════════════════════════════════════════════╗
║               AUTOMATION TEST QUALITY SCORECARD                      ║
╠══════════════════════════════════════════════════════════════════════╣
║ Module / File: __________________________________________________     ║
║ Language:      [ ] Dart  [ ] TypeScript  [ ] JavaScript  [ ] Python  ║
║ Total Tests:   ____  │  Zero-Assert Tests: ____                      ║
╠═══════════════════════╦══════════════╦══════════╦════════════════════╣
║ Dimension             ║ Max Points   ║ Score    ║ Grade              ║
╠═══════════════════════╬══════════════╬══════════╬════════════════════╣
║ A. AAA Compliance     ║ 30           ║ __/30    ║ [A/B/C/D/F]       ║
║ B. Assertion Density  ║ 40           ║ __/40    ║ [A/B/C/D/F]       ║
║ C. Mutation Resilience║ 20           ║ __/20    ║ [A/B/C/D/F]       ║
║ D. Smell-Free         ║ 10           ║ __/10    ║ [A/B/C/D/F]       ║
╠═══════════════════════╬══════════════╬══════════╬════════════════════╣
║ TOTAL                 ║ 100          ║ __/100   ║ [A/B/C/D/F]       ║
╚═══════════════════════╩══════════════╩══════════╩════════════════════╝

Assertion Density Index: ____
Zero-Assertion Tests:    [List test function names]
AAA Violations Found:    [List: file:line — violation type]
Test Smells Found:       [List: smell name — file:line]
Mutation-Vulnerable Assertions: [Count and examples]
```
