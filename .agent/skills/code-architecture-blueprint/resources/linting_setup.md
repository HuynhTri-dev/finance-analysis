# Linting & Formatting by Ecosystem

Goal: eliminate style debates (single vs. double quotes, indentation width, brace placement) with shared configuration, so code review can focus on logic instead of style.

## TypeScript / JavaScript

- **Linter**: ESLint (use the flat config `eslint.config.js` for newer versions).
- **Formatter**: Prettier — kept separate from ESLint (use `eslint-config-prettier` to disable overlapping style rules in ESLint).
- Config files: `.eslintrc.json`/`eslint.config.js`, `.prettierrc`.
- Popular base configs: `eslint-config-airbnb-typescript` or `@typescript-eslint/recommended`, depending on how strict the team wants to be.

## Python

- **Linter**: Ruff (fast, replaces Flake8 + isort + most popular plugins) or traditional Flake8.
- **Formatter**: Black (or Ruff's formatter — same toolchain as the linter).
- **Static type checking**: mypy or pyright if the project relies heavily on type hints.
- Config file: `pyproject.toml` (under `[tool.ruff]`, `[tool.black]`).

## Dart / Flutter

- **Linter**: the built-in linter configured via `analysis_options.yaml`, using the `lints` or `flutter_lints` package as a base.
- **Formatter**: `dart format` (built-in, no extra install needed).

## Java

- **Linter**: Checkstyle or SpotBugs (bug-pattern detection, distinct from a style linter).
- **Formatter**: google-java-format or Spotless (integrates with Maven/Gradle).

## C# / .NET

- **Integrated linter/formatter**: `dotnet format` + `.editorconfig` (style rules defined directly in `.editorconfig`, respected by Visual Studio/Rider).
- Can be supplemented with Roslyn Analyzers for stricter rules.

## Go

- **Formatter**: `gofmt`/`goimports` (built-in, no configuration options — this is intentional in Go: no style debates).
- **Linter**: `golangci-lint` (bundles many popular linters into one tool).

## General Principles for Setting Up a New Project

1. Pick a popular community base config (Airbnb, Google style...) instead of writing one from scratch — this cuts down on style debates.
2. Commit the config file to the repo (`.eslintrc`, `analysis_options.yaml`, `pyproject.toml`...) so every team member uses the same setup, instead of everyone configuring their IDE independently.
3. Wire lint/format into a pre-commit hook (Husky + lint-staged for JS/TS, the `pre-commit` framework for Python...) or the CI pipeline to block non-compliant code before merge, rather than relying on manual reminders during review.
4. Don't use a linter as a substitute for code review — a linter catches style issues and some basic bug patterns, but it can't evaluate design/architecture (that's the job of Workflow C in `SKILL.md`).
