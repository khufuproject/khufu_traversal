import unittest


class Mock(object):

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class ResourceContainerTests(unittest.TestCase):

    @property
    def Container(self):
        if hasattr(self, 'container_class'):
            return self._container_class

        from khufu_traversal import ResourceContainer

        class MyContainer(ResourceContainer):
            def __iter__(self): pass
            def __getitem__(self, k): pass

        self._container_class = MyContainer
        return self._container_class

    def test_wrap(self):
        rc = self.Container()
        m = Mock()
        x = rc.wrap(m, 'foo')

        self.assertEqual(x.__name__, 'foo')
        self.assertEqual(x.__parent__, rc)

    def test_traversal_to_pk(self):
        rc = self.Container()
        self.assertEqual(rc.traversal_to_pk(u'1'), (1,))

    def test_pk_to_traversal(self):
        rc = self.Container()
        self.assertEqual(rc.pk_to_traversal(1), u'1')


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


class AttrProvidedContainerTests(unittest.TestCase):

    def make_container(self):
        from sqlalchemy import Column, Integer

        from khufu_traversal import AttrProvidedContainer

        MockObj = create_model_class(id=Column(Integer, primary_key=True))
        children = [
            MockObj(id=1),
            MockObj(id=2),
            MockObj(id=3),
            ]
        parent = Mock(children=children)
        return AttrProvidedContainer('foo', parent, attr_name='children')

    def test_nameless_constructor(self):
        from khufu_traversal import AttrProvidedContainer
        container = AttrProvidedContainer(attr_name='foo',
                                          name=None)
        self.assertEqual(container.__name__, 'foo')

    def test_getitem(self):
        container = self.make_container()
        self.assertRaises(TypeError, lambda: container[5])
        self.assertEqual(container[u'1'], container.parent.children[0])

        # check the lazy property setting
        self.assertEqual(container[u'1'], container.parent.children[0])

    def test_iter(self):
        container = self.make_container()
        self.assertEqual([x for x in container], container.parent.children)


class AttrProvidedContainerCompoundPKTests(unittest.TestCase):

    def make_container(self):
        from sqlalchemy import Column, Integer

        from khufu_traversal import AttrProvidedContainer

        MockObj = create_model_class(pk1=Column(Integer, primary_key=True),
                                     pk2=Column(Integer, primary_key=True))
        children = [
            MockObj(pk1=10, pk2=6000),
            MockObj(pk1=10, pk2=7000),
            MockObj(pk1=20, pk2=43),
            ]
        parent = Mock(children=children)
        return AttrProvidedContainer('foo', parent, attr_name='children')

    def test_getitem(self):
        container = self.make_container()
        self.assertEqual(container[u'10-6000'],
                         container.parent.children[0])
