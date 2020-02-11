# $Id$

.PHONY: run build clean lint lintrun dist

OS:=$(shell uname -s)

ifeq ($(OS),Darwin)
PYTHONDIR:=/System/Library/Frameworks/Python.framework/Versions/Current
export PYTHONPATH=$(wildcard $(PYTHONDIR)/lib/python*/site-packages)
PYTHONBINPREFIX:=$(PYTHONDIR)/bin/
APPCONTENTS:=derived/openMSX_Catapult.app/Contents
PY_DIR:=$(APPCONTENTS)/MacOS
RES_DIR:=$(APPCONTENTS)/Resources
else
PYTHONBINPREFIX:=
PY_DIR:=derived
RES_DIR:=derived
endif

ICONS:=$(wildcard res/*.png) $(wildcard res/*.icns) $(wildcard res/*.ico)
COPY_ICONS:=$(ICONS:res/%=$(RES_DIR)/%)

SOURCES:=$(wildcard src/*.py)
COPY_SRC:=$(SOURCES:src/%=$(PY_DIR)/%)

UI_DESIGNS:=$(wildcard res/*.ui)
UI_GEN_SRC:=$(UI_DESIGNS:res/%.ui=$(PY_DIR)/ui_%.py)

DIST_FILES:=Makefile $(SOURCES) $(ICONS) $(UI_DESIGNS) win32exe.py

CHANGELOG_REVISION=\
	$(shell sed -ne "s/\$$Id: ChangeLog \([^ ]*\).*/\1/p" ChangeLog)
VERSION=prerelease-$(CHANGELOG_REVISION)

# Default to build
build:

run: build
ifeq ($(OS),Darwin)
	open derived/openMSX_Catapult.app
else
	cd $(PY_DIR) && $(PYTHONBINPREFIX)python3 catapult.py
endif

#TODO make the *.db files dependend on *txt files and generate them
# for now launch autorunfilldb.py manually
dbfiles:
	cp tools/autorun.db $(PY_DIR)
	cp tools/softdb.db $(PY_DIR)
	cp tools/hwimages.db $(PY_DIR)

runcd: build dbfiles
ifeq ($(OS),Darwin)
	open derived/openMSX_Catapult.app --cd
else
	cd $(PY_DIR) && $(PYTHONBINPREFIX)python3 catapult.py --cd
endif

build: $(COPY_SRC) $(COPY_ICONS) $(UI_GEN_SRC)

$(COPY_SRC): $(PY_DIR)/%.py: src/%.py
	@mkdir -p $(@D)
	cp $< $@

$(COPY_ICONS): $(RES_DIR)/%: res/%
	@mkdir -p $(@D)
	cp $< $@

$(UI_GEN_SRC): $(PY_DIR)/ui_%.py: res/%.ui
	@mkdir -p $(@D)
	$(PYTHONBINPREFIX)pyuic5 $< -o $@

ifeq ($(OS),Darwin)
build: $(APPCONTENTS)/Info.plist $(APPCONTENTS)/PkgInfo $(APPCONTENTS)/MacOS/run.sh

$(APPCONTENTS)/MacOS/run.sh: build/package-darwin/run.sh
	mkdir -p $(@D)
	cp $< $@

$(APPCONTENTS)/Info.plist: build/package-darwin/Info.plist ChangeLog
	mkdir -p $(@D)
	sed -e 's/%VERSION%/$(VERSION)/' < $< > $@

$(APPCONTENTS)/PkgInfo:
	mkdir -p $(@D)
	echo "APPLoMXC" > $@
endif

clean:
	rm -rf derived

# Altough the generated sources are not checked, the modules that are checked
# import them and those import statements are checked.
lint: build
	cd src && PYTHONPATH=$(PYTHONPATH):../$(PY_DIR) pylint $(SOURCES:src/%.py=%.py)

lintrun: build
	@echo "Checking modified sources with PyLint..."
	@MODIFIED=`svn st | sed -ne 's/[AM]..... src\/\(.*\.py\)$$/\1/p'` && \
		if [ -n "$$MODIFIED" ]; then \
			cd src && ! PYTHONPATH=$(PYTHONPATH):../$(PY_DIR) pylint --errors-only $$MODIFIED | grep .; \
		fi
	make run

precommit: build
	@svn diff
	@MODIFIED=`svn st | sed -ne 's/[AM]..... src\/\(.*\.py\)$$/\1/p'` && \
		if [ -n "$$MODIFIED" ]; then \
			cd src && PYTHONPATH=$(PYTHONPATH):../$(PY_DIR) pylint -rn $$MODIFIED; \
		fi

dist:
	 zip catapult-$(VERSION).zip $(DIST_FILES)
