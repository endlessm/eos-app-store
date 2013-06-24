jsdir = $(pkgdatadir)/js/
dist_js_DATA = \
	$(BUILT_SOURCES) \
	appStoreWindow.js \
	appStore.js \
	builder.js \
	frameClock.js \
	main.js \
	params.js \
	$(NULL)

do_subst = sed -e 's|@pkgdatadir[@]|$(pkgdatadir)|g'
path.js: Makefile path.js.in
	$(AM_V_GEN) $(do_subst) $(srcdir)/path.js.in > $@

BUILT_SOURCES = \
	path.js \
	$(NULL)

EXTRA_DIST = \
	path.js.in \
	$(NULL)
