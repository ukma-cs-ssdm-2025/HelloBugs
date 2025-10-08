import os
import yaml
from src.api.app import app, api

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

docs_dir = os.path.join(project_root, "docs")
os.makedirs(docs_dir, exist_ok=True)

yaml_path = os.path.join(docs_dir, "openapi-generated.yaml")

with app.app_context():
    spec = api.spec.to_dict()
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(spec, f, sort_keys=False, allow_unicode=True)

print(f"OpenAPI spec generated: {yaml_path}")
