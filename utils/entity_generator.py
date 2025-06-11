import json
import os
import re
import uuid # For generating privilege IDs
from jinja2 import Environment, FileSystemLoader

# Helper function to convert entity_name to snake_case for filenames/variables
def to_snake_case(name: str) -> str:
    if not name:
        return ""
    # Add an underscore before an uppercase letter if it's preceded by a lowercase letter or digit,
    # but not if it's preceded by an underscore (to avoid double underscores).
    name = re.sub(r'(?<=[a-z0-9])(?=[A-Z])', r'_', name)
    # Add an underscore before an uppercase letter if it's preceded by another uppercase letter
    # and followed by a lowercase letter (e.g., SimpleHTTPServer -> Simple_HTTP_Server)
    # This also helps with acronyms like HTMLWorld -> HTML_World if not already split by previous rule.
    name = re.sub(r'(?<=[A-Z])(?=[A-Z][a-z])', r'_', name)
    return name.lower().replace('__', '_') # Ensure any introduced double underscores are cleaned.

# Helper function to convert entity_name to PascalCase for class names
# This is the version from the previous successful test run (after my fix for pascal case)
def to_pascal_case(name: str) -> str:
    if not name:
        return ""

    # Heuristic for already PascalCase names like "ProductItem" or "Project"
    if '_' not in name and name[0].isupper():
        is_pascal_like = True
        # Check for all caps like "UUID" or "ID"
        if name.isupper():
            # Standard behavior: "UUID" -> "Uuid", "ID" -> "Id"
            return name[0] + name[1:].lower() if len(name) > 1 else name

        # For mixed case like "ProductItem"
        # Check if it contains lowercase characters after the first letter
        has_lower_after_first = any(c.islower() for c in name[1:])
        if has_lower_after_first:
             # If it's like "ProductItem" (mixed case after first char), assume it's intended PascalCase
             return name
        else:
            # If all caps after first (e.g. "PRoject" which is unlikely, or "PPROJECT"),
            # or single char "P", fallback to default splitting behavior.
            # But if it's like "PROject" this will be an issue.
            # The current test cases "ProductItem" and "project" are the main drivers.
            # "ProductItem" is returned as is. "project" goes to default.
            pass # Fall through to default splitting if not clearly "ProductItem" like or all caps.


    # Default for snake_case or other variants: split by underscore, capitalize each part.
    # "hello_world" -> "HelloWorld"
    # "product_item" -> "ProductItem"
    # "project" -> "Project" (split results in ['project'], then capitalize)
    return "".join(word.capitalize() for word in name.replace('-', '_').split('_'))


# Jinja2 filter to map general types to SQLAlchemy types
def map_sqlalchemy_type(general_type):
    mapping = {
        "string": "String",
        "text": "Text",
        "integer": "Integer",
        "float": "Float",
        "boolean": "Boolean",
        "datetime": "DateTime",
        "uuid": "UUID",
    }
    return mapping.get(general_type.lower(), "String")

# Jinja2 filter to map general types to Pydantic types
def map_pydantic_type(general_type):
    mapping = {
        "string": "str",
        "text": "str",
        "integer": "int",
        "float": "float",
        "boolean": "bool",
        "datetime": "datetime",
        "uuid": "UUID",
    }
    return mapping.get(general_type.lower(), "str")

# Jinja2 filter for Pydantic default values
def map_pydantic_default(default_value):
    if default_value is None:
        return "None"
    if isinstance(default_value, bool):
        return str(default_value)
    if isinstance(default_value, (int, float)):
        return str(default_value)
    return f'"{default_value}"'

def generate_entity_files(json_string: str, base_output_path: str = "."):
    try:
        entities_data = json.loads(json_string)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return

    template_dir = os.path.join(base_output_path, "templates")
    if not os.path.isdir(template_dir):
        print(f"Templates directory not found at {template_dir}")
        if os.path.isdir("templates"):
            template_dir = "templates"
        elif os.path.isdir(os.path.join(os.path.dirname(__file__), "..", "templates")):
             template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
        else:
            print("Templates directory not found at ./templates or ../templates either. Aborting.")
            return

    env = Environment(loader=FileSystemLoader(template_dir))
    env.filters['map_sqlalchemy_type'] = map_sqlalchemy_type
    env.filters['map_pydantic_type'] = map_pydantic_type
    env.filters['map_pydantic_default'] = map_pydantic_default
    env.filters['to_snake_case'] = to_snake_case
    env.filters['to_pascal_case'] = to_pascal_case

    layers = ["models", "schemas", "routers", "services", "repositories"]
    for layer in layers:
        os.makedirs(os.path.join(base_output_path, layer), exist_ok=True)

    generated_files_info = []
    all_sql_privileges = []

    for entity_data in entities_data:
        original_entity_name = entity_data.get("name", "UnnamedEntity")
        entity_name_pascal = to_pascal_case(original_entity_name)
        entity_name_snake = to_snake_case(original_entity_name)

        context = {
            "entity_name": entity_name_pascal,
            "entity_name_snake": entity_name_snake,
            "entity_description": entity_data.get("description", ""),
            "properties": entity_data.get("properties", []),
            "relationships": entity_data.get("relationships", []),
        }

        for rel in context["relationships"]:
            original_target_name = rel.get('target_entity', '')
            rel['target_entity_pascal'] = to_pascal_case(original_target_name)
            rel['target_entity_snake'] = to_snake_case(original_target_name)
            if rel.get('type') == 'many-to-one':
                rel['foreign_key_column'] = rel.get('foreign_key_column', f"{rel['target_entity_snake']}_id")

        template_files = {
            "models": "models/model.py.j2",
            "schemas": "schemas/schema.py.j2",
            "routers": "routers/router.py.j2",
            "services": "services/service.py.j2",
            "repositories": "repositories/repository.py.j2",
        }

        for layer, template_name in template_files.items():
            try:
                template = env.get_template(template_name)
                rendered_content = template.render(context)

                output_filename_base = entity_name_snake
                output_filename = f"{output_filename_base}.py"
                if layer == "schemas":
                    output_filename = f"{output_filename_base}_schema.py"

                output_path = os.path.join(base_output_path, layer, output_filename)

                with open(output_path, "w") as f:
                    f.write(rendered_content)
                generated_files_info.append(f"Generated: {output_path}")

            except Exception as e:
                generated_files_info.append(f"Error generating {layer} for {entity_name_pascal}: {e}")

        privilege_actions = ["create", "read", "update", "delete"]
        for action in privilege_actions:
            priv_name = f"{entity_name_snake}:{action}"
            priv_description = f"Allows to {action} {entity_name_snake} entities."
            priv_id = str(uuid.uuid4())
            created_at = "NOW()"
            updated_at = "NOW()"
            sql = f"INSERT INTO privilege (id, name, description, entity, action, created_at, updated_at, is_deleted) " \
                  f"VALUES ('{priv_id}', '{priv_name}', '{priv_description}', '{entity_name_snake}', '{action}', {created_at}, {updated_at}, FALSE);"
            all_sql_privileges.append(sql)

    for info in generated_files_info:
        print(info)

    privileges_sql_path = os.path.join(base_output_path, "generated_privileges.sql")
    try:
        with open(privileges_sql_path, "w") as f:
            for sql_statement in all_sql_privileges:
                f.write(sql_statement + "\n")
        print(f"Successfully generated SQL privileges at: {privileges_sql_path}")
    except Exception as e:
        print(f"Error writing SQL privileges file: {e}")


if __name__ == "__main__":
    print("Running entity generator example (with SQL generation)...")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    actual_template_dir = os.path.join(project_root, "templates")
    if not os.path.isdir(actual_template_dir):
        print(f"CRITICAL: Actual templates directory not found at {actual_template_dir} for __main__ test.")
        os.makedirs(os.path.join(actual_template_dir, "models"), exist_ok=True)
        with open(os.path.join(actual_template_dir, "models/model.py.j2"), "w") as f: f.write("Dummy Model: {{ entity_name }}")
        print("Created dummy templates for __main__ because actual ones were missing.")

    test_json_data_str = """
    [
      {
        "name": "Invoice",
        "description": "Represents a customer invoice.",
        "properties": [
          {"name": "invoice_number", "type": "string", "is_nullable": false, "is_unique": true, "description": "Unique invoice number"},
          {"name": "amount", "type": "float", "is_nullable": false, "description": "Total amount of the invoice"}
        ],
        "relationships": []
      }
    ]
    """

    print(f"Project root (for template lookup and output): {project_root}")
    generate_entity_files(test_json_data_str, base_output_path=project_root)
    print("Entity generation example finished. Check project root for generated files and generated_privileges.sql.")
    print("The __main__ block now attempts to use the templates restored in the previous step.")
