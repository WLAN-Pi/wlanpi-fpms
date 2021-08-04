.PHONY = all clean distclean install uninstall

prefix=/usr/local
bindir=$(prefix)/bin
datadir=$(prefix)/share
default_prefix=/usr/local

install_data_dir = $(DESTDIR)$(datadir)/fpms
install_bin_dir = $(DESTDIR)$(bindir)

networkinfo_rel_dir = share/fpms/BakeBit/Software/Python/scripts/networkinfo

SERVICE_SUBS = \
	s,[@]bindir[@],$(bindir),g; \
	s,[@]datadir[@],$(datadir),g; \
	s,[@]networkinfo[@],$(prefix)/$(networkinfo_rel_dir),g

all:

fpms.service: fpms.service.in
	@echo "Set the prefix on fpms.service"
	sed -e '$(SERVICE_SUBS)' $< > $@

networkinfo.service: networkinfo.service.in
	@echo "Set the prefix on networkinfo.service"
	sed -e '$(SERVICE_SUBS)' $< > $@

install: installdirs $(binary_name) fpms.service networkinfo-links networkinfo.service
	cp -rf $(filter-out debian fpms.service.in networkinfo.service.in $^,$(wildcard *)) $(install_data_dir)
	install -m 644 fpms.service $(DESTDIR)/lib/systemd/system
	install -m 644 networkinfo.service $(DESTDIR)/lib/systemd/system

installdirs:
	mkdir -p $(install_bin_dir) \
		$(install_data_dir) \
		$(DESTDIR)/lib/systemd/system

networkinfo-links:
	ln -fs ../$(networkinfo_rel_dir)/reachability.sh $(install_bin_dir)/reachability
	ln -fs ../$(networkinfo_rel_dir)/publicip.sh $(install_bin_dir)/publicip
	ln -fs ../$(networkinfo_rel_dir)/watchinternet.sh $(install_bin_dir)/watchinternet
	ln -fs ../$(networkinfo_rel_dir)/telegrambot.sh $(install_bin_dir)/telegrambot
	ln -fs ../$(networkinfo_rel_dir)/ipconfig.sh $(install_bin_dir)/ipconfig
	ln -fs ../$(networkinfo_rel_dir)/portblinker.sh $(install_bin_dir)/portblinker

clean:
	-rm -f fpms.service
	-rm -f networkinfo.service

distclean: clean

uninstall:
	-rm -rf $(install_data_dir) \
		$(DESTDIR)/lib/systemd/system \
		$(bindir)/reachability \
		$(bindir)/publicip \
		$(bindir)/watchinternet \
		$(bindir)/telegrambot \
		$(bindir)/ipconfig \
		$(bindir)/portblinker

