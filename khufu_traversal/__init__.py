import khufu_traversal._api
from khufu_traversal._api import (
    ITraversalSetup,
    Locatable,
    ResourceContainer,
    )


def includeme(c):
    '''"Include" method for pyramid.
        ``config.include('khufu_traversal')``
    '''

    c.add_directive('setup_model_container',
                    khufu_traversal._api.setup_model_container)
    c.add_directive('expose_attrs',
                    khufu_traversal._api.expose_attrs)


class MappingRoot(object):
    '''A root factory that is aware of khufu registered traversal
    models.
    '''

    def __init__(self, request):
        self.request = request
        self._cache = {}

    def __getitem__(self, k):
        if k in self._cache:
            return self._cache[k]

        m = khufu_traversal._api.get_or_set_util(self.request)
        mapping = m.traversal_names.get(k, None)
        if mapping is None:
            raise KeyError(k)

        self._cache[k] = mapping.modelcontainer(request=self.request)
        return self._cache[k]
