include /ioc/tools/driver.makefile

BUILDCLASSES = Linux

MODULE = cta

EXCLUDE_VERSIONS = 3.13 3.14.8

ARCH_FILTER = SL6-x86_64 eldk52-e500v2

USR_CFLAGS += -DQP_IMPL

SOURCES += seqCtrl/devSeqCtrl.c
SOURCES += seqCtrl/seqCtrl.c
SOURCES += seqCtrl/qep_hsm.c
SOURCES += seqCtrl/qf_act.c
SOURCES += seqCtrl/qf_actq.c
SOURCES += seqCtrl/qf_hooks.c
SOURCES += seqCtrl/qf_qact.c
SOURCES += seqCtrl/qf_dyn.c
SOURCES += seqCtrl/qf_mem.c
SOURCES += seqCtrl/qf_port.c
SOURCES += seqCtrl/qf_time.c
SOURCES += seqCtrl/qf_ps.c
SOURCES += seqCtrl/qf_qeq.c

DBDS += seqCtrl/seqCtrl.dbd

TEMPLATES += cta/cta.template
TEMPLATES += cta/cta.db
TEMPLATES += cta/performance.db
TEMPLATES += seqCtrl/seqCtrl.db
TEMPLATES += series/series.db
TEMPLATES += superposition/superposition.db

ifeq (spy, $(CONF))
	CFLAGS += -DQ_SPY
  qpc_VERSION = spy
endif

install_ui:
	scripts/install_ui.sh ui
