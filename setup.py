from setuptools import setup, find_packages
setup(name='mlrun',
      version='1.0',
      packages=find_packages("lib"),
      package_dir={'':'lib'},
      install_requires = [],
      scripts=['bin/mlrun'])