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

See /lib/REAMDE.md for CTA library installation 

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
