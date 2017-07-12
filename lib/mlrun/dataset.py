import numpy as np

import mlrun.config

from tabulate import tabulate

def printlist():
  print("Source datasets:")
  metadata = [ [m.name,m.description] for m in mlrun.config.datasets.list() ]
  print(tabulate(metadata))

def helptext():
  dataset_summaries = [ "%s[:%s]" % (m.name, "|".join(m.subsets)) for m in mlrun.config.datasets.list() ]
  return ", ".join(dataset_summaries)

def fetch(source, name, **kwargs):
  for s in mlrun.config.datasets.list():
    if s.name == source:
      dset = s.fetch(name, **kwargs)
      return dset

  return None

def fetch_local(source, name):
  for s in mlrun.config.datasets.list():
    if s.name == source:
      dset = s.fetch(name)
      return dset

  return None

class Dataset:
  def __init__(self, labels, features):
    self.dense_labels = labels
    self.labels = self.dense_labels
    self.features = features

  def size(self):
    return len(self.labels)

  def one_hot_index(self, dense_value):
    return dense_value

  def one_hot_category_count(self):
    return 10

  def one_hot_labels(self):
    oh_labels = np.zeros([len(self.dense_labels), self.one_hot_category_count()])
    label_indices = [self.one_hot_index(dense_label) for dense_label in self.dense_labels]
    oh_labels[np.arange(len(self.dense_labels)), label_indices] = 1
    return oh_labels

  def toggle_one_hot(self, on=False):
    self.labels = self.one_hot_labels() if on else self.dense_labels