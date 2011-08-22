import unittest


class Mock(object):

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class SetupTests(unittest.TestCase):

    def setUp(self):
        from pyramid.testing import setUp
        self.config = setUp()

    def tearDown(self):
        from pyramid.testing import tearDown
        self.config = None
        tearDown()

    def test_setup(self):
        from khufu_traversal import ITraversalSetup
        self.config.include('khufu_traversal')
        self.assertTrue(hasattr(self.config, 'setup_model_container'))
        self.config.setup_model_container(Mock)
        m = self.config.registry.queryUtility(ITraversalSetup)
        self.assertNotEqual(m, None)


class RegistrationTests(unittest.TestCase):

    def setUp(self):
        from pyramid.testing import setUp
        self.config = setUp()

        from khufu_traversal._api import setup_model_container

        class MyModel(object):
            @property
            def children(self):
                return [Mock(a=1), Mock(b=2)]

        setup_model_container(self.config, MyModel,
                              [('children', Mock)])

    def tearDown(self):
        from pyramid.testing import tearDown
        self.config = None
        tearDown()

    def test_it(self):
        from khufu_traversal._api import ITraversalSetup

        m = self.config.registry.queryUtility(ITraversalSetup)
        # should be 2, one for MyModel and another for Mock
        self.assertEqual(len(m.bases), 2)
        self.assertEqual(len(m.attr_containers), 1)
        self.assertEqual(len(m.model_containers), 1)


# class ResourceContainerTests(unittest.TestCase):

#     def setUp(self):
#         from khufu_traversal._api import ResourceContainer

#         class MyContainer(ResourceContainer):
#             def __iter__(self): pass
#             def __getitem__(self, k): pass

#         self.Container = MyContainer

#     def test_wrap(self):
#         rc = self.Container()
#         m = Mock()
#         x = rc.wrap(m, 'foo')

#         self.assertEqual(x.__name__, 'foo')
#         self.assertEqual(x.__parent__, rc)

#     def test_traversal_to_pk(self):
#         rc = self.Container()
#         self.assertEqual(rc.traversal_to_pk(u'1'), (1,))

#     def test_pk_to_traversal(self):
#         rc = self.Container()
#         self.assertEqual(rc.pk_to_traversal(1), u'1')


def create_model_class(**cols):
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy import Column, Unicode

    Base = declarative_base()

    class_fields = {
        '__tablename__': 'foo',
        'name': Column(Unicode(100))
        }
    class_fields.update(cols)
    return type('MockObj', (Base,), class_fields)


# class AttrProvidedContainerTests(unittest.TestCase):

#     def make_container(self):
#         from sqlalchemy import Column, Integer

#         from khufu_traversal._api import AttrProvidedContainer

#         MockObj = create_model_class(id=Column(Integer, primary_key=True))
#         children = [
#             MockObj(id=1),
#             MockObj(id=2),
#             MockObj(id=3),
#             ]
#         parent = Mock(children=children)
#         return AttrProvidedContainer('foo', parent, attr_name='children')

#     def test_nameless_constructor(self):
#         from khufu_traversal._api import AttrProvidedContainer
#         container = AttrProvidedContainer(attr_name='foo',
#                                           name=None)
#         self.assertEqual(container.__name__, 'foo')

#     def test_getitem(self):
#         container = self.make_container()

#         # test bad traversal name type
#         self.assertRaises(TypeError, lambda: container[5])

#         self.assertEqual(container[u'1'], container.parent.children[0])

#         # check the lazy property setting
#         self.assertEqual(container[u'1'], container.parent.children[0])

#     def test_iter(self):
#         container = self.make_container()
#         self.assertEqual([x for x in container], container.parent.children)


# class AttrProvidedContainerCompoundPKTests(unittest.TestCase):

#     def make_container(self):
#         from sqlalchemy import Column, Integer

#         from khufu_traversal._api import AttrProvidedContainer

#         MockObj = create_model_class(pk1=Column(Integer, primary_key=True),
#                                      pk2=Column(Integer, primary_key=True))
#         children = [
#             MockObj(pk1=10, pk2=6000),
#             MockObj(pk1=10, pk2=7000),
#             MockObj(pk1=20, pk2=43),
#             ]
#         parent = Mock(children=children)

#         class Request(object):
#             environ = {}

#             def session_factory():
#                 return None

#             registry = Mock(
#                 settings={'khufu.dbsession_factory': session_factory})

#         return AttrProvidedContainer('foo', parent, attr_name='children',
#                                      request=Request())

#     def test_getitem(self):
#         container = self.make_container()
#         self.assertEqual(container[u'10-6000'],
#                          container.parent.children[0])


# class ModelContainerTests(unittest.TestCase):

#     def setUp(self):
#         from sqlalchemy import Column, Integer
#         MockObj = create_model_class(id=Column(Integer, primary_key=True))

#         class Session(object):
#             data = {(1,): MockObj(id=1, name='grr'),
#                     (2,): MockObj(id=2, name='abc'),
#                     (3,): MockObj(id=3, name='foo'),
#                     (4,): MockObj(id=4, name='yes')}

#             def query(self, model_class):
#                 return self

#             def get(self, pk):
#                 return self.data[pk]

#             def __iter__(self):
#                 return iter(self.data.values())

#             def filter_by(self, **kwargs):
#                 for x in self.data.values():
#                     passed = filter(lambda tup: getattr(x, tup[0], None) == tup[1],
#                                     kwargs.items())
#                     if len(passed) == len(kwargs):
#                         yield x

#         class Request(object):
#             environ = {}

#             def session_factory():
#                 return Session()

#             @staticmethod
#             def add_finished_callback(f):
#                 pass

#             registry = Mock(
#                 settings={'khufu.dbsession_factory': session_factory})

#         self.session = Session
#         self.request = Request()

#         from khufu_traversal._api import ModelContainer
#         self.container = ModelContainer(model_class=MockObj,
#                                         request=self.request)

#     def test_getitem(self):
#         container = self.container
#         session = self.session

#         self.assertEqual(getattr(session.data[(1,)], '__name__', None), None)
#         self.assertEqual(container['1'], session.data[(1,)])
#         self.assertEqual(getattr(session.data[(1,)], '__name__', None), '1')

#         # test missing object
#         self.assertRaises(KeyError, lambda: container['5'])

#     def test_getitem_filter_by(self):
#         container = self.container
#         container.filter_by_kwargs = {'name': 'abc'}

#         self.assertRaises(KeyError, lambda: container['1'])
#         self.assertTrue(container['2'] is not None)

#     def test_filter_by(self):
#         container = self.container
#         session = self.session

#         self.assertEqual(set([x.id for x in container.filter_by()]),
#                          set([x.id for x in session.data.values()]))
#         self.assertEqual(set([x.id for x in container.filter_by(name='abc')]),
#                          set([2]))

#     def test_iter(self):
#         container = self.container
#         session = self.session

#         self.assertEqual(set([x.id for x in container]),
#                          set([x.id for x in session.data.values()]))
