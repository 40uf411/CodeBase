# Feature: Entity Generator

This document describes the Entity Generator utility, a powerful tool for scaffolding new entities within the My Platform application.

## Overview

The Entity Generator (`utils/entity_generator.py`) automates the creation of boilerplate code for new data models and their associated application layers. By defining your entity's structure in a JSON file, you can quickly generate:

-   **SQLAlchemy Models**: (`models/your_entity.py`)
-   **Pydantic Schemas**: (`schemas/your_entity_schema.py`) for request/response validation and serialization.
-   **FastAPI Routers**: (`routers/your_entity.py`) with CRUD endpoint definitions.
-   **Service Layers**: (`services/your_entity.py`) for business logic.
-   **Repository Layers**: (`repositories/your_entity.py`) for database interactions.
-   **SQL Privileges**: (`generated_privileges.sql`) an SQL script to insert basic CRUD privileges for the new entity.

**Benefits:**
-   **Speed**: Rapidly create the foundational code for new entities.
-   **Consistency**: Ensures all entities follow a standardized structure and naming conventions.
-   **Reduced Boilerplate**: Minimizes repetitive coding tasks.

## Location of the Script

The generator script is located at: `utils/entity_generator.py`

## Input: The JSON Definition File

The Entity Generator is driven by a JSON file that describes the entities you want to create. A comprehensive example can be found in `test.json` in the project root.

### Top-Level JSON Structure

The JSON input should be a list of objects, where each object represents an entity to be generated.

```json
[
  {
    // Entity 1 definition
  },
  {
    // Entity 2 definition
  }
  // ... more entities
]
```

### Entity Object Attributes

Each entity object in the list can have the following attributes:

-   **`name`** (String, Required):
    The name of the entity. It's recommended to use PascalCase (e.g., "ProductItem") or snake_case (e.g., "product_item"). The generator will normalize this to PascalCase for class names and snake_case for filenames and variable names.
    *Example:* `"name": "Project"`

-   **`description`** (String, Optional):
    A brief description of the entity. This will be used in the docstring of the generated SQLAlchemy model.
    *Example:* `"description": "Represents a project with multiple tasks."`

-   **`properties`** (Array of Objects, Optional):
    A list defining the attributes (columns in the database table) for the entity. Each property object has its own set of attributes.

-   **`relationships`** (Array of Objects, Optional):
    A list defining the relationships this entity has with other entities. Each relationship object has its own set of attributes.

### `properties` Array Structure

Each object in the `properties` array defines a single attribute of the entity:

-   **`name`** (String, Required):
    The name of the property (e.g., "title", "creation_date"). This will be converted to snake_case.
    *Example:* `"name": "start_date"`

-   **`type`** (String, Required):
    The general data type of the property. The generator maps these to appropriate SQLAlchemy and Pydantic types. Supported general types include:
    -   `"string"` (maps to `String` in SQLAlchemy, `str` in Pydantic)
    -   `"text"` (maps to `Text` in SQLAlchemy, `str` in Pydantic)
    -   `"integer"` (maps to `Integer` in SQLAlchemy, `int` in Pydantic)
    -   `"float"` (maps to `Float` in SQLAlchemy, `float` in Pydantic)
    -   `"boolean"` (maps to `Boolean` in SQLAlchemy, `bool` in Pydantic)
    -   `"datetime"` (maps to `DateTime` in SQLAlchemy, `datetime` in Pydantic)
    -   `"uuid"` (maps to `UUID` in SQLAlchemy, `UUID` in Pydantic)
    *Example:* `"type": "datetime"`

-   **`is_nullable`** (Boolean, Optional, Default: `false`):
    Set to `true` if the property can have a `NULL` value in the database.
    *Example:* `"is_nullable": true`

-   **`is_unique`** (Boolean, Optional, Default: `false`):
    Set to `true` if the property must have a unique value in the database.
    *Example:* `"is_unique": true` for an email field.

-   **`is_indexed`** (Boolean, Optional, Default: `false`):
    Set to `true` to create a database index on this property for faster queries.
    *Example:* `"is_indexed": true` for frequently queried fields.

-   **`default_value`** (Any, Optional):
    The default value for the property if none is provided. The type should match the property's `type`.
    *Example:* `"default_value": false` for an `is_active` boolean field. `"default_value": 0` for a quantity.

-   **`description`** (String, Optional):
    A description for this property, often used for comments in the generated model or schema.
    *Example:* `"description": "When the project is scheduled to start"`

**Example Property:**
```json
{
  "name": "budget",
  "type": "float",
  "is_nullable": true,
  "description": "Allocated budget for the project"
}
```

### `relationships` Array Structure

Each object in the `relationships` array defines a link to another entity:

-   **`name`** (String, Required):
    The name of the relationship attribute in the generated SQLAlchemy model (e.g., "author", "comments").
    *Example:* `"name": "tasks"` (for a project's tasks)

-   **`type`** (String, Required):
    The type of relationship. Supported types:
    -   `"one-to-many"`: One instance of this entity relates to many instances of the target entity.
    -   `"many-to-one"`: Many instances of this entity relate to one instance of the target entity. (This entity will have the foreign key).
    -   `"many-to-many"`: Many instances of this entity relate to many instances of the target entity (requires an association table).
    -   `"one-to-one"`: (Basic support) One instance of this entity relates to one instance of the target entity. The templates provide basic support, usually assuming the current entity is the parent and the foreign key is on the child.
    *Example:* `"type": "one-to-many"`

-   **`target_entity`** (String, Required):
    The name of the other entity involved in this relationship (PascalCase or snake_case).
    *Example:* `"target_entity": "Task"`

-   **`back_populates`** (String, Required):
    The name of the corresponding relationship attribute on the `target_entity` model. This is crucial for SQLAlchemy to correctly link bi-directional relationships.
    *Example:* If a `Project` has `tasks` (one-to-many to `Task`), the `Task` model should have a `project` attribute (many-to-one to `Project`), so `back_populates` for `Project.tasks` would be `"project"`.

-   **`foreign_key_column`** (String, Optional):
    Applicable primarily for `"many-to-one"` relationships. Specifies the name of the foreign key column that will be created in the current entity's table to link to the `target_entity`.
    If not provided, it defaults to `{{target_entity_snake}}_id` (e.g., if `target_entity` is "UserProfile", defaults to "user_profile_id").
    *Example:* `"foreign_key_column": "project_id"` (in a `Task` entity relating to `Project`)

-   **`association_table_name`** (String, Optional):
    Applicable only for `"many-to-many"` relationships. Allows you to explicitly name the intermediary association table.
    If not provided, the model template generates a default name like `{{current_entity_snake}}_{{target_entity_snake}}_association` (e.g., "task_tag_association").
    *Example:* `"association_table_name": "task_tags_association"`

-   **`is_nullable`** (Boolean, Optional, Default for FK in many-to-one: `true`):
    For a `"many-to-one"` relationship, this determines if the foreign key column can be `NULL`. Set to `false` if the relationship is mandatory.
    *Example:* `"is_nullable": false` if a `Task` must always belong to a `Project`.

-   **`description`** (String, Optional):
    A description for this relationship, used for comments in the model.
    *Example:* `"description": "Tasks associated with this project."`

**Example Relationship (Project having many Tasks):**
In `Project` entity definition:
```json
{
  "name": "tasks",
  "type": "one-to-many",
  "target_entity": "Task",
  "back_populates": "project",
  "description": "Tasks associated with this project."
}
```
And in `Task` entity definition (corresponding many-to-one):
```json
{
  "name": "project",
  "type": "many-to-one",
  "target_entity": "Project",
  "back_populates": "tasks",
  "foreign_key_column": "project_id",
  "is_nullable": false,
  "description": "The project this task belongs to."
}
```

---
*(Part 2 will cover how to run the script and understand its output.)*

## How to Run the Entity Generator

### Prerequisites

-   **Python Environment**: Ensure you have a Python environment set up with all project dependencies installed (see [Installation Guide](../getting-started/installation.md)).
-   **Jinja2**: The generator uses Jinja2 for templating. It's included in the `utils/entity_generator.py` script's imports and should be available if project dependencies are installed.
-   **JSON Definition File**: Prepare your entity definitions in a JSON file (e.g., `my_entities.json`) following the structure described above. The `test.json` in the project root serves as a good example.

### Executing the Script

The script `utils/entity_generator.py` is designed to be run from the command line. It expects the JSON data as a string argument to its main generation function. Typically, you would read your JSON file in a wrapper script or directly in Python and pass the content.

For direct testing or simple use, the script also includes an `if __name__ == "__main__":` block which demonstrates how to load a JSON file and call the generator. You can modify this block to point to your custom JSON file.

**Example (Modifying `utils/entity_generator.py`'s `__main__` block):**

1.  Open `utils/entity_generator.py`.
2.  Locate the `if __name__ == "__main__":` section.
3.  Change the `test_json_data` variable to load your JSON file:

    ```python
    # Inside utils/entity_generator.py's __main__ block
    if __name__ == "__main__":
        print("Running entity generator...")

        # Path to your JSON definition file
        json_file_path = "test.json" # Or "path/to/your/entities.json"

        try:
            with open(json_file_path, "r") as f:
                json_string_data = f.read()
            print(f"Successfully loaded JSON from {json_file_path}")
        except FileNotFoundError:
            print(f"Error: JSON file not found at {json_file_path}")
            exit()
        except Exception as e:
            print(f"Error reading JSON file: {e}")
            exit()

        # Define where generated files should be placed (project root by default for subdirectories)
        output_base_path = "." # Generates into ./models, ./schemas, etc.

        generate_entity_files(json_string_data, base_output_path=output_base_path)
        print(f"Entity generation process finished. Check the output directories under {os.path.abspath(output_base_path)}.")
    ```

4.  Run the script from the project root:
    ```bash
    python utils/entity_generator.py
    ```

The script will then process your JSON file and generate the entity files.

## Output Files

Upon successful execution, the generator will create the following files for each entity defined in your JSON (e.g., for an entity named "YourEntity"):

-   **Model**: `models/your_entity.py`
    -   Contains the SQLAlchemy model class.
-   **Schemas**: `schemas/your_entity_schema.py`
    -   Contains Pydantic schemas (Base, Create, Update, Response).
-   **Router**: `routers/your_entity.py`
    -   Contains FastAPI router with CRUD endpoints.
-   **Service**: `services/your_entity.py`
    -   Contains the service class with business logic stubs.
-   **Repository**: `repositories/your_entity.py`
    -   Contains the repository class for database interactions.

Filenames will be in `snake_case` (e.g., "ProductItem" becomes `product_item.py`).

### SQL Privileges File

-   **File**: `generated_privileges.sql` (in the project root)
-   **Content**: Contains SQL `INSERT` statements to add CRUD privileges for each generated entity into the `privilege` table.
    ```sql
    -- Example for an entity 'your_entity':
    INSERT INTO privilege (id, name, description, entity, action, created_at, updated_at, is_deleted) VALUES ('...', 'your_entity:create', 'Allows to create your_entity entities.', 'your_entity', 'create', NOW(), NOW(), FALSE);
    INSERT INTO privilege (id, name, description, entity, action, created_at, updated_at, is_deleted) VALUES ('...', 'your_entity:read', 'Allows to read your_entity entities.', 'your_entity', 'read', NOW(), NOW(), FALSE);
    -- ... and so on for update, delete.
    ```
-   **Usage**: You need to manually execute this SQL script against your database to apply the new privileges. Use your preferred database client or tool.

## Manual Step: Updating `__init__.py` Files

**This is a crucial manual step.** After the generator creates the new entity modules, they are not automatically discoverable by the Python import system or by frameworks like FastAPI and SQLAlchemy until you update the relevant `__init__.py` files.

For each generated module (e.g., `models/your_entity.py`), you need to import it or its key classes into the corresponding package's `__init__.py`.

**Example:**

If you generated an entity named "ProductItem":

1.  **`models/__init__.py`**:
    Add: `from .product_item import ProductItem`
    (Ensure your `models/base.py` which defines `BaseModel` is correctly set up for SQLAlchemy metadata collection if you rely on models being imported for table creation via Alembic).

2.  **`schemas/__init__.py`**:
    You might expose key schemas:
    `from .product_item_schema import ProductItemCreate, ProductItemResponse, ProductItemUpdate`

3.  **`routers/__init__.py`**:
    If you have a main router that includes sub-routers, you'd import and include the new entity's router. For example, if your main FastAPI app or another router aggregates API routers:
    ```python
    # In a central router aggregation point (e.g., routers/__init__.py or main.py)
    # from .product_item import router as product_item_router
    # main_api_router.include_router(product_item_router)
    ```
    The exact way to include routers depends on your project's FastAPI setup. The generated router file (e.g. `routers/product_item.py`) will contain an `APIRouter` instance.

4.  **`services/__init__.py`** (Less common to bulk import, usually imported directly where needed):
    You generally don't need to add service classes to `__init__.py` unless you have a specific pattern for it. They are usually imported directly.

5.  **`repositories/__init__.py`** (Similar to services):
    Repositories are also often imported directly where needed.

**Failure to update `__init__.py` files will typically result in `ModuleNotFoundError` or errors where SQLAlchemy/Alembic cannot find your new models, or FastAPI cannot route to your new endpoints.**

## Troubleshooting

-   **JSON Errors**: Validate your JSON file using a linter or online validator if you encounter parsing errors. Pay close attention to commas, brackets, and quotes.
-   **Template Errors**: If you modify the Jinja2 templates in the `templates/` directory, syntax errors in the templates can cause generation to fail. The error message will usually point to the problematic template file and line.
-   **File Not Found (Templates)**: Ensure the `templates` directory is in the correct location relative to where you run the script, or that the `base_output_path` provided to `generate_entity_files` correctly leads to the project structure where `templates` can be found.
-   **Import Errors After Generation**: This is almost always due to not updating the `__init__.py` files as described above.

This Entity Generator should significantly streamline your development workflow. Remember to review the generated code and adapt it as necessary for any specific complex logic your entity might require.
