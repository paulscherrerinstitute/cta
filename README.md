
# Complex Triggering Application (CTA)

This module provides an epics application and a gui which
can be used to define a sequence of events. This sequence
can be downloaded on an IOC and played out on a mrf
EVG HW.

# Tagging policy
This repository contains several components (e.g. EPICS db app, python cta_lib, python ui).
Each of these components evolve separately and are deployed separately but all components need to fit together to get a working CTA system.

To manage this we use a tagging scheme with the following tags:

  * CTA bundle tags: format = cta_bundle_major.minor.bugfix
  * CTA EPICS DB tags: format = major.minor.bugfix
  * CTA lib tags: format = cta_lib_major.minor.bufgix

The CTA bundle tags mark a state where all the components in the repro fit together.

The CTA EPICS DB tags mark a state of a releasable CTA EPICS database. The major.minor.bugfix tag name is used as EPICS version by the driver.makefile.

The CTA lib tags mark a state of a releasable CTA lib. The major.minor.bugfix part of the CTA lib tag is used as conda package version in lib/conda-recipe/meta.yaml.

# CTA Version 2 (Refactored Architecture)

### Architectural changes

CTA Version 2 replaces the legacy **QP/C (Quantum Platform in C)** architecture with a direct EPICS processing chain and a deterministic state machine implemented in an `aSub` record.

This change was made because the previous architecture was fundamentally incompatible with EPICS IOC design: QP/C assumes ownership of event scheduling, while EPICS already provides its own deterministic record-processing model. EPICS 3 appeared to tolerate this by chance due to permissive runtime behaviour, but the design was never correct and fails under EPICS 7.

---

### Pulse ID robustness improvement

The original CTA implementation did not account for jitter in the Pulse ID transmission.

The Pulse ID is sent by the timing master through the timing data buffer via a software-driven process. Because of this, occasional timing jitter can occur, causing CTA to read the same Pulse ID twice or miss an increment. This behaviour was confirmed experimentally by scientists.

To make CTA robust against this, Version 2 introduces a redesigned state machine.

---

### State machine

#### `IDLE`
In this state, CTA continuously checks Pulse ID sanity.

A Pulse ID is considered valid only if the new value equals the previous Pulse ID incremented by one.

If this condition is not met, CTA remains in `IDLE`.

---

#### `ARMED`
When Pulse ID sanity is confirmed, CTA automatically transitions to `ARMED`.

In this state, Pulse ID validation continues exactly as in `IDLE`.

This ensures CTA remains synchronized before sequence start.

---

#### `STARTED`
CTA enters `STARTED` when:

- the machine is in `ARMED`
- the user has pressed the start button

The start request is latched.

This means if the user presses start while CTA is not yet `ARMED`, the request is preserved, and the sequence will start automatically as soon as the next valid Pulse ID is detected.

This state determines the exact sequence start according to user configuration:

- **divisor**
- **offset**

(these features already existed in Version 1)

---

#### `RUNNING`
In this state, CTA advances the sequence index at every processing cycle.

When the end of the sequence is reached, CTA handles repetition according to user configuration:

- run forever
- run for a fixed number of cycles

---

#### `STOP`
This state resets:

- counters
- internal variables
- sequence state

CTA then returns to `IDLE`.

