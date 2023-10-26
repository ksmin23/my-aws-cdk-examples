import io
import os

import numpy as np
import pandas as pd
import mlflow


def model_fn(model_dir):
    print(f"model dir: {model_dir}")
    model = mlflow.sklearn.load_model(f"{model_dir}/model")
    return model


def predict_fn(input_object, model):
    print("calling model")
    predictions = model.predict(input_object)
    return predictions


def input_fn(input_data, content_type):
    print("processing input")
    if content_type == "application/x-npy":
        npy_input = np.load(io.BytesIO(input_data))
        df = pd.DataFrame(npy_input)
        return df
    elif content_type == "text/csv":
        # Read the raw input data as CSV.
        df = pd.read_csv(io.StringIO(input_data))
        return df
    else:
        raise ValueError("{} not supported by script!".format(content_type))
