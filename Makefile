LIBDIR = $(DESTDIR)/usr/lib/eos-app-store
clean:
	rm -f *.py[co] */*.py[co]
install:
	mkdir -p $(LIBDIR)
	cp -R src/* $(LIBDIR)
	python -m compileall -d /usr/lib/eos-app-store $(LIBDIR)
	find $(LIBDIR) -name '*.py' -delete
uninstall:
	rm -Rf /usr/lib/eos-app-store
	rm -Rf $(LIBDIR)
