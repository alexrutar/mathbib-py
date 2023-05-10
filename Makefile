SHELL := /usr/local/bin/fish

.PHONY: upload test format test-type

upload: format test
	python -m build
	TWINE_USERNAME="__token__" TWINE_PASSWORD=(keyring get pypi_texproject_token alexrutar) twine upload dist/*

test:
	mypy .
	pytest --run-slow

format:
	black . --target-version py311 --preview
	flake8 src/mathbib/
