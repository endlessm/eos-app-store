ACLOCAL_AMFLAGS = -I m4 ${ACLOCAL_FLAGS}

SUBDIRS = EosAppStore data po

# Preamble
bin_SCRIPTS =
libexec_SCRIPTS =
EXTRA_DIST =
CLEANFILES =
DISTCLEANFILES =

EXTRA_DIST += \
	autogen.sh \
	eos-reset-app-store \
	COPYING \
	NEWS

bin_SCRIPTS += \
	eos-app-store-launcher \
	eos-fill-desktop \
	eos-reset-app-store \
	eos-reset-desktop
libexec_SCRIPTS += eos-app-store

do_subst = $(SED) \
	-e 's|@pkglibdir[@]|$(pkglibdir)|g' \
	-e 's|@pkgdatadir[@]|$(pkgdatadir)|g' \
	-e 's|@GJS_CONSOLE[@]|$(GJS_CONSOLE)|g'

eos-app-store: eos-app-store.in Makefile
	$(AM_V_GEN) $(do_subst) $< > $@
	chmod +x $@

eos-fill-desktop: eos-fill-desktop.in Makefile
	$(AM_V_GEN) $(do_subst) $< > $@
	chmod +x $@

eos-app-store-launcher: eos-app-store-launcher.in Makefile
	$(AM_V_GEN) $(do_subst) $< > $@
	chmod +x $@

eos-reset-desktop: eos-reset-desktop.in Makefile
	$(AM_V_GEN) $(do_subst) $< > $@
	chmod +x $@

CLEANFILES += eos-app-store eos-app-store-launcher eos-fill-desktop eos-reset-desktop
EXTRA_DIST += eos-app-store.in eos-app-store-launcher.in eos-fill-desktop.in eos-reset-desktop.in
