ACLOCAL_AMFLAGS = -I m4 ${ACLOCAL_FLAGS}

SUBDIRS = EosAppStore data po

# Preamble
bin_SCRIPTS =
EXTRA_DIST =
CLEANFILES =
DISTCLEANFILES =

EXTRA_DIST += \
	autogen.sh \
	COPYING \
	NEWS

# launcher
bin_SCRIPTS += eos-app-store

do_subst = $(SED) \
	-e 's|@pkglibdir[@]|$(pkglibdir)|g' \
	-e 's|@pkgdatadir[@]|$(pkgdatadir)|g' \
	-e 's|@GJS_CONSOLE[@]|$(GJS_CONSOLE)|g'

eos-app-store: eos-app-store.in Makefile
	$(AM_V_GEN) $(do_subst) $< > $@
	chmod +x $@

CLEANFILES += eos-app-store
EXTRA_DIST += eos-app-store.in
