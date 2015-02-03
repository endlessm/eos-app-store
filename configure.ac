dnl -*- Mode: autoconf -*-
dnl Process this file with autoconf to produce a configure script.
AC_PREREQ(2.53)
AC_INIT([eos-app-store], [1.0.99], [http://www.endlessm.com])
m4_ifdef([AM_SILENT_RULES],[AM_SILENT_RULES([yes])])
AC_CONFIG_SRCDIR([EosAppStore/main.js])
AC_CONFIG_HEADERS([EosAppStore/config.h])
AC_CONFIG_MACRO_DIR([m4])
AM_INIT_AUTOMAKE([1.9 no-dist-gzip dist-xz tar-ustar foreign])

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
AC_DEFINE_UNQUOTED(GETTEXT_PACKAGE,"$GETTEXT_PACKAGE",[The name of the gettext domain])
IT_PROG_INTLTOOL(0.40.0)

AC_DEFINE_UNQUOTED(CONTENT_GETTEXT_PACKAGE,"eos-shell-content",[The name of the gettext domain to use for content])

AC_CACHE_SAVE

GOBJECT_INTROSPECTION_REQUIRE([0.9.6])

PKG_CHECK_MODULES(EOS_APP_STORE,
                  gjs-1.0
                  gio-2.0
                  gtk+-3.0 >= 3.10.0
                  json-glib-1.0
                  libsoup-2.4 >= 2.44.0
                  webkit2gtk-3.0
                  libsystemd-journal
                  endless-0)
AC_SUBST(EOS_APP_STORE_CFLAGS)
AC_SUBST(EOS_APP_STORE_LIBS)

GJS_CONSOLE=`$PKG_CONFIG --variable=gjs_console gjs-1.0`
AC_SUBST(GJS_CONSOLE)

GLIB_COMPILE_RESOURCES=`$PKG_CONFIG --variable glib_compile_resources gio-2.0`
AC_SUBST(GLIB_COMPILE_RESOURCES)

GDBUS_CODEGEN=`$PKG_CONFIG --variable gdbus_codegen gio-2.0`
AC_SUBST(GDBUS_CODEGEN)

AC_CACHE_SAVE

AC_PROG_CC_C99

AC_ARG_ENABLE([maintainer-cflags],
              [AS_HELP_STRING([--enable-maintainer-cflags],
                              [Enable more compiler warnings])],
              [],
              [enable_maintainer_cflags=yes])
AS_IF([test "x$enable_maintainer_cflags" = "xyes"],
      [
        MAINTAINER_CFLAGS="$MAINTAINER_CFLAGS -Wall"
        MAINTAINER_CFLAGS="$MAINTAINER_CFLAGS -Wcast-align"
        MAINTAINER_CFLAGS="$MAINTAINER_CFLAGS -Wuninitialized"
        MAINTAINER_CFLAGS="$MAINTAINER_CFLAGS -Wno-strict-aliasing"
        MAINTAINER_CFLAGS="$MAINTAINER_CFLAGS -Werror=pointer-arith"
        MAINTAINER_CFLAGS="$MAINTAINER_CFLAGS -Werror=missing-declarations"
        MAINTAINER_CFLAGS="$MAINTAINER_CFLAGS -Werror=redundant-decls"
        MAINTAINER_CFLAGS="$MAINTAINER_CFLAGS -Werror=empty-body"
        MAINTAINER_CFLAGS="$MAINTAINER_CFLAGS -Werror=format -Werror=format-security -Werror=format-nonliteral"
        MAINTAINER_CFLAGS="$MAINTAINER_CFLAGS -Werror=init-self"
      ])
AC_SUBST(MAINTAINER_CFLAGS)

AC_CONFIG_FILES([
        Makefile
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
