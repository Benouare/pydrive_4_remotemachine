import sys
from os import path

from setuptools import find_namespace_packages, find_packages, setup

from pydrivesync import constance

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

requires = [
    'pydrive2',
]
setup(name='pydrivesync',
      version=constance.__VERSION__,
      description='PyDriveSync',
      author='Benoît Laviale',
      author_email='contact@benoit-laviale.fr',
      license='MIT',
      packages=find_namespace_packages(),
      install_requires=requires,
      entry_points={
          "console_scripts": [
              "pydrivesync=pydrivesync.client:run"
          ],
      },
      data_files=[("/pydrivesync/", ["pydrivesync/pydrivesync.yaml"])],
      zip_safe=False
      )
