Welcome to Askhome!
===================

**Askhome** wraps the `Smart Home Skill API`_ for Amazon Echo and removes all that ugly boilerplate.

Basic skill in askhome looks like this::

    from askhome import Smarthome, Appliance

    class Star(Appliance):
        @Appliance.action
        def turn_on(self, request):
            ... # Let there be light

    home = Smarthome()
    home.add_appliance('star1', Star, name='Sun')

    handler = home.lambda_handler

Features
--------

* Define what your smart devices can do with simple class interface
* Askhome then handles device discovery and routes Alexa requests to your methods
* Requests come in a nice preprocessed object and provide easy to use response methods
* If something goes wrong, just raise the appropriate exception
* You don't have to touch the raw JSON requests at all!

Why a Smart Home Skill
----------------------

Alexa `Custom Skills`_ are indeed much more flexible, but creating their intent schema can be a hassle.
If you want to simply control your devices, Smart Home Skills provide a robust voice interfaces
and all you have to do is plug in your control logic --- well, that is with **askhome**.

User Guide
----------

.. toctree::
    :maxdepth: 3

    quickstart
    advanced

API Documentation
-----------------

If you are looking for information on a specific function, class or method, this part of the
documentation is for you.

.. toctree::
    :maxdepth: 3

    api


.. links
.. _Smart Home Skill API: https://developer.amazon.com/public/solutions/alexa/alexa-skills-kit/docs/smart-home-skill-api-reference
.. _Custom Skills: https://developer.amazon.com/public/solutions/alexa/alexa-skills-kit/overviews/understanding-custom-skills