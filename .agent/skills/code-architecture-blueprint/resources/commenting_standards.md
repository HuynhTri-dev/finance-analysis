# Commenting Standard

## Core Principle: Comments Explain WHY, Not WHAT

If the code already says what it does (thanks to good naming — see `naming_conventions.md`), you don't need a comment repeating it. A comment should answer "why is this code written this way," not "what does this code do" (that should be readable directly from the code).

```
// BAD — just restates the code, adds nothing
// Increment count by 1
count += 1;

// GOOD — explains the business reason
// Reset the retry counter after a successful API call so the
// circuit breaker doesn't incorrectly trip on the next valid request
count = 0;
```

## Comments Are Mandatory In These Cases

### 1. Core business purpose of a class/function

For important functions/classes (public API, containing business logic), a comment at the top should state: what business need this function serves, what its input/output is, and any side effects worth noting.

### 2. Magic Numbers & Magic Strings

A "bare" number or string that doesn't explain its own meaning must be extracted into a named constant, with a comment explaining how the value was derived (if there's a formula):

```typescript
// BAD: nobody knows what 86400000 means
const expiry = Date.now() + 86400000;

// GOOD
// 86400000 = 24 hours * 60 minutes * 60 seconds * 1000 ms (token lifetime)
const TOKEN_LIFETIME_MS = 86400000;
```

The same applies to magic strings: status codes as strings, object keys, error codes... should be named constants, not hardcoded in multiple places.

### 3. Workarounds & Hacks

When forced to write "ugly" or suboptimal code to work around a limitation of a framework, third-party library, or browser, you MUST document:
- Why this workaround is needed (which specific limitation, of what, in what version).
- Under what condition the workaround can be removed (e.g., "once we upgrade the framework to version X").

```typescript
// WORKAROUND: React 18 StrictMode calls useEffect twice in dev mode;
// this flag prevents a duplicate API call. Can be removed once we
// migrate to the framework's new fetch mechanism (see issue #123).
```

Purpose: so a future maintainer doesn't "clean up" code that looks redundant and accidentally breaks it.

### 4. TODO / FIXME / NOTE — use the standard tags correctly

- `// TODO:` — future work (refactoring, a new feature), not a current bug.
- `// FIXME:` — a known potential bug that hasn't been fixed yet due to time/priority constraints. Include a short description of when it triggers.
- `// NOTE:` — important context the reader needs before modifying this code (not a bug, not pending work).

Don't let TODO become a way to hide unbounded technical debt — link it to a tracked issue/ticket whenever possible.

### 5. Regex

Regex is nearly unreadable at a glance — always comment its purpose, and consider breaking complex regex into named parts (named capture groups or intermediate variables) if the language supports it.

```typescript
// Simplified RFC 5322-style email check:
// - local part: letters, digits, ., _, %, +, -
// - domain: letters, digits, ., - ; must contain at least one dot
const EMAIL_REGEX = /^[\w.%+-]+@[\w.-]+\.[A-Za-z]{2,}$/;
```

### 6. Input/Output of Important Public Functions

For functions called from many other places (a module/class's public API), document clearly: what each parameter is (type, constraints if any), what's returned, and what errors it may throw. In languages with strong static typing (TypeScript, Dart, Java...), the type signature already covers most of this — just add a comment for CONSTRAINTS the type system can't express (e.g., "email must already be validated before calling this function").

## When NOT to Comment

- A comment that just repeats what the variable/function name already says.
- A comment covering up bad code instead of fixing it (comments are not a substitute for good naming or clear function decomposition).
- A stale comment that no longer matches the current code — a wrong comment is worse than no comment, because it misleads. When reviewing, always check that comments still match the code.
