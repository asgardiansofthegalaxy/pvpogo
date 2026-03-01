# AGENTS.md - PvPogo Development Guide

This repository contains two main components:
- **Frontend**: React + TypeScript + Next.js (App Router) + HeroUI + Tailwind CSS
- **Backend**: Python (pypogo) with Django

---

## Build, Lint, and Test Commands

### Frontend (npm - in root directory)

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Start production server
npm run start

# Lint code (ESLint with Next.js)
npm run lint
```

### Backend (Python - in pypogo directory)

```bash
cd pypogo

# Install dependencies
pip install -e .

# Run all Python tests with pytest
pytest

# Run a single test file
pytest pypogo/tests/test_battle.py

# Run a specific test
pytest pypogo/tests/test_battle.py::test_battle_turn_order

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=pypogo --cov-report=html
```

---

## Code Style Guidelines

### TypeScript / React / Next.js (Frontend)

**General:**
- Use strict TypeScript (`strict: true` in tsconfig.json)
- Use Next.js App Router (`app/` directory)
- Use functional components with arrow functions or `function` keyword
- Add `"use client"` directive for client-side components
- Component files should be PascalCase (e.g., `ContactForm.tsx`)

**Imports:**
- Use `@/*` alias for local modules (`@/components/Component`)
- Use package imports for external libraries (`@heroui/react`, `@formspree/react`)
- Order: external imports, blank line, local imports

**Formatting:**
- Use 2 spaces for indentation
- Max line length: 100 characters (soft limit)
- Use double quotes for strings in JSX, single quotes elsewhere
- Trailing commas in arrays and objects

**HeroUI Components:**
- Use HeroUI components instead of raw HTML elements
- Examples: `<Button>`, `<Input>`, `<Card>`, `<Modal>`, etc.
- Configure HeroUIProvider in `app/layout.tsx`

**Types:**
- Always define types for props, state, and function parameters
- Use interfaces for object shapes
- Use `readonly` for immutable arrays/objects

**Naming:**
- Components: PascalCase
- Functions/variables: camelCase
- Constants: SCREAMING_SNAKE_CASE
- File names: kebab-case for utilities, PascalCase for components

**Error Handling:**
- Use try/catch for async operations
- Display user-friendly error messages in UI
- Log errors to console for debugging

**Tailwind CSS:**
- Use utility classes for styling
- Common pattern: `className="flex flex-col items-center"`
- Use responsive prefixes: `md:text-xl`, `lg:text-2xl`

### Python (Backend)

**General:**
- Follow PEP 8 style guide
- Use type hints (as seen in `battle.py`)
- Use absolute imports within the package (`from pypogo.pokemon import ...`)
- Use relative imports for intra-package imports (`from .constants import ...`)

**Naming:**
- Classes: PascalCase (e.g., `PvpBattle`)
- Functions/variables: snake_case
- Constants: SCREAMING_SNAKE_CASE
- Private methods: prefix with underscore

**Types:**
- Use Python type hints for all function signatures
- Use `typing` module for complex types (`List`, `Dict`, `Optional`)
- Example: `def __init__(self, player_one: Player, player_two: Player) -> None:`

**Formatting:**
- 4 spaces for indentation
- Max line length: 100 characters
- Two blank lines between top-level definitions
- One blank line between method definitions

**Error Handling:**
- Use custom exceptions for domain-specific errors
- Catch specific exceptions, avoid bare `except:`
- Include meaningful error messages

**Testing:**
- Use `pytest` as the test framework
- Test files in `pypogo/tests/` directory
- Naming convention: `test_*.py`
- Use descriptive test function names: `test_battle_turn_order`

---

## Project Structure

```
pvpogo/
├── app/                       # Next.js App Router
│   ├── layout.tsx             # Root layout with HeroUIProvider
│   ├── page.tsx               # Main page
│   └── globals.css            # Global styles with Tailwind
├── public/                    # Static assets
│   └── sunflower-bg.jpg       # Background image
├── pypogo/                    # Python backend
│   ├── pypogo/
│   │   ├── battle.py
│   │   ├── pokemon.py
│   │   ├── player.py
│   │   ├── moves.py
│   │   ├── ai/
│   │   ├── game_master/
│   │   └── tests/
│   └── pokexperience/         # Django web app
├── package.json
├── tsconfig.json
├── tailwind.config.js
├── postcss.config.js
├── next.config.js
└── AGENTS.md
```

---

## Common Development Tasks

### Adding a new React component
1. Create file in `app/components/` with PascalCase name
2. Add `"use client"` directive if using hooks or HeroUI interactive components
3. Define props interface with TypeScript
4. Export as default
5. Import in parent component using `@/components/Component` alias

### Adding a new page
1. Create file in `app/` with PascalCase name (e.g., `about/page.tsx`)
2. Use Next.js file-based routing

### Adding a new Python module
1. Create file in `pypogo/pypogo/`
2. Add type hints to all functions
3. Create corresponding test file in `pypogo/pypogo/tests/`
4. Run `pytest` to verify

### Running full test suite
```bash
# Frontend
npm run lint

# Backend
cd pypogo && pytest
```

---

## Notes

- Frontend uses Next.js 14 with App Router and HeroUI component library
- HeroUI provides theming, dark mode, and accessible components
- Backend uses Python with pytest for testing
- No pre-commit hooks currently configured
- ESLint is configured with Next.js support
