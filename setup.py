import sys
from os import path

from setuptools import find_namespace_packages, find_packages, setup

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

type = "prod"
if "--dev" in sys.argv:
    type = "dev"
    sys.argv.remove("--dev")

requires = [
    'requests', 'responses', 'psutil', 'PyJWT', 'py-cpuinfo', 'pySMART'
]
setup(name='pynas-{}'.format(type),
      version='0.0.1',
      description='PyDriveSync',
      author='Benoît Laviale',
      author_email='contact@benoit-laviale.fr',
      license='MIT',
      packages=find_namespace_packages(),
      install_requires=requires,
      entry_points={
          "console_scripts": [
              "pyDriveSync=pydrivesync.client:run_{}".format(type)
          ]
},
    zip_safe=False)
