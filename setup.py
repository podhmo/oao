import os

from setuptools import setup, find_packages
here = os.path.abspath(os.path.dirname(__file__))
try:
    with open(os.path.join(here, 'README.rst')) as f:
        README = f.read()
    with open(os.path.join(here, 'CHANGES.txt')) as f:
        CHANGES = f.read()
except IOError:
    README = CHANGES = ''

install_requires = [
    "typing_extensions",
]

docs_extras = []

dev_extras = [
    "mypy",
    "mypy_extensions",
]

tests_require = []

testing_extras = tests_require + []

setup(
    name='oao',
    version='0.0.0',
    description='openapi object',
    long_description=README + '\n\n' + CHANGES,
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
    keywords='',
    author="",
    author_email="",
    url="",
    packages=find_packages(exclude=["oao.tests"]),
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    extras_require={
        'testing': testing_extras,
        'docs': docs_extras,
        'dev': dev_extras,
    },
    tests_require=tests_require,
    test_suite="oao.tests",
    entry_points="""
"""
)
