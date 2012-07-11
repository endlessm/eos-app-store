
PYINSTALLER_VERSION=1.5.1
PYINSTALLER_PATH=$(HOME)/apps/pyinstaller-$(PYINSTALLER_VERSION)
SPECFILE=endless_os_desktop_widget.spec

all: clean
	python $(PYINSTALLER_PATH)/Build.py $(SPECFILE)

clean:
	rm -fR build dist

install:
	mkdir -p $(DESTDIR)/usr/share/locale/pt_BR/LC_MESSAGES/
	msgfmt -v po/pt_BR.po -o $(DESTDIR)/usr/share/locale/pt_BR/LC_MESSAGES/endless_desktop.mo
	mkdir -p $(DESTDIR)/usr/bin/
	mkdir -p $(DESTDIR)/usr/share/endlessm/images
	install --mode=755 dist/* $(DESTDIR)/usr/bin/
	install --mode=644 images/*.png $(DESTDIR)/usr/share/endlessm/images
