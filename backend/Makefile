# Author: noi.narisak@gmail.com
# Date:
# Desc: Base makefile template for Python development
# v1: Init

.ONESHELL:
.SHELL := /usr/bin/bash
.DEFAULT_GOAL := help

ROOT_PATH := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/../..)

venv: venv/bin/activate

venv/bin/activate: requirements
	@echo "+ $@"
	@test -d venv || python -m venv venv
	@source venv/bin/activate; pip install -Ur requirements/dev.txt
	@touch venv/bin/activate

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-16s\033[0m %s\n", $$1, $$2}'

.PHONY: clean
clean: ## Clean up
	@echo "+ $@"
	@find . -type f -name '*.pyc' -exec rm -f {} +
	@find . -type d -name '*__pycache__*' -exec rm -rf {} +
	@find . -type d -name 'venv' -exec rm -rf {} +

.PHONY: build
build: clean venv ## Build
	@echo "+ $@"

.PHONY: lint
lint: venv ## Linting
	@echo "+ $@"
	@source venv/bin/activate; flake8

.PHONY: ngork
ngrok: ## Run ngrok to expose services locally
	@echo "+ $@"
	ngrok http 5000 -host-header="localhost:5000"

.PHONY: run
run: venv ## Run
	@echo "+ $@"
	@source venv/bin/activate; python manage.py runserver

.PHONY: test
test: venv ## Run test
	@echo "+ $@"
	@source venv/bin/activate; nosetests project/test
