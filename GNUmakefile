include /ioc/tools/driver.makefile

MODULE = cta
BUILDCLASSES = Linux
ARCH_FILTER = SL6-x86_64 eldk52-e500v2

# TEMPLATES
TEMPLATES += cta/cta.template
TEMPLATES += cta/cta.db
TEMPLATES += cta/performance.db
TEMPLATES += cta/seqCtrl.db
TEMPLATES += series/series.db
TEMPLATES += superposition/superposition.db

SOURCES += src/cta.c

install_ui:
	scripts/install_ui.sh ui
