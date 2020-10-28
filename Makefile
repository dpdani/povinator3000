#!/usr/bin/make -f

SHELL := /bin/bash

.PHONY: install start update

install:
	git clone https://github.com/dpdani/povinator3000.git
	cd povinator3000
	python3 -m venv .venv
	source .venv/bin/activate && pip install -r requirements.txt

start:
	source .venv/bin/activate && python -m povinator3000 $(bind)

stop:
	source .venv/bin/activate && python stop-povinator.py

update:
	git pull

upgrade: stop update start

clear-downloads:
	find ./downloads -type f -name '*.zip' -exec rm {} +
