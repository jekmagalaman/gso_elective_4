import pandas as pd
from django.apps import apps
from django.db import models

def process_migration(file_path, target_model):
    """
    Reads Excel/CSV and inserts data into the target model.
    Works whether target_model is a string or a model class.
    """
    # Auto-detect file type
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    else:
        df = pd.read_excel(file_path)

    # 🔹 If we got a string, resolve it to model class
    if isinstance(target_model, str):
        app_label, model_name = target_model.split(".")
        model_class = apps.get_model(app_label, model_name)
    elif isinstance(target_model, models.Model):
        model_class = target_model.__class__
    else:
        model_class = target_model   # already a class

    # Filter only valid fields to avoid unexpected columns
    valid_fields = {f.name for f in model_class._meta.get_fields()}

    for _, row in df.iterrows():
        data = {k: v for k, v in row.to_dict().items() if k in valid_fields}
        model_class.objects.create(**data)
