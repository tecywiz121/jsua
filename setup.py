from setuptools import setup, find_packages

try:
    import pypandoc
    long_description = pypandoc.convert('README.md', 'rst')
except ImportError:
    with open('README.md') as f:
        long_description = f.read()

setup(name='jsua',
      version='0.1.0',
      description='A parser for JSON that can start at an arbitrary point in the file',
      long_description=long_description,

      author='Sam Wilson',
      author_email='sam@binarycake.ca',

      url='https://github.com/tecywiz121/jsua',

      license='LGPL',

      classifiers=[
          'Development Status :: 3 - Alpha',
          'Intended Audience :: Developers',
          'Programming Language :: Python :: 3',
          'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)'
      ],

      setup_requires=['cffi>=1.9.1'],
      cffi_modules=['jsua/_jsua_builder.py:ffibuilder'],
      install_requires=['cffi>=1.9.1'],

      packages=['jsua'])
