.. _setup-label:

===============
Setup
===============


.. contents::
   :local:
   :depth: 3


Initial setup
=============

Follow certificate setup as per `Jeppe's tutorial <https://www.ippp.dur.ac.uk/~andersen/GridTutorial/certificates.html>`_

Make a careful note of passwords (can get confusing). Don't use passwords used
elsewhere in case you want to automate proxy renewal (like me and Juan)

NNLOJET Setup (for nnlojet developers only)
-------------------------------------------

As usual - pull the NNLOJET repository, update to modules and ``make -jXX``

.. note::
  LHAPDF 6.2.1 will not work on the grid outside of Durham(!)

- When installing lhapdf, don't have the default prefix ``$HOME`` for installation
  as the entire home directory will be tarred up when initialising the grid
  libraries for LHAPDF(!)

- For this you will also need to install and link against boost (painful I
  know...)

- As of 20/4/2018, the minimum known compatible version of gcc with NNLOJET is
  gcc 4.9.1. Versions above this are generally ok

Grid Script Setup
==================

To start using ``pyHepGrid`` you need to do the following steps.

0. Keep track of all your changes by committing them (e.g. fork the remote)

#. (optional) Create your own header (e.g. copy and edit the
   ``src/pyHepGrid/headers/template_header.py``) and add yourself to the
   ``header_mappings`` in ``src/pyHepGrid/src/header.py``. This is used for a
   python import so a header in ``some_folder/your_header.py`` would require
   ``your_name: some_folder.your_header``. If you do not add yourself the
   ``template_header.py`` will be used.

#. Generate a ``runcard.py`` similar to ``template_runcard.py`` inside the
   ``runcards`` folder. ``runcard.py`` is used to run ``pyHepGrid`` *not your
   program*. The only required setting in there is ``dictCard``, but you can
   also overwrite any setting from your header, e.g. ``BaseSeed`` or
   ``producRun``.

#. Create folders on ``gfal`` to save your in and output. They have to match
   ``grid_input_dir``, ``grid_output_dir`` and ``grid_warmup_dir`` of your
   header

#. If you use you own program: Write you own ``runfile`` similar to `
   `example/simplerun.py``. This script will be ran on each node, so it should
   be *self-contained* and *Python 2.7 compatible*. It should also be able to
   handle all arguments of the ``nnnnlorun.py``, even if they are not used in
   the script itself. An argument parser and other common functions are shipped
   with ``pyHepGrid`` in `grid_functions.py
   <https://github.com/scarlehoff/pyHepGrid/blob/master/src/pyHepGrid/extras/grid_functions.py>`_,
   ``grid_functions.py`` will automatically be copied to each grid node and can
   be used on there. To run on Dirac make sure you do not depend on a specific
   local setup, i.e. download all required programs from ``gfal`` or use what is
   available on the ``/cvmfs/``. Wrapper around ``gfal`` are provided in
   ``grid_functions.py``, e.g. in your ``runfile`` you can download
   ``grid_file`` with

   .. code-block:: python

      import grid_functions as gf
      gf.copy_from_grid(grid_file, local_file, args)


#. To install and run the scripts, run

   .. code-block:: bash

      python3 setup.py install --user
      python3 setup.py develop --user

   (Include the ``--prefix`` option and add to a location contained in
   ``$PYTHONPATH`` if you want to install it elsewhere). ``--user`` is used on
   the gridui as we don't have access to the python3 installation - if you have
   your own install, feel free to drop it.

   .. note::
       We currently need to be in develop mode given the way that the header
       system works - the plan is for this to change at some point.

   Alternatively: if you wish to run pyHepGrid from within a Conda environment,
   install the scripts by moving to the directory containing setup.py and
   running:

   .. code-block:: bash

      conda install conda-build
      conda develop .

   If prompted to install any dependencies required by conda-build in step 1.,
   type ``Y`` to proceed.

After this you should be able to run ``pyHepGrid test runcards/your_runcard.py
-B``. This will execute the your ``runfile`` locally inside the ``test_sandbox``
folder. You might want to try running it with a *clean* environment, e.g.
without sourcing your ``~/.bashrc``. If this works fine you can try submitting to
the arc  test queue with ``pyHepGrid run runcards/your_runcard.py -B --test``. The
test queue highly limited in resources. **Only submit a few short jobs to it**
(<10).

Further customisations (advanced usage)
---------------------------------------

Beside the header and runcard setup, ``pyHepGrid`` has two big *attack points*
for customisations. First and foremost the ``runfile`` which is run on each grid
node. This is similar to other grid-scripts that you might have used before.
Additionally you can change some local background behaviour through the
``runmode``. A ``runmode`` is *program* specific, e.g. there is a ``runmode``
``"NNLOJET"`` and ``"HEJ"``. The behaviour of ``pyHepGrid ini`` is completely
controlled by the ``runmode``. You could set it up to upload some common files
(runcards, warmup-files, executable, etc.) with ``gfal`` before submitting jobs.
An simple example for a completely customised ``runfile`` and ``runmode`` is
provided in the ``example/`` folder.

If you want to implement your own ``runmode`` write a *program* class as a
subclass of the `ProgramInterface <https://github.com/scarlehoff/pyHepGrid/blob/master/src/pyHepGrid/src/program_interface.py>`_.
You can then load your program as a ``runmode`` in your ``runcard.py``, e.g. you
could specify ``runmode="pyHepGrid.src.programs.HEJ"`` to explicitly load HEJ (the
shorter ``runmode=HEJ`` is just an alias). As always, to get started it is easiest
to look at existing runmodes or programs, i.e. the
`backend_example.py <https://github.com/scarlehoff/pyHepGrid/blob/master/example/backend_example.py>`_ or any default in
`programs.py <https://github.com/scarlehoff/pyHepGrid/blob/master/src/pyHepGrid/src/programs.py>`_. Dependent on your setup you
might not need to implement all functions. For example to use the initialisation
in production mode you only need to implement the ``init_production`` function.

You can also use your custom program class to pass non-standard arguments to
your ``runfile`` by overwriting the ``include_arguments``,
``include_production_arguments`` or ``include_warmup_arguments`` functions. You can
add, change or even delete entries as you want (the latter is not advised). The
output of ``include_agruments`` is directly passed to your ``runfile`` as a
command-line argument of the form ``--key value`` for Arc and Dirac, or replaces
the corresponding arguments in the ``slurm_template``.

.. note::
    ``pyHepGrid`` will and can not sanitise your setup and it is your
    responsibility to ensure your code runs as intended. As a general advice try
    to reuse code shipped with ``pyHepGrid`` where possible, in particular from
    ``grid_functions.py``, since this should be tested to some expend.

Arc Proxy setup
===============

By default, jobs will fail if the arc proxy ends before they finish running, so
it's a good idea to keep them synced with new proxies as you need:

.. code-block:: bash

    # Create new proxy
    arcproxy -S pheno -N -c validityPeriod=24h -c vomsACvalidityPeriod=24h

    # Sync current jobs with latest proxy
    arcsync -c ce1.dur.scotgrid.ac.uk
    arcrenew -a

There is also a method to create a long proxy for one week describes in
`Jeppe's grid tutorial <https://www.ippp.dur.ac.uk/~andersen/GridTutorial/certificates.html>`_.

Automated (set & forget)
------------------------

In `proxy_renewal/ <https://github.com/scarlehoff/pyHepGrid/blob/master/proxy_renewal/>`_ are some simple scripts to
automatically update your proxy. To get these working, create a file

.. code-block:: bash

    nano ~/.password/arcpw
    chmod 400 ~/.password/arcpw

and enter your password. Make sure you that your ``~/.password/arcpw`` is hidden,
i.e. ``ls -l ~/.password/arcpw`` should show ``-rw-------`` otherwise other users
could read your password. Afterwards add

.. code-block:: bash

    export CERT_PW_LOCATION=~/.password/arcpw
    export PATH=/path/to/pyHepGrid/proxy_renewal:${PATH}

to your ``~/.bashrc`` and source it. Afterwards you should be able to run
``newproxy`` to get a new 24 hour proxy without typing your password, you can
check the proxy time with ``arcproxy -I``.

``syncjobs`` will update the certificate on all your queuing and running jobs.
Set it to run as a `cron job <https://crontab.guru/>`_ at least twice per day,
such that no jobs will ever be stopped do to an invalid certificate.


DIRAC
=====

Installing Dirac is quite easy nowadays! This information comes directly from
https://www.gridpp.ac.uk/wiki/Quick_Guide_to_Dirac. Running all commands will
install dirac version ``$DIRAC_VERSION`` to ``$HOME/dirac_ui``. You can change this
by modifying the variable ``DIRAC_FOLDER``

.. code-block:: bash

    DIRAC_FOLDER="~/dirac_ui"
    DIRAC_VERSION="-r v6r22p6 -i 27 -g v14r1" # replace with newest version

    mkdir $DIRAC_FOLDER
    cd $DIRAC_FOLDER
    wget -np -O dirac-install https://raw.githubusercontent.com/DIRACGrid/DIRAC/integration/Core/scripts/dirac-install.py
    chmod u+x dirac-install
    ./dirac-install $DIRAC_VERSION
    source $DIRAC_FOLDER/bashrc # this is not your .bashrc but Dirac's bashrc, see note below
    dirac-proxy-init -x  # Here you will need to give your grid certificate password
    dirac-configure -F -S GridPP -C dips://dirac01.grid.hep.ph.ic.ac.uk:9135/Configuration/Server -I
    dirac-proxy-init -g pheno_user -M

.. note::
    Remember you might need to source ``$DIRAC_FOLDER/bashrc`` every time you want to use dirac.
