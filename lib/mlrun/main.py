#!/usr/bin/env python

# config (basic path setup, etc.)
import mlrun.config as config

import argparse

import mlrun

import os
import inspect

from keras.models import load_model

def help(model):
  print("I don't know what you're talking about, there is no model '%s'" % model)

def parse_dataset(dataset, dataset_default):
  parts = dataset.split(":")
  if len(parts) > 1:
    return parts
  else:
    return [parts[0],dataset_default]

def model_help():
  return """
  Name of the model you want to run.

  Available models: %s
  """ % mlrun.model.helptext()

def dataset_help():
  return """
  DATASET[:SUBSET]
  If no SUBSET is given, the subset will be assumed to match the mode (train or test)

  Available datasets: %s

  """ % mlrun.dataset.helptext()

def mode_help():
  return """
  train|test
  If not specified, the model is both trained and tested

  """

def initialize():
  datasets_path = os.path.join(config.project_root, "datasets")
  models_path = os.path.join(config.project_root, "models")
  datasets_module = ".".join([config.project_prefix, "datasets"])
  models_module = ".".join([config.project_prefix, "models"])

  mlrun.config.datasets = mlrun.util.namespace_folder(datasets_module, datasets_path)
  mlrun.config.models = mlrun.util.namespace_folder(models_module, models_path)

  mlrun.util.add_module_variables(mlrun.config.datasets, mlrun=mlrun,
                                                         paths=config.paths,
                                                         Dataset=mlrun.dataset.Dataset)
  mlrun.util.add_module_variables(mlrun.config.models, mlrun=mlrun,
                                                       paths=config.paths)
  # Call project specific config dynamically?

# argv is expected to be from sys.argv (and thus contain the original script name
# as the very first argument)
def start(argv):
  parser = argparse.ArgumentParser(description='Run a predictive model', 
                                   formatter_class=argparse.RawTextHelpFormatter)
  parser.add_argument("model", help=model_help().lstrip())
  parser.add_argument("--mode", action="store", default=None, help=mode_help().lstrip())
  parser.add_argument("--dataset", action="store", default="helloworld", help=dataset_help().lstrip())
  parser.add_argument("--no-rebuild", action="store_true", help="When training, if a model has already been saved, continue training it")
  parser.add_argument("--model-name", action="store", help="Name of the model to save/load")

  args = parser.parse_args(args=argv[1:])
  model = mlrun.model.load(args.model)

  if model is None:
    print("Model '%s' not found." % args.model)
    mlrun.model.list()
  else:
    derived_args = {}
    derived_args['model'] = model_instance(model, args.model_name, args.no_rebuild)

    steps = [args.mode] if args.mode else ["train", "test"]

    print("Running %s..." % ", ".join(steps))

    for step in steps:
      dataset_name, subset_name = parse_dataset(args.dataset, step)
      dataset = mlrun.dataset.fetch(dataset_name, subset_name)
      derived_args['dataset'] = dataset
      print("%s dataset: %s (%s - size: %i)" % 
            (step, dataset_name, subset_name, len(dataset.labels)))
      model_func = getattr(model, step)
      extra_args = mlrun.util.exclude_keys(args, ['model', 'dataset'])
      model_func_args = mlrun.util.build_args(model_func, [derived_args, extra_args])
      model_func(**model_func_args)
      if step == "train":
        save_model(model, derived_args['model'], args.model_name)

    if "train" in steps:
      save_model(model, derived_args['model'], args.model_name)

def model_instance(model_mod, model_name=None, no_rebuild=False):
  if no_rebuild:
    if not model_name:
      model_name = model_mod.name
    return load_model(config.paths.saved_model("%s.h5" % model_name))
  else:
    return model_mod.build()

def save_model(model_mod, model_instance, model_name=None):
  if not model_name:
    model_name = model_mod.name

  model_instance.save(config.paths.saved_model("%s.h5" % model_name))