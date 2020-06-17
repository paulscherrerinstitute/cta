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