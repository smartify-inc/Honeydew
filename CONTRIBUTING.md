# Contributing to HoneyDew

<p align="center">
  <img src="docs/assets/honeydew-logo-2.png" alt="HoneyDew logo" width="400" />
</p>

Thanks for your interest in contributing! Here's how to get started.

## Development Setup

1. **Clone the repo** and run the installer:

   ```bash
   ./install.sh
   ```

   This installs all dependencies and creates `config.json` from the example.

2. **Edit `config.json`** to set your user/agent names and boards.

3. **Start the app:**

   ```bash
   ./start.sh
   ```

## Running Tests

**API tests** (run from `backend/`):

```bash
cd backend
pip install -r requirements-dev.txt
python -m pytest tests/ -v
```

**Install and start scripts** — verify that `./install.sh` and `./start.sh --check-only` succeed:

```bash
./scripts/test_install_start.sh
```

Or run the full test suite; it includes an integration test that runs install and start pre-flight (`test_install_start.py`).

## Submitting Changes

1. Fork the repo and create a branch from `main`.
2. Make your changes and add or update tests as needed.
3. Run the test suite and make sure all tests pass.
4. Open a pull request with a clear description of what you changed and why.

## Reporting Issues

Open a [GitHub issue](https://github.com/smartify-inc/Honeydew/issues) or contact [dev@smartify.ai](mailto:dev@smartify.ai) (Smartify Inc.). For issues, please include:

- A clear title and description.
- Steps to reproduce (if it's a bug).
- Expected vs. actual behavior.

## Code Style

- **Python**: Follow PEP 8. Use type hints where practical.
- **TypeScript/React**: Follow the existing ESLint config (`npm run lint`).
- Keep commits focused — one logical change per commit.
