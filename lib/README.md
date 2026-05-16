# CTA Python Library (`cta_lib`)

## Overview

`cta_lib` provides a Python interface to interact with the CTA EPICS7 IOC.

It can be used to:

- upload and download CTA sequences
- configure repetition behaviour
- start and stop execution
- receive callbacks on state changes

## Prerequisites

The following must be available:

- Python 3
- EPICS7 runtime environment

Required Python dependencies:

- `pyepics`
- `numpy`

## Installation

### Option 1: Install into an existing Python environment (deployment)

Activate the target Python environment and install from source:

```bash
python -m pip install .
```

This installs `cta_lib` together with its required Python dependencies.

### Option 2: Build and install as a Conda package

Build the package:

```bash
cd conda-recipe
conda build .
```

Install it into the target environment:

```bash
conda install --use-local cta_lib
```

This option is recommended for controlled Conda-based deployments.

## Example Usage

The package provides example command-line tools for interacting with CTA.
