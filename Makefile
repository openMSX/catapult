# $Id$

.PHONY: run build clean lint lintrun dist

ICONS:=$(wildcard res/*.png)
COPY_ICONS:=$(ICONS:res/%=derived/%)

SOURCES:=$(wildcard src/*.py)
COPY_SRC:=$(SOURCES:src/%=derived/%)

UI_DESIGNS:=$(wildcard res/*.ui)
UI_GEN_SRC:=$(UI_DESIGNS:res/%.ui=derived/ui_%.py)

DIST_FILES:=Makefile $(SOURCES) $(ICONS) $(UI_DESIGNS) win32exe.py

run: build
	cd derived && python catapult.py

build: $(COPY_SRC) $(COPY_ICONS) $(UI_GEN_SRC)

$(COPY_SRC): derived/%.py: src/%.py
	@mkdir -p derived
	cp $< $@

$(COPY_ICONS): derived/%: res/%
	@mkdir -p derived
	cp $< $@

$(UI_GEN_SRC): derived/ui_%.py: res/%.ui
	@mkdir -p derived
	pyuic4 $< -o $@

clean:
	rm -rf derived

# Altough the generated sources are not checked, the modules that are checked
# import them and those import statements are checked.
lint: build
	cd src && PYTHONPATH=../derived pylint $(SOURCES:src/%.py=%.py)

lintrun: build
	@echo "Checking modified sources with PyLint..."
	@MODIFIED=`svn st | sed -ne 's/[AM]..... src\/\(.*\.py\)$$/\1/p'` && \
		if [ -n "$$MODIFIED" ]; then \
			cd src && ! PYTHONPATH=../derived pylint --errors-only $$MODIFIED | grep .; \
		fi
	cd derived && python catapult.py

precommit: build
	@svn diff
	@MODIFIED=`svn st | sed -ne 's/[AM]..... src\/\(.*\.py\)$$/\1/p'` && \
		if [ -n "$$MODIFIED" ]; then \
			cd src && PYTHONPATH=../derived pylint -rn $$MODIFIED; \
		fi

dist:
	 zip catapult-$(shell date +%Y-%m-%d-%H-%M).zip $(DIST_FILES)
