from django.db import models
from thing import Thing
from uuid import uuid4


# ThingModel responds to a modeling philosophy that lies in
# between relation and non-relational modeling. Being a Django
# model, it can have relations with foreign keys and such when
# needed. It also has a `.data` attribute that on runtime is of
# type `Thing`, which means it hold any type of JSON-serializable
# data. Non-relational attributes are stored in this Thing instance,
# and never declared on the class definition.
#
# ThingModel's `getattr` and `setattr` have been redefined, to
# allow transparent interaction between relational (Django-powered)
# and non-relational (Thing-powered) fields. If you get or set a
# relational attribute, it will handled by Django. If you try to
# get or set a non-relational attribute (that might already exists, or not),
# it will be handled by the Thing, and added or retrieved correspondingly.
#
# Before saving, ThingModel takes its Thing instance, dumps it to JSON,
# and stores that JSON in the `json_data` attribute. At initialization,
# it does the opposite operation, effectively restoring all non-relational
# attributes. Upon saving, if it finds any `idx_<field_name>` attribute,
# it will be filled with the `<field_name>` attribute of its Thing.
# This allow to create indexes for non-relational attributes, to speed
# up retrieve queries using the Django ORM. Its your responsibility to
# declare this `idx_*` fields with the correct Django field type, and all
# necessary attributes (blank=True, null=True, max_length, etc.) such
# that whatever is found in the corresponding non-relational attribute
# can be stored in the `idx_*` attribute.
#
# Bon appetite!
#
class ThingModel(models.Model):
    class Meta:
        abstract = True

    uuid = models.CharField(max_length=50, primary_key=True)
    json_data = models.TextField(blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)

    def __init__(self, *args, **kwargs):
        self.__dict__['__initializing__'] = True

        super(ThingModel, self).__init__(*args, **kwargs)

        self.__dict__['data'] = Thing(self.json_data)
        self.__dict__['__initializing__'] = False

    def save(self, *args, **kwargs):
        if not self.uuid:
            self.uuid = str(uuid4())

        self.__dict__['json_data'] = self.data.json()

        for attr in dir(self):
            if attr.startswith('idx_'):
                self.__dict__[attr] = self.data.get(attr[4:])

        super(ThingModel, self).save(*args, **kwargs)

    def __getattr__(self, name):
        # Bypass all redirection when initializing
        if self.__dict__['__initializing__']:
            return super(models.Model, self).__getattribute__(name)

        return getattr(self.data, name)

    def __setattr__(self, name, value):
        # Bypass all redirection when initializing
        if self.__dict__['__initializing__']:
            super(models.Model, self).__setattr__(name, value)
            return

        # Handle special case for `data` field
        if name == 'data':
            self.__dict__['data'] = Thing(value)
            return

        # Handle special case for `json_data` field
        if name == 'json_data':
            self.__dict__['data'] = Thing(value)
            self.__dict__['json_data'] = value
            return

        # Handle private and protected fields with default behaviour
        if name.startswith('_'):
            super(models.Model, self).__setattr__(name, value)
            return

        try:
            # Let Django try to solve the attribute
            super(models.Model, self).__getattribute__(name)
            # If it exists, then we just set it as usual
            super(models.Model, self).__setattr__(name, value)
        except AttributeError:
            # If it didn't existed, then set it inside our thing
            try:
                setattr(self.data, name, value)
            except ValueError as e:
                raise ValueError("At attribute `%s`: %s" % (name, str(e)))
