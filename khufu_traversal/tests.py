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
        self.assertEqual(rc.traversal_to_pk(u'1'), u'1')

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

    def test_id_pk(self):
        from sqlalchemy import Column, Integer
        self._test_it(id=Column(Integer, primary_key=True))

    def test_simple_pk(self):
        from sqlalchemy import Column, Integer
        self._test_it(pk=Column(Integer, primary_key=True))

    def test_compound_pk(self):
        from sqlalchemy import Column, Integer
        self._test_it(pk1=Column(Integer, primary_key=True),
                      pk2=Column(Integer, primary_key=True))

    def _test_it(self, **cols):
        from khufu_traversal import AttrProvidedContainer

        MockObj = create_model_class(**cols)
        children = [MockObj(name=1), MockObj(name=2)]
        parent = Mock(children=children)

        container = AttrProvidedContainer('foo', parent, 'children')
        self.assertEqual(children, [x for x in container])
