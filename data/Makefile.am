
EXTRA_DIST =
CLEANFILES =

resource_files = $(shell $(GLIB_COMPILE_RESOURCES) --sourcedir=$(srcdir) --generate-dependencies $(srcdir)/eos-app-store.gresource.xml)
eos-app-store.gresource: eos-app-store.gresource.xml $(resource_files)
	$(AM_V_GEN) $(GLIB_COMPILE_RESOURCES) --target=$@ --sourcedir=$(srcdir) $<

resourcedir = $(pkgdatadir)
resource_DATA = eos-app-store.gresource

# Can't be part of GResource, or symbolic won't work
iconsdir = $(pkgdatadir)/icons
icons_DATA = \
	icon_apps-symbolic.svg \
	icon_folder-symbolic.svg \
	icon_website-symbolic.svg \
	$(NULL)

EXTRA_DIST += $(icons_DATA)

EXTRA_DIST += \
	eos-app-store.gresource.xml \
	$(resource_files) \
	$(NULL)

CLEANFILES += \
	eos-app-store.gresource \
	$(NULL)

servicedir = $(datadir)/dbus-1/services
service_DATA = com.endlessm.AppStore.service

com.endlessm.AppStore.service: Makefile
	$(AM_V_GEN) \
	( echo "[D-BUS Service]" ; \
	  echo "Name=com.endlessm.AppStore" ; \
	  echo "Exec=${libexecdir}/eos-app-store" ) > $@.tmp && \
	mv $@.tmp $@

CLEANFILES += $(service_DATA)
