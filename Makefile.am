SUBDIRS = data EosAppStore images

bin_SCRIPTS = eos-app-store eos-fill-desktop eos-reset-desktop

eos-app-store: eos-app-store.in Makefile
	$(AM_V_GEN)sed -e s!\@PYTHON\@!@PYTHON@!	\
	    -e s!\@PYOPTIONS\@!-OOt!			\
	    -e s!\@DATADIR\@!${datadir}!		\
	    < $< > $@
	chmod +x $@

eos-fill-desktop: eos-fill-desktop.in Makefile
	$(AM_V_GEN)sed -e s!\@PYTHON\@!@PYTHON@!	\
	    -e s!\@PYOPTIONS\@!-OOt!			\
	    -e s!\@DATADIR\@!${datadir}!		\
	    < $< > $@
	chmod +x $@

eos-reset-desktop: eos-reset-desktop.in Makefile
	$(AM_V_GEN)sed -e s!\@PYTHON\@!@PYTHON@!	\
	    -e s!\@PYOPTIONS\@!-OOt!			\
	    -e s!\@DATADIR\@!${datadir}!		\
	    < $< > $@
	chmod +x $@

CLEANFILES = eos-app-store eos-fill-desktop eos-reset-desktop
EXTRA_DIST = eos-app-store.in eos-fill-desktop.in eos-reset-desktop.in
