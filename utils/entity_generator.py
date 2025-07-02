import json
import os
import re
import uuid # For generating privilege IDs
from jinja2 import Environment, FileSystemLoader
from utils.terminal_ui import TerminalUI

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
def map_sqlalchemy_type(prop: dict):
    general_type = prop.get("type")

    if prop.get("is_enum_array"):
        enum_class_name = prop.get("enum_class_name")
        enum_sql_name = prop.get("enum_sql_type_name") # This is the base name like 'my_enum_type'
        enum_create_sql_type = prop.get("enum_create_sql_type", True)

        # The template will need to ensure 'Enum' and 'ARRAY' (from postgresql) are imported.
        # Example SQLAlchmey: Column(ARRAY(Enum(PythonEnumName, name='sql_enum_name', create_type=True)))
        return {
            "is_special": True,
            "type_string": "ARRAY",
            "inner_type": f"Enum({enum_class_name}, name='{enum_sql_name}_enum', create_type={str(enum_create_sql_type)})"
            # Appending '_enum' to sql_name for the actual SQL type to differentiate from table/column names if necessary,
            # and to follow a common convention for SQL enum type names.
        }
    else:
        mapping = {
            "string": "String",
            "text": "Text",
            "integer": "Integer",
            "float": "Float",
            "boolean": "Boolean",
            "datetime": "DateTime",
            "uuid": "UUID",
            # other simple types
        }
        return {
            "is_special": False,
            "type_string": mapping.get(str(general_type).lower(), "String") # Ensure general_type is string for .lower()
        }

# Jinja2 filter to map general types to Pydantic types
def map_pydantic_type(prop: dict):
    general_type = prop.get("type")

    if prop.get("is_enum_array"):
        enum_class_name = prop.get("enum_class_name")
        # Pydantic schema will need the Python Enum class to be imported.
        # e.g., from ..models.enums import YourEnumClassName
        return f"List[{enum_class_name}]"
    else:
        mapping = {
            "string": "str",
            "text": "str",
            "integer": "int",
            "float": "float",
            "boolean": "bool",
            "datetime": "datetime",
            "uuid": "UUID",
            # other simple types
        }
        return mapping.get(str(general_type).lower(), "str") # Ensure general_type is string

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
    ui = TerminalUI()
    ui.display_section_header("Entity Generation Process Starting")

    try:
        entities_data = json.loads(json_string)
    except json.JSONDecodeError as e:
        ui.display_error(f"Error decoding JSON: {e}")
        return

    template_dir = os.path.join(base_output_path, "templates")
    if not os.path.isdir(template_dir):
        ui.display_warning(f"Templates directory not found at {template_dir}")
        if os.path.isdir("templates"):
            template_dir = "templates"
            ui.display_info("Found templates directory at ./templates")
        elif os.path.isdir(os.path.join(os.path.dirname(__file__), "..", "templates")):
             template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
             ui.display_info(f"Found templates directory at {template_dir}")
        else:
            ui.display_error("Critical: Templates directory not found. Aborting.")
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

    all_sql_privileges = []
    all_enums_to_generate = {} # Initialize dictionary to store unique enum definitions

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

        # Process properties for enum_array types
        for prop in context["properties"]:
            if prop.get("type") == "enum_array":
                enum_options = prop.get("enum_options")
                if not enum_options or not isinstance(enum_options, dict):
                    ui.display_warning(f"Property '{prop['name']}' in entity '{original_entity_name}' is 'enum_array' but missing valid 'enum_options'. Skipping.")
                    prop["type"] = "string" # Fallback or mark as invalid
                    continue

                enum_class_name = enum_options.get("name")
                enum_values = enum_options.get("values")
                create_sql_type = enum_options.get("create_sql_type", True) # Default to True

                if not enum_class_name or not enum_values or not isinstance(enum_values, list):
                    ui.display_warning(f"Enum '{enum_class_name}' for property '{prop['name']}' in entity '{original_entity_name}' has invalid 'name' or 'values'. Skipping.")
                    prop["type"] = "string" # Fallback or mark as invalid
                    continue

                prop["is_enum_array"] = True
                prop["enum_class_name"] = enum_class_name
                prop["enum_values_list"] = enum_values
                prop["enum_create_sql_type"] = create_sql_type
                prop["enum_sql_type_name"] = to_snake_case(enum_class_name) # SQL type name for CREATE TYPE
                # Note: The template will add "_sql_enum" or similar if needed for the actual SQL type name vs Python class name.
                # For now, this is the base name for the SQL type. The Python class will use enum_class_name.

                if enum_class_name not in all_enums_to_generate:
                    all_enums_to_generate[enum_class_name] = {
                        "values": enum_values,
                        "sql_name": prop["enum_sql_type_name"], # This is the SQL type name, e.g., 'work_item_status_enum'
                        "create_sql_type": create_sql_type,
                        "class_name": enum_class_name # PascalCase name for Python class
                    }
                else:
                    # Optional: Validate consistency if multiple definitions for the same enum name
                    if all_enums_to_generate[enum_class_name]["values"] != enum_values:
                        ui.display_warning(f"Enum '{enum_class_name}' redefined with different values in entity '{original_entity_name}'. Using first definition.")
                    # Update create_sql_type only if the new one is True and old one was False
                    if create_sql_type and not all_enums_to_generate[enum_class_name]["create_sql_type"]:
                         all_enums_to_generate[enum_class_name]["create_sql_type"] = True


        # Enhanced relationship processing
        for rel in context["relationships"]:
            original_target_name = rel.get('target_entity', '')
            # Standard case conversions for target entity
            rel['pascal_case_target_entity'] = to_pascal_case(original_target_name)
            rel['snake_case_target_entity'] = to_snake_case(original_target_name)

            # Carry through back_populates attribute
            rel['back_populates_attribute'] = rel.get('back_populates')

            rel_type = rel.get('type')

            # Initialize all boolean flags to False
            rel['is_one_to_one'] = False
            rel['is_one_to_many_parent'] = False
            rel['is_many_to_one_child'] = False
            rel['is_many_to_many'] = False
            rel['has_foreign_key_in_self'] = False # Default, can be overridden

            if rel_type == "one-to-one":
                rel['is_one_to_one'] = True
                rel['uselist_attr_value'] = False
                if rel.get('foreign_key_on') == 'self':
                    rel['has_foreign_key_in_self'] = True
                    rel['foreign_key_column_name'] = rel.get('foreign_key_column', f"{rel['snake_case_target_entity']}_id")
                else: # FK is on target
                    rel['has_foreign_key_in_self'] = False

            elif rel_type == "one-to-many": # Current entity is the 'one' side
                rel['is_one_to_many_parent'] = True
                rel['uselist_attr_value'] = True

            elif rel_type == "many-to-one": # Current entity is the 'many' side
                rel['is_many_to_one_child'] = True
                rel['uselist_attr_value'] = False
                rel['has_foreign_key_in_self'] = True
                rel['foreign_key_column_name'] = rel.get('foreign_key_column', f"{rel['snake_case_target_entity']}_id")

            elif rel_type == "many-to-many":
                rel['is_many_to_many'] = True
                rel['uselist_attr_value'] = True

                association_table_name_json = rel.get('association_table_name')
                current_entity_snake_name = context['entity_name_snake']

                if association_table_name_json:
                    rel['association_config_name'] = association_table_name_json
                else:
                    sorted_names = sorted([current_entity_snake_name, rel['snake_case_target_entity']])
                    rel['association_config_name'] = f"{sorted_names[0]}_{sorted_names[1]}_association"

                rel['association_left_fk_column'] = f"{current_entity_snake_name}_id"
                rel['association_right_fk_column'] = f"{rel['snake_case_target_entity']}_id"
                rel['association_left_fk_target'] = f"{current_entity_snake_name}.id"
                rel['association_right_fk_target'] = f"{rel['snake_case_target_entity']}.id"
                rel['association_metadata_ref'] = "BaseModel.metadata"


        template_files = {
            "models": "models/model.py.j2",
            "schemas": "schemas/schema.py.j2",
            "routers": "routers/router.py.j2",
            "services": "services/service.py.j2",
            "repositories": "repositories/repository.py.j2",
        }

        context["all_enums_to_generate"] = all_enums_to_generate # Make global enums available to templates

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
                ui.display_success(f"Generated: {output_path}")

            except Exception as e:
                ui.display_error(f"Error generating {layer} for {entity_name_pascal}: {e}")

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

    # After processing all entities and their files, show summary of Enums to be generated
    if all_enums_to_generate:
        ui.display_section_header("Summary of Python Enum Classes to be Generated")
        for enum_name, enum_details in all_enums_to_generate.items():
            ui.display_info(f"- {enum_details['class_name']} (Values: {', '.join(enum_details['values'])})")

    privileges_sql_path = os.path.join(base_output_path, "generated_privileges.sql")
    try:
        with open(privileges_sql_path, "w") as f:
            for sql_statement in all_sql_privileges:
                f.write(sql_statement + "\n")
        ui.display_success(f"SQL privileges generated at: {privileges_sql_path}")

        if all_sql_privileges:
            ui.display_section_header("Generated SQL Privileges")
            for sql_statement in all_sql_privileges:
                print(sql_statement) # Using print as per initial plan
    except Exception as e:
        ui.display_error(f"Error writing SQL privileges file: {e}")

    ui.display_section_header("Entity Generation Complete")
    ui.display_info("All entities processed. Review generated files and SQL output above.")


if __name__ == "__main__":
    ui = TerminalUI() # Instantiate for __main__ block
    ui.display_section_header("Entity Generator - __main__ Example")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    actual_template_dir = os.path.join(project_root, "templates")
    if not os.path.isdir(actual_template_dir):
        ui.display_error(f"CRITICAL: Actual templates directory not found at {actual_template_dir} for __main__ test.")
        # Attempt to create dummy templates if missing (as per original logic)
        try:
            os.makedirs(os.path.join(actual_template_dir, "models"), exist_ok=True)
            with open(os.path.join(actual_template_dir, "models/model.py.j2"), "w") as f:
                f.write("Dummy Model: {{ entity_name }}")
            ui.display_warning("Created dummy model template for __main__ because actual one was missing.")
        except Exception as e_mkdir:
            ui.display_error(f"Could not create dummy templates: {e_mkdir}")


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

    ui.display_info(f"Project root (for template lookup and output): {project_root}")
    generate_entity_files(test_json_data_str, base_output_path=project_root)
    # The generate_entity_files function now has its own completion messages.
    # Add a final message specific to the __main__ block completion.
    ui.display_info("Standalone generator __main__ example run finished.")
