# $Id$

.PHONY: run lint dist

UI_DESIGNS:=$(wildcard *.ui)
UI_GEN_SRC:=$(UI_DESIGNS:%.ui=ui_%.py)

run: $(UI_GEN_SRC)
	python catapult.py

$(UI_GEN_SRC): ui_%.py: %.ui
	pyuic4 $< -o $@

SOURCES:=$(filter-out $(UI_GEN_SRC),$(wildcard *.py))
DIST_FILES:=Makefile $(UI_DESIGNS) $(SOURCES) $(wildcard *.png)

lint:
	pylint $(SOURCES)

dist:
	 zip $(shell date +%Y-%m-%d-%H-%M).zip $(DIST_FILES)
