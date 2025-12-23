export PROJECTNAME=$(shell basename "$(PWD)")

.SILENT: ;               # no need for @

deps: ## Install dependencies
	uv sync

pre-commit: ## Manually run all precommit hooks
	uv run pre-commit install
	uv run pre-commit run --all-files

pre-commit-tool: ## Manually run a single pre-commit hook
	uv run pre-commit run $(TOOL) --all-files

clean: ## Clean package
	find . -type d -name '__pycache__' | xargs rm -rf
	rm -rf build dist

package: clean pre-commit ## Run installer
	uv run pyinstaller main.spec

setup: ## Re-initiates virtualenv
	@make install-macosx
	@echo "Installation completed"

install-macosx: package ## Installs application in users Application folder
	./scripts/install-macosx.sh ActiveBreaks.app

.PHONY: help
.DEFAULT_GOAL := help

help: Makefile
	echo
	echo " Choose a command run in "$(PROJECTNAME)":"
	echo
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
	echo
