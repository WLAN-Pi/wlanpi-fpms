.PHONY = all clean distclean install uninstall

prefix=/usr/local
bindir=$(prefix)/bin
datadir=$(prefix)/share
default_prefix=/usr/local

install_data_dir = $(DESTDIR)$(datadir)/fpms
install_bin_dir = $(DESTDIR)$(bindir)

SERVICE_SUBS = \
	s,[@]bindir[@],$(bindir),g; \
	s,[@]datadir[@],$(datadir),g

all:

fpms.service: fpms.service.in
	@echo "Set the prefix on fpms.service"
	sed -e '$(SERVICE_SUBS)' $< > $@

install: installdirs fpms.service
	cp -rf $(filter-out debian Makefile fpms.service.in $^,$(wildcard *)) $(install_data_dir)
	install -m 644 fpms.service $(DESTDIR)/lib/systemd/system

installdirs:
	mkdir -p $(install_bin_dir) \
		$(install_data_dir) \
		$(DESTDIR)/lib/systemd/system

clean:
	-rm -f fpms.service

distclean: clean

uninstall:
	-rm -rf $(install_data_dir) \
		$(DESTDIR)/lib/systemd/system

