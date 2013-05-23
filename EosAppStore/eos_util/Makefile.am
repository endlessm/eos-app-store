appdir = $(pythondir)/EosAppStore/eos_util
app_PYTHON = \
	__init__.py \
	image.py \
	image_util.py \
	locale_util.py \
	path_util.py \
	screen_util.py \
	$(NULL)

do_subst = sed -e 's|@datadir[@]|$(datadir)|g' \
               -e 's|@pkgdatadir[@]|$(pkgdatadir)|g'

path_util.py: Makefile path_util.py.in
	$(AM_V_GEN) $(do_subst) path_util.py.in > $@
