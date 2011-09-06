import abc
import sqlalchemy.orm
import khufu_sqlalchemy
import zope.interface
import collections
import pyramid_traversalwrapper

Mapping = collections.namedtuple(
    'Mapping', 'model base modelcontainer traversal_name')


class ITraversalSetup(zope.interface.Interface):
    '''Interface describing the traversal-setup utility.
    '''

    model_containers = zope.interface.Attribute('model_containers')
    attr_containers = zope.interface.Attribute('attr_containers')
    bases = zope.interface.Attribute('bases')
    traversal_names = zope.interface.Attribute('traversal_names')
    proxies = zope.interface.Attribute('proxies')


class TraversalSetup(object):
    '''State management for the traversal functionality.
    '''

    zope.interface.implements(ITraversalSetup)

    def __init__(self):
        self.model_containers = {}
        self.attr_containers = {}
        self.bases = {}
        self.traversal_names = {}
        self.proxies = {}


def get_or_set_util(c):
    mappings = c.registry.queryUtility(ITraversalSetup)
    if mappings is None:
        mappings = TraversalSetup()
        c.registry.registerUtility(mappings,
                                   provided=ITraversalSetup)
    return mappings


class BaseContainer(object):

    def __str__(self):
        return '<%s>' % str(self.__class__.__name__)
    __repr__ = __str__


def get_or_set_base(c, model):
    mappings = get_or_set_util(c)
    base = mappings.bases.get(model, None)
    if base is not None:
        return base

    base_name = model.__name__ + 'Container'
    base = type(base_name,
                (BaseContainer, ),
                {})
    mappings.bases[model] = base
    return base


def expose_attrs(c, model, attr_mappings):
    mappings = get_or_set_util(c)
    for k, v in attr_mappings:
        attr_base = get_or_set_base(c, v)
        attr_class = mappings.attr_containers.get(v, None)
        if attr_class is None:
            attr_class = type(v.__name__ + 'AttrProvidedContainer',
                              (AttrProvidedContainer, attr_base,),
                              {'attr_name': k,
                               'model_class': v})
            mappings.attr_containers[v] = attr_class

    if model in mappings.proxies:
        proxy = mappings.proxies[model]
        for k, v in attr_mappings:
            proxy._dict_items[k] = mappings.attr_containers[v]
    else:
        d = {}
        for k, v in attr_mappings:
            d[k] = mappings.attr_containers[v]

        name = model.__name__.lower().title() + 'TraversalProxy'
        proxy = type(name, (TraversalProxy,), {'_dict_items': d})
        mappings.proxies[model] = proxy

    return proxy


def setup_model_container(c, model, attr_mappings=None,
                          base=None, traversal_name=None):
    '''Create a new container class, register it with khufu_traversal,
    and return the result.  If traversal_name is unspecified or None
    then traversal_name will become the lowercase and plural spelling
    of the model name (ie model=User, traversal_name=users).
    '''

    mappings = get_or_set_util(c)
    if mappings.model_containers.get(model, None) is not None:
        return mappings.model_containers.get(model)

    if base is None:
        base = get_or_set_base(c, model)

    base_name = model.__name__
    model_container_class = type(
        base_name + 'ModelContainer',
        (ModelContainer, base),
        {'model_class': model})

    expose_attrs(c, model, attr_mappings or [])

    if traversal_name is None:
        traversal_name = model.__name__.lower() + 's'
    mappings.model_containers[model] = mapping = Mapping(
        model, base, model_container_class, traversal_name)
    mappings.traversal_names[traversal_name] = mapping

    return base


class TraversalError(Exception):
    pass


class TraversalProxy(pyramid_traversalwrapper.LocationProxy):
    __slots__ = ('__parent__', '__name__', '__request__',
                 '__request__', '_dict_items', '__acl__')

    def __new__(self, ob, container=None, name=None, request=None,
                dict_items=None):
        return pyramid_traversalwrapper.LocationProxy.__new__(self, ob)

    def __init__(self, ob, container=None, name=None, request=None,
                 dict_items=None):
        if dict_items is None:
            dict_items = {}
        pyramid_traversalwrapper.LocationProxy.__init__(
            self, ob, container, name)
        self.__request__ = request
        self._dict_items = dict_items
        self._cache = {}

    def __getitem__(self, k):
        v = self._cache.get(k, 1)
        if v == 1:
            if k in self._dict_items:
                v = self._dict_items[k](k, self, request=self.__request__)
                self._cache[k] = v
                return v
            else:
                self._cache[k] = None
        elif v is not None:
            return v

        raise TraversalError(k)


class Locatable(object):
    '''Mixin representing anything with a name and parent'''

    __name__ = None
    __parent__ = None


class ResourceContainer(Locatable):
    '''All containers created are subclasses of ResourceContainer.
    '''

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __getitem__(self, k):
        pass

    @abc.abstractmethod
    def __iter__(self, k):
        pass

    def wrap(self, subobj, name):
        mappings = get_or_set_util(self.request)
        proxy = mappings.proxies.get(self.model_class, None)
        if proxy is not None:
            subobj = proxy(ob=subobj, container=self,
                           name=name, request=self.request)
        subobj.__name__ = name
        subobj.__parent__ = self
        return subobj

    def traversal_to_pk(self, traversal_name):
        if not isinstance(traversal_name, basestring):
            raise TypeError('key must be a string, not an '
                            'instance of: ' + str(type(traversal_name)))

        cols = [int(x) for x in traversal_name.split('-')]
        return tuple(cols)

    def pk_to_traversal(self, pk):
        return unicode(pk)

    def get_pk(self, o):
        mapper = sqlalchemy.orm.object_mapper(o)
        return mapper.primary_key_from_instance(o)

    def __str__(self):
        return '<%s>' % str(self.__class__.__name__)
    __repr__ = __str__


class AttrProvidedContainer(ResourceContainer):
    '''A location-aware container for models that live as
    an iterable attr of another object.  Primarily this
    is used to map to relationship attributes on a model.
    '''

    model_class = None
    attr_name = None

    def __init__(self, name=None, parent=None, attr_name=None,
                 request=None):
        super(AttrProvidedContainer, self).__init__()

        if name is None:
            name = attr_name
        self.__name__ = name
        self.parent = parent
        if attr_name is not None:
            self.attr_name = attr_name
        self._pk_map = None
        self.request = request

    @property
    def attr(self):
        return getattr(self.parent, self.attr_name)

    def __getitem__(self, k):
        pk = self.traversal_to_pk(k)

        if self._pk_map is not None:
            return self.wrap(self._pk_map[pk], k)

        self._pk_map = {}
        for resource in self.attr:
            self._pk_map[tuple(self.get_pk(resource))] = resource

        return self.wrap(self._pk_map[pk], k)

    def __iter__(self):
        for x in self.attr:
            pk = self.get_pk(x)
            yield self.wrap(x, self.pk_to_traversal(pk))

    def __len__(self):
        return len(self.attr)

    def __str__(self):
        return '<%s>' % str(self.__class__.__name__)
    __repr__ = __str__


class ModelContainer(ResourceContainer):
    '''A location-aware container for models that can be
    given an arbitrary filter_by expression.
    '''

    model_class = None

    def __init__(self,
                 name=None,
                 parent=None,
                 request=None,
                 model_class=None,
                 filter_by_kwargs={}):
        super(ModelContainer, self).__init__()

        self.__name__ = name
        self.__parent__ = parent
        if model_class is not None:
            self.model_class = model_class
        self.request = request
        self.filter_by_kwargs = filter_by_kwargs

    def __getitem__(self, k):
        db = khufu_sqlalchemy.dbsession(self.request)

        o = db.query(self.model_class).get(self.traversal_to_pk(k))

        if self.filter_by_kwargs:
            for k, v in self.filter_by_kwargs.items():
                if getattr(o, k, None) != v:
                    raise KeyError(k)

        return self.wrap(o, k)

    def __len__(self):
        return self.get_query().count()

    def get_query(self, **kwargs):
        db = khufu_sqlalchemy.dbsession(self.request)
        q = db.query(self.model_class)

        filter_by_kwargs = dict(self.filter_by_kwargs or {})
        filter_by_kwargs.update(kwargs)
        if filter_by_kwargs:
            q = q.filter_by(**filter_by_kwargs)
        return q

    def filter_by(self, **kwargs):
        '''Return an iterable of data objects that applies the
        default filter passed into the constructor plus the *kwargs*
        argument here.
        '''

        q = self.get_query(**kwargs)

        for obj in q:
            mapper = sqlalchemy.orm.object_mapper(obj)
            pk = mapper.primary_key_from_instance(obj)
            yield self.wrap(obj, self.pk_to_traversal(pk))

    def __iter__(self):
        return self.filter_by()


def get_model_container(c, model_class):
    u = get_or_set_util(c)
    # make sure it's setup first
    c.setup_model_container(model_class)
    o = u.model_containers.get(model_class, None)
    return o.modelcontainer
