# AGENTS.md

This repo is a multi-package monorepo for Flash (async-first Dash), with
Python packages plus several JS/TS component packages and the Dash renderer.
The most important code lives in `flash-package/`, which implements Quart-based
backend changes and Flash-only features like async/event callbacks.
Follow local package configs when working inside subdirectories.

## Repo layout (high level)
- `flash-package/`: Python package for dash-flash (Poetry). Primary backend.
- `dash/`: upstream Dash code; only `dash/background_callback/` and
  `dash/development/` are relevant for this repo's backend work.
- `components/`, `dash/dash-renderer`, `dash_table`, `dcc`, `html`: ignore for
  Flash backend changes unless explicitly asked.
- `@plotly/`: ignore unless explicitly asked.
- `tests/`: ignore for backend work unless explicitly asked.

## Build / lint / test commands
Use the root scripts when possible; they orchestrate multiple subpackages.

flash-package (from `flash-package/`)
- JS/TS format/lint/build: use local `package.json` scripts.
- Python packaging: Poetry config in `flash-package/pyproject.toml`.

## Code style and conventions

General formatting
- EditorConfig: LF line endings, final newline, 4-space indent for `*.py`/`*.js`.
- `package.json` and `.circleci/config.yml` use 2-space indent.
- Prefer ASCII in new edits; keep existing encoding otherwise.

Python style
- Formatting is enforced by Black (default Black line length unless overridden).
- Indentation: 4 spaces; no tabs.
- Naming per `pylint` config:
  - `snake_case` for functions, methods, variables, and modules.
  - `PascalCase` for classes.
  - `UPPER_CASE` for constants.
  - Allowed short names include `i`, `j`, `k`, `ex`, `Run`, `_`.
- Unused args/variables should start with `_` (see pylint ignored patterns).
- Avoid unused imports; keep `__init__.py` exports tidy even if lint is lenient.
- Docstrings are not required everywhere (pylint missing-docstring disabled),
  but add them for public APIs or non-obvious behavior.

Python imports
- Prefer explicit imports; avoid wildcard imports unless module defines `__all__`.
- Group imports as: standard library, third-party, local (PEP 8 order).

Python error handling
- Use specific exception classes; avoid broad `except Exception` unless you
  re-raise or add context.
- Preserve stack traces when re-raising; prefer `raise ... from e` when needed.

JavaScript/TypeScript style
- Use Prettier and ESLint where configured in each package.
- Indentation is 4 spaces in JS/TS files per EditorConfig.
- Local Prettier configs vary by package:
  - `components/dash-core-components/.prettierrc`: single quotes, no bracket
    spacing, trailing comma `es5`.
  - `components/dash-table/.prettierrc`: single quotes, no bracket spacing,
    trailing comma `none`.
  - `dash/dash-renderer`: uses `@plotly/prettier-config-dash`.
- Always run format/lint in the package you changed if it has scripts.

JS/TS lint rules (common patterns)
- No `console.*` in renderer packages (ESLint `no-console`).
- Prefer `const` over `let` when possible.
- Avoid `eval` and `with`.
- No unused vars; prefix unused parameters with `_`.
- Avoid magic numbers unless listed in allowed set (see ESLint config).

TypeScript
- `dash/dash-renderer/tsconfig.json` is strict:
  - `strict`, `noImplicitAny`, `noUnusedLocals`, `noUnusedParameters` enabled.
- Prefer explicit types for exported/public APIs; avoid `any`.

React conventions (renderer/components)
- Use React best practices enforced by ESLint:
  - No direct state mutation.
  - Use ES6 classes where applicable.
  - PropTypes are required in JS components.

## Working in this repo
The primary goal is to maintain a Quart-based backend and Flash-only features
that extend Dash (e.g., async event callbacks and streaming). When working on
backend behavior, always compare against the canonical Flash implementation in
`flash-package/flash/` and update it first; Dash changes are upstream inputs.

When merging upstream Dash changes
- Focus on `dash/background_callback/` and `dash/development/` only; ignore
  renderer/components (`dash-renderer`, `dash_table`, `dcc`, `html`),
  `@plotly/`, and Dash tests unless explicitly asked.
- Identify which Dash files changed in those areas and find the corresponding
  counterparts in `flash-package/flash/`.
- Port changes while preserving Quart behavior and Flash-specific features.
- Re-check async pathways, SSE streaming, and callback/event semantics.

Key Flash backend areas (start here)
- `flash-package/flash/flash.py`: app initialization and main API surface.
- `flash-package/flash/_callback.py`: core callback plumbing.
- `flash-package/flash/_event_callback.py`: async event callbacks + streaming.
- `flash-package/flash/SSE.py`: Server-Sent Events transport.
- `flash-package/flash/_hooks.py`: lifecycle hooks.
- `flash-package/flash/_get_app.py`: app retrieval and wiring.

## Tooling notes
- Root `npm run lint` and `npm run format` orchestrate multiple subpackages.
- `npm run test` runs Python tests and renderer tests (see root `package.json`).
- If a package has its own `package.json`, prefer its scripts over ad-hoc commands.

## Cursor / Copilot rules
- No `.cursor/rules`, `.cursorrules`, or `.github/copilot-instructions.md` found.

## When adding new files
- Match the local package style (prettier/eslint/black settings).
- Keep file names `snake_case.py` for Python and `kebab-case` or existing
  conventions for JS/TS in that package.
- Update or add tests alongside behavior changes.
