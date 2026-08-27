# Functional Requirements Document (FRD)

> Focus on: WHAT the system must DO (not how to do it at the UI level). Each FR must have an ID, clearly defined input/output, and associated business rules.

## 1. Functional Requirements List

### Module: [Module Name]

| FR ID | Requirement Description | Input | Output | Associated Business Rule | Priority |
|---|---|---|---|---|---|
| FR-001 | | | | BR-001 | Must-have |

## 2. Business Rules

| BR ID | Rule Description | Applies to FR |
|---|---|---|
| BR-001 | | FR-001 |

> A business rule is an invariant logical condition (e.g., "Orders over $50 qualify for free shipping"), distinct from a functional requirement which describes system behavior (e.g., "The system automatically calculates shipping fees at checkout").

## 3. Data Structure

Describe the main entities related to this module, to be used as input for the ERD in the Mermaid diagrams section:

### Entity: [Entity Name]
| Field | Data Type | Required | Constraints |
|---|---|---|---|
| | | | |

## 4. Pre/Post-Conditions

### FR-001
- **Pre-condition:** the state the system must be in before this action can occur
- **Post-condition:** the state of the system after the action succeeds
- **Exception / Error case:** error scenarios that must be handled and the corresponding system behavior