# $Id$

.PHONY: run build clean lint lintrun dist

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
	rm -f $(UI_GEN_SRC) *.pyc *.pyo

# Altough the generated sources are not checked, the modules that are checked
# import them and those import statements are checked.
lint: build
	pylint $(SOURCES)

lintrun: build
	@echo "Checking modified sources with PyLint..."
	@MODIFIED=`svn st | sed -ne 's/[AM]..... \(.*\.py\)$$/\1/p'` && \
		if [ -n "$$MODIFIED" ]; then \
			! pylint --debug-mode $$MODIFIED | grep .; \
		fi
	python catapult.py

precommit: build
	@svn diff
	@MODIFIED=`svn st | sed -ne 's/[AM]..... \(.*\.py\)$$/\1/p'` && \
		if [ -n "$$MODIFIED" ]; then \
			pylint -rn $$MODIFIED; \
		fi

dist:
	 zip $(shell date +%Y-%m-%d-%H-%M).zip $(DIST_FILES)
