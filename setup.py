import io
from setuptools import setup

import nr_stomp


def read(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)


setup(author='Jonathan Sharpe',
      author_email='jsharpe@trl.co.uk',
      classifiers=['Programming Language :: Python :: 2.7',
                   'Programming Language :: Python :: 2 :: Only',
                   'Development Status :: 2 - Pre-Alpha',
                   'Natural Language :: English',
                   'Operating System :: OS Independent',
                   'Topic :: Scientific/Engineering'],
      description='STOMP client for Network Rail\'s public data.',
      include_package_data=True,
      install_requires=['stompest>=2.1.6'],
      license='License :: OSI Approved :: MIT License',
      long_description=read('README.md'),
      name='nr_stomp',
      packages=['nr_stomp'],
      platforms='any',
      scripts=['scripts/run_client.py'],
      version=nr_stomp.__version__)
