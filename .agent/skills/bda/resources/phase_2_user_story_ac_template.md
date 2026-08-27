# User Stories & Acceptance Criteria

> Reference: Agile Alliance. Each User Story must satisfy the **INVEST** criteria: Independent, Negotiable, Valuable, Estimable, Small, Testable. Acceptance Criteria are written in Gherkin (Given/When/Then) format for easy conversion to test cases.

## Standard Format

```
US-XXX: [Short descriptive title]

As a [user role],
I want to [action / feature],
So that [value / benefit achieved].

Links: FR-XXX, BR-XXX

Acceptance Criteria:
  AC1:
    Given [initial condition]
    When [action occurs]
    Then [expected result]

  AC2:
    Given ...
    When ...
    Then ...

Priority: Must-have / Should-have / Could-have (MoSCoW)
Story Points: (if the team uses estimation)
```

## Illustrative Example

```
US-012: Login with email and password

As a registered user,
I want to log in with my email and password,
So that I can access the personalized features of the system.

Links: FR-008, BR-003

Acceptance Criteria:
  AC1:
    Given the user has a valid account
    When they enter the correct email and password and click "Login"
    Then the system redirects them to the Dashboard within 2 seconds

  AC2:
    Given the user has entered an incorrect password more than 5 consecutive times
    When they attempt to log in for the 6th time
    Then the system temporarily locks the account for 15 minutes and displays a corresponding notification

Priority: Must-have
```

## Self-Check Checklist When a Story Is Written (INVEST)
- [ ] **Independent** — can be developed and tested independently of other stories
- [ ] **Negotiable** — describes the value, does not lock in the implementation approach
- [ ] **Valuable** — delivers clear value to the user or the business
- [ ] **Estimable** — contains enough detail for the team to estimate effort
- [ ] **Small** — completable within one sprint; if not, it must be split
- [ ] **Testable** — Acceptance Criteria are specific enough to write test cases directly