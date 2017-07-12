import mlrun.config

from tabulate import tabulate

def helptext():
  model_summaries = [ m.name for m in mlrun.config.models.list() ]
  return ", ".join(model_summaries)

def load(model_name):
  for m in mlrun.config.models.list():
    if m.name == model_name:
      return m
  return None

def list():
  print("Available Models:")
  metadata = [ [m.name, m.description] for m in mlrun.config.models.list() ]
  print(tabulate(metadata))
