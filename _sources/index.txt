===============
khufu_traversal
===============

Overview
========

*khufu_traversal* is a method for mapping SQLAlchemy-based models for traversal
in :term:`Pyramid`.

Requirements
============

  * Python >= 2.5 (not tested with Python 3.x series)

Setup
=====

Simply include the ``khufu_traversal`` package with the configurator, ie:

.. code-block:: python
 :linenos:

 config.include('khufu_traversal')

Usage
=====

The standard way to setup traversal containers is as follows:

.. code-block:: python
 :linenos:

 # config is an instance of Configurator
 # Group and User are SQLAlchemy-based model classes

 config.include('khufu_traversal')
 GroupContainer = config.setup_model_container(Group, [('users', User)])
 UserContainer = config.setup_model_container(User, [('groups', Group)])

For a more complete example please see the ``khufu_traversal.demo`` python module.

Credits
=======

  * Developed and maintained by Rocky Burt <rocky AT serverzen DOT com>

More Information
================

.. toctree::
 :maxdepth: 1

 api.rst
 glossary.rst

Indices and tables
==================

* :ref:`glossary`
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
