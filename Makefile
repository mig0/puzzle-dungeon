PACKAGE = puzzle-dungeon
VERSION = 0.3.0
SUFFIX = -custom
distdir = $(PACKAGE)-$(VERSION)$(SUFFIX)

prefix = /usr/local
bindir = $(prefix)/bin
datadir = $(prefix)/share
PKG_DATADIR = $(datadir)/$(PACKAGE)
DESTDIR =

INSTALL = install
PYTHON = python
CHMOD = chmod
SED = sed
TAR = tar
ZIP = zip
RM = rm

all: check-dependencies
	@echo ""
	@echo "You may install the game using one of the following commands:"
	@echo ""
	@echo "    make install                 # use the default prefix $(prefix)"
	@echo "    make install prefix=~/puzzle-dungeon"
	@echo "    make install bindir=/opt/bin datadir=/opt/share PYTHON=/usr/bin/python3"
	@echo ""
	@echo "If you don't change the prefix, then 'dungeon' script is installed"
	@echo "into $(bindir) and the game data into $(PKG_DATADIR) ."
	@echo ""

check-dependencies:
	@$(PYTHON) --version 2>/dev/null | grep -q 'Python 3' || \
		echo "! Looks like $(PYTHON) is missing or not version 3"
	@$(PYTHON) -c 'import pgzero' >/dev/null 2>&1 || \
		echo "! Looks like $(PYTHON) module pgzero is missing"
	@$(PYTHON) -c 'import pygame' >/dev/null 2>&1 || \
		echo "! Looks like $(PYTHON) module pygame is missing"
	@$(PYTHON) -c 'import bitarray' >/dev/null 2>&1 || \
		echo "! Looks like $(PYTHON) module bitarray is missing"

install: check-dependencies
	$(INSTALL) -d $(DESTDIR)$(bindir)
	$(INSTALL) dungeon $(DESTDIR)$(bindir)
	$(INSTALL) -d $(DESTDIR)$(datadir)
	$(INSTALL) -d $(DESTDIR)$(PKG_DATADIR)
	$(INSTALL) -d $(DESTDIR)$(PKG_DATADIR)/images
	$(INSTALL) -d $(DESTDIR)$(PKG_DATADIR)/info
	$(INSTALL) -d $(DESTDIR)$(PKG_DATADIR)/maps
	$(INSTALL) -d $(DESTDIR)$(PKG_DATADIR)/music
	@for dir in bg images info/puzzles maps music pictures sounds; do \
		for file in `find $$dir -follow -type f -print`; do \
			echo install: $(DESTDIR)$(PKG_DATADIR)/$$file; \
			$(INSTALL) -d -m 755 `dirname $(DESTDIR)$(PKG_DATADIR)/$$file`; \
			$(INSTALL) -m 644 $$file $(DESTDIR)$(PKG_DATADIR)/$$file; \
		done; \
	done
	@for dir in . puzzle; do \
		$(INSTALL) -d -m 755 $(DESTDIR)$(PKG_DATADIR)/$$dir; \
		for file in `find $$dir -name '*.py' -print`; do \
			echo install: $(DESTDIR)$(PKG_DATADIR)/$$file; \
			$(INSTALL) -m 644 $$file $(DESTDIR)$(PKG_DATADIR)/$$file; \
		done; \
	done
	$(SED) -i 's|DATA_DIR = "."|DATA_DIR = "$(PKG_DATADIR)"|' $(DESTDIR)$(PKG_DATADIR)/config.py
	$(SED) -i 's|pgzrun main.py|pgzrun "$(PKG_DATADIR)"/main.py|' $(DESTDIR)$(bindir)/dungeon

uninstall:
	$(RM) $(DESTDIR)$(bindir)/dungeon
	$(RM) -r $(DESTDIR)$(PKG_DATADIR)

web:
	@tools/create-all-html-pages

web-local:
	@base= tools/create-all-html-pages

web-redirect:
	@tools/create-all-html-pages -r

web-refresh:
	@tools/create-all-html-pages -R

dist: check-dependencies
	@echo "Creating $(distdir)"
	@$(RM) -rf $(distdir)
	@$(INSTALL) -d -m 00755 $(distdir)
	@for file in `git ls | grep -v -E '^(html|elements|info/screenshots|info/videos|tools|.gitignore)'`; do \
		$(INSTALL) -D -m 644 $$file $(distdir)/$$file; \
	done
	@$(INSTALL) -t $(distdir) dungeon
	@echo "Creating $(distdir).tar.gz"
	@$(TAR) --owner root --group root -czf $(distdir).tar.gz $(distdir)
	@echo "Creating $(distdir).zip"
	@$(ZIP) -FSrq $(distdir).zip $(distdir)

rpm:
	@echo "This functionality is not implemented yet"

