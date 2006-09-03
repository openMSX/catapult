# $Id$

.PHONY: run build clean lint dist

UI_DESIGNS:=$(wildcard *.ui)
UI_GEN_SRC:=$(UI_DESIGNS:%.ui=ui_%.py)

SOURCES:=$(filter-out $(UI_GEN_SRC),$(wildcard *.py))
DIST_FILES:=Makefile $(UI_DESIGNS) $(SOURCES) $(wildcard *.png)

run: build
	python catapult.py

build: $(UI_GEN_SRC)

$(UI_GEN_SRC): ui_%.py: %.ui
	pyuic4 $< -o $@

clean:
	rm $(UI_GEN_SRC)

# Altough the generated sources are not checked, the modules that are checked
# import them and those import statements are checked.
lint: build
	pylint $(SOURCES)

dist:
	 zip $(shell date +%Y-%m-%d-%H-%M).zip $(DIST_FILES)
