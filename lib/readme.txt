How to list local conda environments?
-------------------------------------
[]$ source /opt/gfa/python 3.6
[]$ conda env list

How to activate a conda environment?
------------------------------------
[]$ source activate my_env

How to list all packages (with version) installed in the active environment
---------------------------------------------------------------------------
[]$ conda list

How to create an environment to build and run cta_lib
-----------------------------------------------------
[]$ source /opt/gfa/python 3.6
[]$ conda create -c paulscherrerinstitute --name my_env python=3.6 numpy pyepics

How to build conda package cta_lib and install it in a coda environment
-----------------------------------------------------------------------
[]$ cd <cta_root_dir>/lib
[]$ source /opt/gfa/python 3.6
[]$ source activate my_env
[]$ conda build conda-recipe
[]$ conda install --use-local cta_lib # use cta_lib=1.0.4 if a specific version is required

How to delete a local environment and everything in it
------------------------------------------------------
[]$ conda env remove --name cta_lib

How to uninstall cta_lib package from the active conda environment
------------------------------------------------------------------
[]$ conda remove cta_lib

How to uninstall cta_lib package from my_env conda environment
---------------------------------------------------------------
[]$ conda remove --name my_env cta_lib
