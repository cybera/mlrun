from os.path import dirname, basename, isfile, splitext, sep as pathsep, join
from glob import glob
import sys, imp

# Import any submodules automatically within the module. Add a 'list()'
# function that lists all the submodules. If named arguments are passed
# in, set variables of the same name under the module and all submodules.
# This will allow, for example, default imports that the files will not
# have to specify themselves to use.
#
# Example:
# 
# preload_module(models, paths=mlrun.config.paths)
# - equivalent to "import mlrun.config.paths as paths" in each submodule
def preload_module(module, **kwargs):
  # Get just the filename of all *.py files under the current folder
  file_mask = pathsep.join([module_dir(module), "*.py"])
  modules = [basename(f) for f in glob(file_mask) if isfile(f)]

  # Remove the extension and filter out this file
  submodules = [splitext(f)[0] for f in modules if f != "__init__.py"]
  module.__setattr__('__all__', submodules)

  for submodule in submodules:
    __import__(module.__name__ + ".%s"% submodule)

  add_module_variables(module, **kwargs)

  # Add "list" function to list submodules
  def list_submodules():
    m = sys.modules[module.__name__]
    return [ getattr(m, x) for x in module.__all__ ]
  setattr(module, 'list', list_submodules)

# Figure out the relative path of the module.
def module_dir(module):
  if hasattr(module, '__file__'):  
    # If the module has an __init__.py file, the __file__ variable will exist
    path = dirname(module.__file__)
  elif hasattr(module.__path__, '_path'):
    # If the module is just a namespace, it's a little more complicated to get
    # the relative path.
    path = module.__path__._path[0]
  else:
    raise("Can't get module path for %s" % module.__name__)
  return path

# Go through all keyword arguments and set them as variables in the 
# module and its submodules
def add_module_variables(module, **kwargs):
  for m in ([module] + [getattr(module, subm) for subm in module.__all__]):
    for key in kwargs:
      setattr(m, key, kwargs[key])

import builtins, importlib

def import_relative(name, path, namespace=None):
  file, filename, data = imp.find_module(name, [path])

  if namespace is not None:
    name = ".".join([namespace, name])
  return imp.load_module(name, file, filename, data)

def create_global_module(name):
  submodules = name.split(".")
  module_stack = [builtins]

  for i, submodule_name in enumerate(submodules):
    parent_module = module_stack[i]

    submodule = None
    if hasattr(parent_module, submodule_name):
      submodule = getattr(parent_module, submodule_name)
    else:
      if submodule_name in sys.modules:
        submodule = importlib.import_module(submodule_name)
      else:
        submodule = imp.new_module(submodule_name)
        submodule.__all__ = []
      
      setattr(parent_module, submodule_name, submodule)

      if hasattr(parent_module, '__all__'):
        parent_module.__all__.append(submodule_name)
    module_stack.append(submodule)

  return module_stack.pop()

def namespace_folder(namespace, path):
  file_mask = pathsep.join([path, "*.py"])
  modules = [basename(f) for f in glob(file_mask) if isfile(f)]
  # Remove the extension and filter out this file
  submodules = [splitext(f)[0] for f in modules if f != "__init__.py"]

  namespace_module = create_global_module(namespace)

  for submodule_name in submodules:
    # Provide a namespace to prevent reloading submodules of the same name over
    # one another.
    submodule = import_relative(submodule_name, path, namespace=namespace)
    setattr(namespace_module, submodule_name, submodule)
    namespace_module.__all__.append(submodule_name)

  def list_submodules():
    return [ getattr(namespace_module, x) for x in namespace_module.__all__ ]
  setattr(namespace_module, 'list', list_submodules)

  return namespace_module
