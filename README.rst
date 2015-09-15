YALP Grok
=========

Forked from https://github.com/garyelephant/pygrok as it seems to be dead. If
pygrok becomes active again this fork may be closed.

Python implementaion of Jordan Sissel's `Grok`.

Install
-------

.. code-block:: bash

    pip install yalp_grok

Basic Usage
-----------

.. code-block:: python

    >>> import yalp_grok as pygrok
    >>> text = 'gary is male, 25 years old and weighs 68.5 kilograms'
    >>> pattern = '%{WORD:name} is %{WORD:gender}, %{NUMBER:age} years old and
    weighs %{NUMBER:weight} kilograms'
    >>> print pygrok.grok_match(text, pattern)
    {'gender': 'male', 'age': '25', 'name': 'gary', 'weight': '68.5'}

Reusing Patterns
----------------

Since compiling a pattern can be time consuming, patterns can be compiled once
and then reused for searching.

.. code-block:: python

    >>> import yalp_grok as pygrok
    >>> pattern = "%{COMMONAPACHELOG}"
    >>> compiled_pattern = pygrok.compile_pattern(pattern)
    >>> with open('/var/log/apache/access.log', 'r') as log_file
    ...     matches = [pygrok.grok_search(line, compiled_pattern) for line in log_file]

.. _Grok: https://github.com/jordansissel/grok
