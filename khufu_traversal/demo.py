'''To run this demo, simply execute::

  $ python -m khufu_traversal.demo
'''

import transaction
from paste.httpserver import serve
from pyramid.response import Response
from pyramid.config import Configurator
from sqlalchemy import (
    Column, ForeignKey, Unicode, Integer, Table, String)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from khufu_traversal import MappingRoot


def main():
    '''Listen on port 8080 with the demo application.
    '''

    config = Configurator(root_factory=MappingRoot)
    config.registry.settings['sqlalchemy.url'] = \
        'sqlite:////tmp/khufu_sqlalchemy.demo.db'
    config.include('khufu_sqlalchemy')

    config.include('khufu_traversal')
    GroupContainer = config.setup_model_container(Group, [('users', User)])
    UserContainer = config.setup_model_container(User, [('groups', Group)])

    config.add_view(index_view, context=MappingRoot)
    config.add_view(groups_view,
                    context=GroupContainer)
    config.add_view(users_view,
                    context=UserContainer)
    config.add_view(user_view, context=User)
    config.add_view(group_view, context=Group)

    Base.metadata.create_all(bind=config.registry.settings['khufu.dbengine'])
    setup_data(config)
    app = config.make_wsgi_app()
    serve(app, host='0.0.0.0')


def setup_data(config):
    s = config.registry.settings['khufu.dbsession_factory']()
    transaction.begin()

    for x in range(1, 3):
        username = 'user' + str(x)
        u = s.query(User).filter_by(username=username).scalar()
        if u is None:
            u = User(username=username,
                     email=username + u'@' + username + u'.com',
                     id=x)
            s.add(u)

        groupname = 'group' + str(x)
        if s.query(Group.id).filter_by(groupname=groupname).count() == 0:
            u.groups.append(Group(groupname=groupname, id=x))
    s.flush()

    grp = s.query(Group).filter_by(groupname='commongroup').scalar()
    if grp is None:
        grp = Group(groupname='commongroup', id=3)
        s.add(grp)
    u = s.query(User).filter_by(username='user1').scalar()
    if grp not in u.groups:
        u.groups.append(grp)
        s.add(u)
    u = s.query(User).filter_by(username='user2').scalar()
    if grp not in u.groups:
        u.groups.append(grp)
        s.add(u)

    transaction.commit()
    s.close()


Base = declarative_base()


user_groups_table = Table(
    'user_groups', Base.metadata,
    Column('user_id', ForeignKey('users.id')),
    Column('group_id', ForeignKey('groups.id'))
    )


class Group(Base):
    '''SQLAlchemy model representing a Group.
    '''

    __tablename__ = 'groups'

    id = Column(Integer, primary_key=True)
    groupname = Column(String(20), nullable=False)

    def __repr__(self):
        return '(Group groupname="%s")' % self.groupname


class User(Base):
    '''SQLAlchemy model representing a User.
    '''

    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(20), nullable=False)
    email = Column(Unicode(50), nullable=False)
    groups = relationship(Group, secondary=user_groups_table, backref='users')


def index_view(request):
    return Response('<ul><li><a href="users/">Users</a></li><li><a href="groups/">Groups</a></li></ul>')


def groups_view(request):
    s = '<div>total groups: %i\n<ul>' % len(request.context)
    for x in request.context:
        s += '<li><a href="%s/">%i - %s</a>\n' % ('/groups/' + str(x.id), x.id, x.groupname)
    s += '</ul>'
    return Response(s)


def users_view(request):
    s = '<div>total users: %i\n<ul>' % len(request.context)
    for x in request.context:
        s += '<li><a href="%s/">%i - %s</a>\n' % ('/users/' + str(x.id), x.id, x.username)
        if len(x.groups) > 0:
            s += '<ul>'
            for y in x.groups:
                s += '<li><a href="%s/">%i - %s</a>\n' % ('/groups/' + str(y.id), y.id, y.groupname)
            s += '</ul>'
    s += '</ul>'
    return Response(s)


def user_view(request):
    s = '<div>User: %s (<a href="groups/">groups</a>)</div>' % request.context.username
    return Response(s)


def group_view(request):
    s = '<div>Group: %s (<a href="users/">users</a>)</div>' % request.context.groupname
    return Response(s)


if __name__ == '__main__':
    main()
