dnl -*- Mode: autoconf -*-
dnl Process this file with autoconf to produce a configure script.
AC_PREREQ(2.53)
AC_INIT([eos-app-store], [1.0.99], [http://www.endlessm.com])
m4_ifdef([AM_SILENT_RULES],[AM_SILENT_RULES([yes])])
AC_CONFIG_SRCDIR([EosAppStore/main.js])
AC_CONFIG_HEADERS([EosAppStore/config.h])
AC_CONFIG_MACRO_DIR([m4])
AM_INIT_AUTOMAKE([1.9 no-dist-gzip dist-xz foreign])

AC_PROG_SED

AC_PROG_CC
AM_PROG_CC_C_O
AC_PROG_CXX
AC_ISC_POSIX
AC_HEADER_STDC

LT_INIT([disable-static])

PKG_PROG_PKG_CONFIG([0.22])

AC_CACHE_SAVE

GETTEXT_PACKAGE=AC_PACKAGE_NAME
AC_SUBST(GETTEXT_PACKAGE)
AC_DEFINE_UNQUOTED(GETTEXT_DOMAIN,"$GETTEXT_PACKAGE",[The name of the gettext domain])
IT_PROG_INTLTOOL(0.40.0)

AC_CACHE_SAVE

GOBJECT_INTROSPECTION_REQUIRE([0.9.6])

PKG_CHECK_MODULES(EOS_APP_STORE,
                  gjs-1.0
                  gio-2.0
                  gtk+-3.0
                  json-glib-1.0
                  libgnome-menu-3.0
                  pstack)
AC_SUBST(EOS_APP_STORE_CFLAGS)
AC_SUBST(EOS_APP_STORE_LIBS)

GJS_CONSOLE=`$PKG_CONFIG --variable=gjs_console gjs-1.0`
AC_SUBST(GJS_CONSOLE)

GLIB_COMPILE_RESOURCES=`$PKG_CONFIG --variable glib_compile_resources gio-2.0`
AC_SUBST(GLIB_COMPILE_RESOURCES)

AC_CACHE_SAVE

AM_GNU_GETTEXT([external])
AM_GNU_GETTEXT_VERSION([0.17])

AC_CACHE_SAVE

AC_CONFIG_FILES([
        Makefile
        content/Makefile
        data/Makefile
        EosAppStore/Makefile
        po/Makefile.in
        ])

AC_OUTPUT
echo "
        eos-app-store $VERSION
        ===================

        prefix: ${prefix}

        Now type 'make' to build $PACKAGE
"
