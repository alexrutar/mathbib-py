SHELL := /usr/local/bin/fish

.PHONY: publish test format test-type

publish: format test
	git tag v(poetry version --short) -m "Poetry build"
	POETRY_PYPI_TOKEN_PYPI=(keyring get pypi_mathbib_token alexrutar) poetry publish --build

test:
	# mypy .
	# pytest --run-slow

format:
	black . --target-version py311 --preview
	flake8 mathbib/
