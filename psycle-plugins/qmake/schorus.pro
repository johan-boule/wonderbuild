TARGET = psycle-plugin-SChorus

include(psycle-plugins.pri)

SOURCES_PRESERVE_PATH += \
	$$findFiles($$PSYCLE_PLUGINS_DIR/src/psycle/plugins, SChorus.cpp)
HEADERS += \
	$$findFiles($$PSYCLE_PLUGINS_DIR/src/psycle/plugins, *.hpp) \
	$$findFiles($$PSYCLE_PLUGINS_DIR/src/psycle/plugins, *.h)