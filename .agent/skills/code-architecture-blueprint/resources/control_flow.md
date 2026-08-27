# Control Flow — Early Return / Guard Clause

## The Problem: Arrow Anti-Pattern

Deeply nested conditionals create "arrow-shaped" code (indentation growing with each condition), forcing the reader to hold every parent condition in mind before understanding the logic buried at the deepest level.

```dart
// BAD — the real logic is buried 3 levels deep
void processOrder(Order order) {
  if (order != null) {
    if (order.isPaid) {
      if (!order.isShipped) {
        // Handle shipping — this is actually the important logic
      }
    }
  }
}
```

## The Fix: Check Invalid/Error Conditions and Return Immediately

```dart
// GOOD — Early Return
void processOrder(Order order) {
  if (order == null) return;
  if (!order.isPaid) return;
  if (order.isShipped) return;

  // Handle shipping — the main logic sits at the base indentation level, easiest to read
}
```

Principle: list the INVALID/skip conditions first and return/continue/throw immediately. The remaining code at the bottom of the function contains only the "happy path" — no more nesting.

## Applying This to Similar Constructs

- **Loops**: use `continue` to skip elements that don't meet a condition instead of wrapping the entire loop body in an `if`.
- **Try/catch**: handle the error and return/throw early inside the catch block, avoiding deeply nested main logic inside the try block.
- **Optional/nullable chaining**: many modern languages offer optional chaining (`?.`) or pattern matching that reduces the need for nested null checks — prefer these when the language supports them, but still use an explicit guard clause once the logic is more than a single line.

## When NOT to Force Early Return

If an if-else structure represents two PARALLEL LOGICAL BRANCHES of equal business importance (e.g., different handling for free-tier vs. premium users, both being equally valid "happy paths," not an error/exclusion condition), keeping the if-else as-is is more appropriate — don't force an early return where there's no real "guard" concept. Early return is for GUARD CLAUSES (excluding invalid cases), not a substitute for every branching structure.

## Signals to Look for When Reviewing

- Nested `if`s deeper than 2 levels inside a single function → suggest refactoring with early return.
- A function whose main logic sits at the last line, at the deepest indentation → a clear sign of the arrow anti-pattern.
- Multiple null/invalid checks scattered throughout a function instead of grouped at the top.
