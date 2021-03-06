
import sys
from setuptools import setup, find_packages

setup_args = dict(
    name='gillcup_graphics',
    version='0.2.0-alpha.1',
    packages=find_packages(),

    description="""Pyglet graphics for Gillcup""",
    author='Petr Viktorin',
    author_email='encukou@gmail.com',
    install_requires=['gillcup>=0.2.0-alpha', 'pyglet==1.1.4'],
    classifiers=[
            'Intended Audience :: Developers',
            'License :: OSI Approved :: MIT License',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 2.6',
            'Programming Language :: Python :: 2.7',
            'Topic :: Software Development :: Libraries',
        ],

    tests_require=['pytest', 'pytest-pep8'],
    test_suite='gillcup_graphics.test.test_suite',
    package_data={'': ['.pylintrc', '*.png']},
)

if sys.version_info < (3, 0):
    setup_args['tests_require'].append('pylint')

if __name__ == '__main__':
    setup(**setup_args)
