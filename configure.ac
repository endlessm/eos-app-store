dnl -*- Mode: autoconf -*-
dnl Process this file with autoconf to produce a configure script.
AC_PREREQ(2.53)
AC_INIT([eos-app-store], [1.0.99], [http://www.endlessm.com])
m4_ifdef([AM_SILENT_RULES],[AM_SILENT_RULES([yes])])
AC_CONFIG_SRCDIR(eos-app-store.in)
AC_CONFIG_HEADERS([config.h])
AM_INIT_AUTOMAKE([1.9 no-dist-gzip dist-xz foreign])

AM_PATH_PYTHON_VERSION(2.7, 2.7.0, 2.6, 2.6.0, 2.5, 2.5.0, 2.4, 2.4.0)

# Initialize libtool
LT_PREREQ([2.2.6])
LT_INIT([disable-static])

# i18n
IT_PROG_INTLTOOL([0.40])

AM_GNU_GETTEXT([external])
AM_GNU_GETTEXT_VERSION([0.17])

GETTEXT_PACKAGE=eos-app-store
AC_SUBST(GETTEXT_PACKAGE)
AC_DEFINE_UNQUOTED(GETTEXT_PACKAGE, "$GETTEXT_PACKAGE",
                   [The prefix for our gettext translation domains.])

PKG_CHECK_MODULES(EOS_APP_STORE,
                  gio-2.0
                  gtk+-3.0)

AC_CONFIG_FILES([
        Makefile
        data/Makefile
        images/Makefile
        EosAppStore/Makefile
        EosAppStore/add_shortcuts_module/Makefile
        EosAppStore/application_store/Makefile
        EosAppStore/desktop/Makefile
        EosAppStore/desktop_files/Makefile
        EosAppStore/eos_log/Makefile
        EosAppStore/eos_util/Makefile
        EosAppStore/eos_widgets/Makefile
        EosAppStore/folder/Makefile
        EosAppStore/osapps/Makefile
        EosAppStore/removal_module/Makefile
        EosAppStore/shortcut/Makefile
        EosAppStore/util/Makefile
        po/Makefile.in
        ])

AC_OUTPUT
echo "
        eos-app-store $VERSION
        ===================

        prefix: ${prefix}

        Now type 'make' to build $PACKAGE
"
