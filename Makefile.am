SUBDIRS = EosAppStore images

bin_SCRIPTS = eos-app-store

eos-app-store: eos-app-store.in Makefile
	$(AM_V_GEN)sed -e s!\@PYTHON\@!@PYTHON@!	\
	    -e s!\@PYOPTIONS\@!-OOt!			\
	    -e s!\@DATADIR\@!${datadir}!		\
	    < $< > $@
	chmod +x $@

CLEANFILES = eos-app-store
EXTRA_DIST = eos-app-store.in
