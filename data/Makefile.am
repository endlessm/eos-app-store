
EXTRA_DIST =
CLEANFILES =

resource_files = $(shell $(GLIB_COMPILE_RESOURCES) --sourcedir=$(srcdir) --generate-dependencies $(srcdir)/eos-app-store.gresource.xml)
eos-app-store.gresource: eos-app-store.gresource.xml $(resource_files)
	$(AM_V_GEN) $(GLIB_COMPILE_RESOURCES) --target=$@ --sourcedir=$(srcdir) $<

resourcedir = $(pkgdatadir)
resource_DATA = eos-app-store.gresource

EXTRA_DIST += \
	eos-app-store.gresource.xml \
	$(resource_files) \
	$(NULL)

CLEANFILES += \
	eos-app-store.gresource \
	$(NULL)

servicedir = $(datadir)/dbus-1/services
service_DATA = com.endlessm.AppStore.service

tmpfilesdir = $(prefix)/lib/tmpfiles.d
dist_tmpfiles_DATA = eos-app-store.conf

com.endlessm.AppStore.service: Makefile
	$(AM_V_GEN) \
	( echo "[D-BUS Service]" ; \
	  echo "Name=com.endlessm.AppStore" ; \
	  echo "Exec=${libexecdir}/eos-app-store" ) > $@.tmp && \
	mv $@.tmp $@

CLEANFILES += $(service_DATA)
