# Contributing to AI SOC Assistant

## Git Workflow

### Branch Strategy

| Branch | Purpose | Who works here |
|--------|---------|----------------|
| `main` | Stable, reviewed code only | Merged via PR |
| `backend` | FastAPI development | Shreerang |
| `big-data` | Kafka + Spark pipeline | Ayush Dandge |
| `ai-ml` | ML models | Sayog Shendre |
| `frontend` | React dashboard | Aryan Dandge |
| `database` | Schema and migrations | Sumiran Bagul |

### Feature Branch Naming

Always branch off your **module branch**, not `main`.

```
feature/<module>/<short-task-name>
```

Examples:
```
feature/backend/log-ingestion-api
feature/ai-ml/anomaly-detection-model
feature/frontend/alerts-dashboard
feature/database/schema-init
feature/big-data/kafka-consumer
```

### Step-by-Step Workflow

```bash
# 1. Switch to your module branch and pull latest
git checkout backend
git pull origin backend

# 2. Create a feature branch
git checkout -b feature/backend/health-endpoint

# 3. Make your changes, commit with a meaningful message
git add .
git commit -m "feat(backend): add /health endpoint with version info"

# 4. Push the feature branch
git push origin feature/backend/health-endpoint

# 5. Open a Pull Request: feature/backend/... → backend (NOT main)
# 6. After review and merge into backend, Shreerang opens a PR: backend → main
```

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short description>
```

| Type | When to use |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `chore` | Config, deps, tooling |
| `docs` | Documentation only |
| `refactor` | Code restructure, no behavior change |
| `test` | Adding or fixing tests |
| `style` | Formatting, linting |

Examples:
```
feat(backend): add /alerts endpoint with pagination
fix(kafka): handle consumer group rebalance error
docs(readme): update setup instructions
chore(deps): pin fastapi to 0.110.0
```

### Pull Request Rules

- PRs from feature branches go to the **module branch** (e.g. `feature/... → backend`)
- PRs from module branch to `main` are opened by **Shreerang only** after team review
- Every PR must have:
  - A clear title using the commit format above
  - A short description of what changed and why
  - At least **1 reviewer** (tag a teammate)
- Keep PRs small — one feature or fix per PR
- Do not merge your own PR without a review

### Branch Protection (main)

- Direct pushes to `main` are **disabled**
- All changes to `main` require a Pull Request
- At least 1 approval required before merge

### Merge Strategy

- **Squash and merge** for feature → module branch (keeps module branch history clean)
- **Merge commit** for module → main (preserves the full history of the phase)

## Code Standards

- Python: follow PEP 8, use type hints, add docstrings on all functions
- JS/React: ESLint + Prettier
- Always add or update tests when changing logic
- Never commit secrets, API keys, or `.env` files

## Questions?

Raise a GitHub Issue or ping Shreerang on the team group.
