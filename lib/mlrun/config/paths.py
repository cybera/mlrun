import os.path

data = "data"
data_raw = os.path.join(data, "raw")
data_processed = os.path.join(data, "processed")
data_models = os.path.join(data, "models")

results = "results"
results_plots = os.path.join(results, "plots")

def saved_model(filename):
  return os.path.join(data_models, filename)

def plot(filename):
  return os.path.join(results_plots, filename)