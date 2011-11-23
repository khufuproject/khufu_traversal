import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()

required = [
    'khufu_sqlalchemy',
    'pyramid_traversalwrapper',
]


setup(name='khufu_traversal',
      version='1.0a1',
      description='Helper for working with SQL-based traversal in Pyramid',
      long_description=README + '\n\n' + CHANGES,
      license='BSD',
      classifiers=[
        "License :: OSI Approved :: BSD License",
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python",
        ],
      author='Rocky Burt',
      author_email='rocky@serverzen.com',
      url='http://khufuproject.github.com/khufu_traveral/',
      keywords='web wsgi pylons pyramid sql traversal',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=required,
      tests_require=required,
      test_suite="khufu_traversal.tests",
      )
