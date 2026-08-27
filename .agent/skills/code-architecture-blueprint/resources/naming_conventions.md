# Naming Conventions

## General Principles (apply to any language)

1. **Names must be self-explanatory.** A reader should understand what a variable/function is for without reading the function body or an extra explanatory comment.
2. **No cryptic abbreviations.** `usr`, `cfg`, `tmp` for long-lived variables are a red flag. Acceptable exceptions: short-lived loop counters (`i`, `j` in a simple for loop), extremely common domain terms (`id`, `url`).
3. **A function should do ONE thing (Single Responsibility at the function level).** The clearest violation signal: a function name joining two actions with a conjunction — `validateAndSaveUser`, `fetchAndParseData`, `checkAndUpdateStatus`. When you see this, split it into two functions; the caller can invoke both in sequence if needed.
4. **Function names should start with a verb; variable/class names should be nouns.** `getUserById` (function) vs. `activeUserList` (variable) vs. `UserRepository` (class).
5. **Booleans should read like a yes/no question**: `isActive`, `hasPermission`, `canEdit` — avoid vague names like `flag` or `status`.
6. **Name length should scale with a variable's scope.** A variable living for 2–3 lines inside a short loop can be terse; a public variable/function used in many places needs a fully descriptive name.

## Convention by Identifier Type — pick one consistent scheme per project

No single convention is "objectively correct" — what matters is CONSISTENCY within one project, and respecting the default idiom of the language/framework in use:

| Identifier type | camelCase (TS/JS, Java, Dart...) | snake_case (Python, Ruby, PHP-DB) | PascalCase |
|---|---|---|---|
| Variables, parameters | `userName` | `user_name` | — |
| Functions/methods | `getUserById` | `get_user_by_id` | — |
| Classes/Interfaces/Types | — | — | `UserService`, `IPaymentGateway` |
| Constants | `TOKEN_LIFETIME_MS` (UPPER_SNAKE regardless of language) | `TOKEN_LIFETIME_MS` | — |
| Files | project-dependent: `user-service.ts` (kebab) or `user_service.py` (snake) or `UserService.cs` (Pascal, matching the class) | | |

**Rule for a new project**: use the DEFAULT convention of the primary language/framework (e.g., Python → snake_case for functions/variables per PEP8; TypeScript/JS → camelCase per Airbnb/Google style; Dart → lowerCamelCase per Effective Dart). Don't invent an unusual convention unless the team has already agreed on one.

## When Reviewing, Point to Specific Violations

Don't just say "naming could be clearer" — point at the exact line and propose a concrete replacement name. Examples:

- `const d = new Date()` → suggest `const createdAt = new Date()` if the variable represents a creation timestamp.
- `function process(data)` → too generic; ask what "process" specifically means, and propose a name reflecting the actual action (`normalizeUserInput`, `calculateShippingFee`...).
