import abc
import logging

import sqlalchemy.orm
import khufu_sqlalchemy

logger = logging.getLogger('khufu_traversal')


class Locatable(object):
    __name__ = None
    __parent__ = None


class ResourceContainer(Locatable):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __getitem__(self, k):
        pass

    @abc.abstractmethod
    def __iter__(self, k):
        pass

    def wrap(self, subobj, name):
        subobj.__name__ = name
        subobj.__parent__ = self
        return subobj

    def traversal_to_pk(self, traversal_name):
        cols = [int(x) for x in traversal_name.split('-')]
        return tuple(cols)

    def pk_to_traversal(self, pk):
        return unicode(pk)

    def get_pk(self, o):
        mapper = sqlalchemy.orm.object_mapper(o)
        return mapper.primary_key_from_instance(o)


class AttrProvidedContainer(ResourceContainer):
    '''A location-aware container for models that live as
    an iterable attr of another object.
    '''

    def __init__(self, name=None, parent=None, attr_name=None):
        if name is None:
            name = attr_name
        self.__name__ = name
        self.parent = parent
        self.attr_name = attr_name
        self._pk_map = None

    @property
    def attr(self):
        return getattr(self.parent, self.attr_name)

    def __getitem__(self, k):
        if not isinstance(k, basestring):
            raise TypeError('key must be a string, not an '
                            'instance of: ' % str(type(k)))

        pk = self.traversal_to_pk(k)

        if self._pk_map is not None:
            return self.wrap(self._pk_map[pk], k)

        self._pk_map = {}
        for resource in self.attr:
            self._pk_map[tuple(self.get_pk(resource))] = resource

        return self.wrap(self._pk_map[pk], k)

    def __iter__(self):
        for x in self.attr:
            yield self.wrap(x, self.pk_to_traversal(self.get_pk(x)))


class SQLContainer(ResourceContainer):
    '''A location-aware container for models that can be
    given an arbitrary filter_by expression.
    '''

    model_class = None

    def __init__(self, name=None, parent=None, request=None,
                 filter_by_kwargs={}):
        super(SQLContainer, self).__init__()

        self.__name__ = name
        self.__parent__ = parent
        self.request = request
        self.filter_by_kwargs = filter_by_kwargs

    def __getitem__(self, k):
        if not isinstance(k, basestring):
            raise TypeError('key must be a string, not an '
                            'instance of: ' % str(type(k)))

        db = khufu_sqlalchemy.dbsession(self.request)

        o = db.query(self.model_class).get(self.traversal_to_pk(k))
        if o is None:
            raise KeyError(k)

        if self.filter_by_kwargs:
            for k, v in self.filter_by_kwargs.items():
                if getattr(o, k) != v:
                    raise KeyError(k)

        return self.wrap(o, k)

    def filter_by(self, **kwargs):
        '''Return an iterable of data objects that applies the
        default filter passed into the constructor plus the *kwargs*
        argument here.
        '''

        db = khufu_sqlalchemy.dbsession(self.request)
        q = db.query(self.model_class)

        filter_by_kwargs = dict(self.filter_by_kwargs or {})
        filter_by_kwargs.update(kwargs)
        if filter_by_kwargs:
            q = q.filter_by(**filter_by_kwargs)

        for obj in q:
            yield self.wrap(obj, self.pk_to_traversal(obj.id))

    def __iter__(self):
        return self.filter_by()
