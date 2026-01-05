#include "qpc.h"
#include "qf_port.h"
#include "qf.h"
#include <stdint.h>
#include <stdlib.h>
#include <stdbool.h>

#include "qep.h"
#include "qequeue.h"
#include "qmpool.h"

void QF_onStartup(void) {
}

void QF_onCleanup(void) {
}

/* NEW: required by many ports */
void QF_onClockTick(void) {
}

void Q_onAssert(char const *module, int loc) {
    (void)module; (void)loc;
    abort(); /* or epics exit path if you prefer */
}
