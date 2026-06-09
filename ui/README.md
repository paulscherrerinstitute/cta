# CTA Graphical User Interface

## Overview

The CTA graphical user interface is available to configure and control a CTA EPICS7 IOC.

## Prerequisites

The following must be available:

- Python 3
- EPICS7 runtime environment
- `cta_lib` installed in the active Python environment
- `PyQt5`

## Installation

See ../lib/README.md for CTA library installation 

## Deployment 

The CTA GUI requires:

 - cta_lib installed in the target Python environment 
 - PyQt5 installed in the same environment 

The following files must be deployed together:

 - cta_gui.py
 - start_cta_gui.sh 

### TODO 

 - In long term, create a conda package for cta_gui, that requires cta_lib to deploy everything at once. 
 - Update cta performances ui.

## Usage

Launch the GUI:

```bash
./start_cta_gui.sh ESX DEVICE
```

Example:

```bash
./start_cta_gui.sh SFTEST SFTEST-CCTA-TI2
```

Show help:

```bash
./start_cta_gui.sh --help
```

## Development Mode

For local development, the GUI can use the local `cta_lib` source tree instead of the installed package:

```bash
./start_cta_gui.sh --dev ESX DEVICE
```

Example:

```bash
./start_cta_gui.sh --dev SFTEST SFTEST-CCTA-TI2
```
