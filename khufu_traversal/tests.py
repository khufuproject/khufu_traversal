import unittest


class Mock(object):

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class MockRegistry(object):

    def __init__(self):
        pass

    def queryUtility(self, x):
        pass

    def registerUtility(self, x, provided):
        pass


class MainTests(unittest.TestCase):

    def test_include(self):
        from khufu_traversal import includeme

        directives = []

        def add_directive(x, y):
            directives.append((x, y))

        c = Mock(add_directive=add_directive)
        includeme(c)

        self.assertEqual(len(directives), 3)

    def test_mapping_root(self):
        from khufu_traversal import MappingRoot
        root = MappingRoot(Mock(registry=MockRegistry()))

        m = root._cache['foo'] = Mock()
        self.assertTrue(root['foo'] is m)

        self.assertRaises(KeyError, root.__getitem__, 'bar')


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


class BaseContainerTests(unittest.TestCase):
    def test_str(self):
        from khufu_traversal._api import BaseContainer
        bc = BaseContainer()
        self.assertEqual(str(bc), '<BaseContainer>')


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
