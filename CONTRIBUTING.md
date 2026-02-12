# Contributing to Insight Stock Dashboard

Thank you for your interest in contributing! This guide will help you get started.

## Getting Started

1. **Fork** the repository
2. **Clone** your fork locally
3. **Create** a feature branch: `git checkout -b feature/my-feature`
4. **Follow** the setup instructions in [docs/SETUP.md](docs/SETUP.md)

## Development Workflow

### Frontend (React + TypeScript)

```bash
npm install
npm run dev          # Start dev server
npm run lint         # Run ESLint
npx tsc --noEmit     # Type check
npx vitest run       # Run tests
```

### Backend (Python + FastAPI)

```bash
cd backend
pip install -r requirements.txt
python main.py       # Start backend server
pytest               # Run tests
```

## Code Style

- **Frontend:** TypeScript strict mode, ESLint rules enforced
- **Backend:** PEP 8, type hints encouraged
- Write meaningful commit messages (imperative mood)

## Pull Request Process

1. Ensure your code passes lint and type checks
2. Update documentation if you change APIs
3. Add tests for new functionality
4. Request review from a maintainer

## Security

- **Never** commit secrets, API keys, or tokens
- All sensitive config goes in `.env` files only
- See [SECURITY.md](SECURITY.md) for vulnerability reporting

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
