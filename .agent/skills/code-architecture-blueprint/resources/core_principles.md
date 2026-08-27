# Core Principles: DRY, KISS, YAGNI

These three principles sometimes pull in opposite directions (DRY encourages abstraction, KISS/YAGNI warn against premature abstraction) — the last section explains how to balance them.

## DRY (Don't Repeat Yourself)

**Definition**: a piece of logic should not exist duplicated in two or more places. When duplication is found, extract it into a shared function/class/utility.

**Violation signals when reviewing**:
- Copy-pasted blocks of code with only a few values changed.
- The same business rule checked in multiple different places (e.g., the condition "order is eligible for refund" written separately in both the Controller and the Service) — the risk: fixing it in one place while forgetting the other causes the logic to drift apart over time.

**Important caveat**: DRY applies to duplicated LOGIC/BUSINESS RULES, not mechanically to code that merely LOOKS similar but represents different concepts. Two blocks of code that happen to be syntactically identical today but serve two independent business purposes should NOT be merged prematurely — merging them creates artificial coupling, so when one business rule changes, it wrongly affects the other.

## KISS (Keep It Simple, Stupid)

**Definition**: choose the simplest solution that correctly solves the current problem. Don't apply a complex Design Pattern to a problem that a few lines of ordinary logic already solve.

**Violation signals when reviewing**:
- Using a Factory Pattern to create just ONE type of object, with no plan to add a second type.
- A full Clean Architecture setup for a one-off internal script/tool.
- An abstraction (interface, abstract class) with exactly ONE implementation and no clear reason a second one will ever exist.

## YAGNI (You Aren't Gonna Need It)

**Definition**: don't write code for a feature "we might need someday" — only solve the actual requirement in front of you.

**Violation signals when reviewing**:
- Adding a parameter/config option "for future flexibility" with no concrete use case yet.
- Designing a DB table with several "reserved" columns that aren't used.
- Building a generalized interface for several hypothetical scenarios when only one actually exists today.

**Distinguishing YAGNI from reasonable extensibility**: YAGNI doesn't mean writing careless code that ignores the future — it means not building a mechanism for an UNCONFIRMED future need. If an extension need is nearly certain (e.g., you're already building multi-tenancy, so multiple tenants will definitely exist), that's not a YAGNI violation — it's a known business constraint.

## Balancing DRY Against KISS/YAGNI

Abstracting too early (over-abstraction) "in the name of DRY" for logic that has only appeared ONCE so far is itself a YAGNI violation. A common rule of thumb: the **"Rule of Three"** — only abstract/consolidate once a piece of logic has been duplicated a THIRD time, or when it's clearly, deliberately shared logic from the start (not a coincidence).
