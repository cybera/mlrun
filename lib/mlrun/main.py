#!/usr/bin/env python

# config (basic path setup, etc.)
import mlrun.config as config

import argparse

import mlrun

import os
import inspect

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

  args = parser.parse_args(args=argv[1:])
  model = mlrun.model.load(args.model)

  if model is None:
    print("Model '%s' not found." % args.model)
    mlrun.model.list()
  else:
    if args.mode:
      dataset_name, subset_name = parse_dataset(args.dataset, args.mode)
      dataset = mlrun.dataset.fetch(dataset_name, subset_name)

      print("Running %s..." % args.mode)
      print("Dataset: %s (%s - size: %i)" % (dataset_name, subset_name, len(dataset.labels)))

      model_func = getattr(model, args.mode)
      # kind of hacky way to allow modes that don't need a data set (mainly for visualizations
      # of a model after it has been made)
      if len(inspect.getargspec(model_func).args) > 0:
        model_func(dataset)
      else:
        model_func()

    else:
      dataset_name, train_subset_name = parse_dataset(args.dataset, "train")
      _, test_subset_name = parse_dataset(args.dataset, "test")

      train = mlrun.dataset.fetch(dataset_name, train_subset_name)
      test = mlrun.dataset.fetch(dataset_name, test_subset_name)

      print("Running train and test...")
      print("Train dataset: %s (%s - size: %i)" % (dataset_name, train_subset_name, len(train.labels)))
      print("Test dataset: %s (%s - size: %i)" % (dataset_name, test_subset_name, len(test.labels)))  

      model.train(train)
      model.test(test)
