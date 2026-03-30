.PHONY: build test lint format typecheck check quality clean install deps-check

install:
	cd frontend && npm install
	cd backend && pip install -e ".[dev]"

build:
	cd frontend && npx tsc && npx vite build

test:
	cd frontend && npx vitest run
	cd backend && pytest

lint:
	cd frontend && npx oxlint . && npx biome check .
	cd backend && ruff check .

format:
	cd frontend && npx biome format --write .
	cd backend && ruff format . && ruff check --fix .

typecheck:
	cd frontend && npx tsc --noEmit

check: format lint typecheck test build
	@echo "All checks passed."

quality:
	@echo "=== Quality Gate ==="
	@test -f LICENSE || { echo "ERROR: LICENSE missing. Fix: add MIT LICENSE file"; exit 1; }
	@! grep -rn "TODO\|FIXME\|HACK\|console\.log\|println\|print(" frontend/src/ backend/src/ 2>/dev/null | grep -v "node_modules" || { echo "ERROR: debug output or TODO found. Fix: remove before ship"; exit 1; }
	@! grep -rn "password=\|secret=\|api_key=\|sk-\|ghp_" frontend/src/ backend/src/ 2>/dev/null | grep -v '\$${' | grep -v "node_modules" || { echo "ERROR: hardcoded secrets. Fix: use env vars with no default"; exit 1; }
	@test ! -f PRD.md || ! grep -q "\[ \]" PRD.md || { echo "ERROR: unchecked acceptance criteria in PRD.md"; exit 1; }
	@echo "OK: automated quality checks passed"
	@echo "Manual checks required: README quickstart, demo GIF, input validation, ADR >=1"

deps-check:
	cd frontend && npx knip || echo "WARN: unused dependencies detected"
	cd backend && ruff check --select F401 . || echo "WARN: unused imports detected"

clean:
	cd frontend && rm -rf dist/ coverage/ node_modules/.cache/
	cd backend && find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	cd backend && find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	cd backend && rm -rf .coverage htmlcov/
