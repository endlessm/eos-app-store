LIBDIR = $(DESTDIR)/lib/eos-app-store
BINDIR = $(DESTDIR)/bin
clean:
	rm -f *.py[co] */*.py[co]
install:
	mkdir -p $(LIBDIR)
	cp -R src/* $(LIBDIR)
	python -m compileall -d $(LIBDIR) $(LIBDIR)
	find $(LIBDIR) -name '*.py' -delete
	sed -i "s|EOSAPPSTOREPATH|$(LIBDIR)|g" eos_app_store
	cp eos_app_store $(BINDIR)
uninstall:
	rm -f $(BINDIR)/eos_app_store
	rm -Rf $(LIBDIR)
