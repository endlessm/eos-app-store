AM_CPPFLAGS = \
	-I$(top_builddir) \
	-I$(top_srcdir) \
	-L$(top_srcdir)/EosAppStore \
	-DEOS_APP_STORE_LIBDIR=\"$(libdir)\" \
	-DEOS_APP_STORE_DATADIR=\"$(datadir)\" \
	-DEOS_APP_STORE_PKGDATADIR=\"$(pkgdatadir)\" \
	-DEOS_APP_STORE_TOP_SRCDIR=\"$(abs_top_srcdir)\" \
	-DEOS_APP_STORE_BUILDDIR=\"$(abs_top_builddir)\"

BUILT_SOURCES =
EXTRA_DIST =
CLEANFILES =
pkglib_LTLIBRARIES =
INTROSPECTION_GIRS =
gir_DATA =
typelib_DATA =
libexec_PROGRAMS =
libexec_SCRIPTS =
js_built_sources =
girdir = $(pkgdatadir)/gir-1.0
typelibdir = $(pkglibdir)/girepository-1.0

include $(INTROSPECTION_MAKEFILE)
include Makefile-lib.am
include Makefile-js.am

gir_DATA += $(INTROSPECTION_GIRS)
typelib_DATA += $(gir_DATA:.gir=.typelib)

CLEANFILES += $(gir_DATA) $(typelib_DATA)
