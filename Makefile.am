SUBDIRS = EosAppStore data

bin_SCRIPTS = eos-app-store

do_subst = sed -e 's|@pkglibdir[@]|$(pkglibdir)|g' \
               -e 's|@pkgdatadir[@]|$(pkgdatadir)|g' \
               -e 's|@GJS_CONSOLE[@]|$(GJS_CONSOLE)|g'

eos-app-store: eos-app-store.in Makefile
	$(AM_V_GEN) $(do_subst) $< > $@
	chmod +x $@

CLEANFILES = eos-app-store
EXTRA_DIST = eos-app-store.in
