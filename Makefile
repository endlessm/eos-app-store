LIBDIR = $(DESTDIR)/lib/eos-app-store
BINDIR = $(DESTDIR)/bin
IMAGEDIR = $(DESTDIR)/share/EndlessOS/images
clean:
	rm -f *.py[co] */*.py[co]
install:
	mkdir -p $(LIBDIR)
	cp -R src/* $(LIBDIR)
	python -m compileall -d $(LIBDIR) $(LIBDIR)
	find $(LIBDIR) -name '*.py' -delete
	sed "s|%EOSAPPSTOREPATH%|$(LIBDIR)|g" eos_app_store.in > eos_app_store
	chmod +x eos_app_store
	mkdir -p $(BINDIR)
	cp eos_app_store $(BINDIR)
	mkdir -p $(IMAGEDIR)
	cp images/* $(IMAGEDIR)
uninstall:
	rm -f $(BINDIR)/eos_app_store
	rm -Rf $(LIBDIR)
	rm -Rf $(IMAGEDIR)

