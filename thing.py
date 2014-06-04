import json


class Thing(object):
    def __init__(self, data=None, **kwargs):
        if data is not None and isinstance(data, (str, unicode)):
            _data = json.loads(data)
        elif data is not None and isinstance(data, dict):
            _data = data
        elif data is not None:
            raise ValueError('`data` must be either `dict` or a json `str`, '
                             'not `%s`' % type(data).__name__)
        else:
            _data = {}

        # Should we allow non-json (arbitrary) attribute values
        self.__dict__['allow_non_json'] = kwargs.pop('allow_non_json', False)

        _data.update(kwargs)

        self.__dict__['__valid_types__'] = \
            (int, long, bool, float, str, unicode)

        self.__set_data(_data)

    def json(self):
        return json.dumps(self.dict())

    def dict(self):
        return self.__get_data()

    def __setitem__(self, k, v):
        if not isinstance(k, (str, unicode)):
            raise KeyError('Keys must be `str` or `unicode`')

        self.__data__[k] = self.__wrap(v)

    def __getitem__(self, k):
        if not isinstance(k, (str, unicode)):
            raise KeyError('Keys must be `str` or `unicode`')

        return self.__data__[k]

    def get(self, k, default=None):
        if not isinstance(k, (str, unicode)):
            raise KeyError('Keys must be `str` or `unicode`')

        return self.__data__.get(k, default)

    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError:
            raise AttributeError("Attribute '%s' not found" % attr)

    def __setattr__(self, attr, value):
        self[attr] = value

    def __set_data(self, data):
        self.__dict__['__data__'] = {}

        for k, v in data.items():
            self[k] = v

    def __get_data(self):
        return {k: self.__unwrap(v) for k, v in self.__data__.items()}

    def __wrap(self, data):
        if isinstance(data, self.__valid_types__):
            return data
        elif isinstance(data, (list, tuple)):
            return [self.__wrap(d) for d in data]
        elif isinstance(data, dict):
            return Thing(data)
        elif isinstance(data, Thing):
            return data
        elif self.allow_non_json:
            return data
        else:
            raise ValueError('Type `%s` is not allowed.' % str(type(data)))

    def __unwrap(self, data):
        if isinstance(data, self.__valid_types__):
            return data
        elif isinstance(data, (list, tuple)):
            return [self.__unwrap(d) for d in data]
        elif isinstance(data, Thing):
            return data.__get_data()
        elif self.allow_non_json:
            return data
        else:
            raise AssertionError('Type `%s` should not be allowed.' %
                                 (str(type(data))))

    def __str__(self):
        return str(self.dict())

    def __repr__(self):
        return repr(self.dict())


if __name__ == '__main__':
    thing = Thing()
    thing.name = 'Mr. Thing'
    thing.age = 42

    thing_son = Thing(name='Thing Jr.', age=20)
    thing_daughter = Thing(name='Miss Thing', age=15, dog=Thing(name='Dog'))

    thing.sons = [thing_son, thing_daughter]

    from pprint import pprint
    pprint(thing.dict())

    thing.sons[1].dog.name = 'Doggie'

    pprint(thing.dict())
