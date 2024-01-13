# Contributing Guide

You will need:
- Python 3.7 or higher

## Getting started

To get your development environment set up, create and activate a virtual
environment, and install poetry:

```
pipx install poetry
# or with conda
conda install poetry
```

Then install dependencies with poetry:

```sh
poetry install
```

This will install the repo version of
`graphene-pydantic` and then install the development dependencies. Once that
has completed, you can start developing.

### Running tests

To run the tests locally, you can simply run `pytest`.

In CI, we run tests using [nox](https://nox.thea.codes/en/stable/index.html),
which runs the test multiple times using different package versions. Run
`poetry run nox` to run the entire test suite.

### Pre-commit, linting

We use [pre-commit](https://pre-commit.com/) to manage git pre-commit hooks. This
will fail linting locally so you can see errors before they run in CI. Run `pre-commit install`
to install the hooks.

To run them manually, run `pre-commit run --all-files`.

To skip them when committing, run `git commit` with the `--no-verify` flag.
