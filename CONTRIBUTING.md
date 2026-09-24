# Reproducibility questions and contributions

Use GitHub issues for questions, documentation corrections and reproducibility problems. Include the repository commit or release, your operating system, R and Python versions, the command you ran and its error output. Do not attach unpublished data or credentials.

Start with the analysis README. Run `uv sync --locked`, then `uv run python -m unittest discover -s analysis -p 'test_release_schema.py'` to check the included analysis schemas. Changes to archive utilities should also pass `uv run python -m unittest discover -s tools -p 'test_*.py'`. The GitHub workflow runs these checks.

Saved manuscript figures and model outputs correspond to the submitted paper. Do not replace them as a side effect of a documentation change or dependency update. For analytical changes, preserve the submitted release and describe the input changes, model changes and numerical comparisons explicitly. Keep original annotation archives unchanged.

The manuscript and USGS observational release are distinct products. Repository maintenance does not itself update the canonical USGS release or its reviewed metadata.
