# Migration to uv Package Management

This project has been migrated from `requirements.txt` to `uv` for better package management.

## For New Users

1. Install uv if you haven't already:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Run the application:
   ```bash
   uv run python api/index.py
   ```

## For Existing Users

If you were using the old `venv/` setup:

1. Deactivate your old virtual environment:
   ```bash
   deactivate
   ```

2. Install uv (if needed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. Run with uv (it will automatically create `.venv/` and install dependencies):
   ```bash
   uv run python api/index.py
   ```

4. Optional: Remove old virtual environment:
   ```bash
   rm -rf venv/
   rm requirements.txt  # No longer needed
   ```

## Benefits of uv

- ⚡ Much faster dependency resolution and installation
- 🔒 Better dependency locking and reproducibility  
- 🛠️ Integrated project management
- 📦 Modern Python packaging standards

## Running Tests

```bash
uv run python test_planner.py
```

## Development

```bash
# Add new dependencies
uv add package-name

# Add development dependencies  
uv add --dev pytest black flake8

# Run with specific Python version
uv run --python 3.10 python api/index.py
``` 