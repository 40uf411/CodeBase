import unittest
import json
import os
import shutil
import tempfile
from unittest.mock import patch, mock_open

# Adjust import path based on where the script is run from or PYTHONPATH
# Assuming 'utils' is a sibling of 'tests' or PYTHONPATH is set up.
from utils.entity_generator import (
    to_snake_case,
    to_pascal_case,
    map_sqlalchemy_type,
    map_pydantic_type,
    map_pydantic_default,
    generate_entity_files
)

class TestEntityGeneratorHelpers(unittest.TestCase):

    def test_to_snake_case(self):
        self.assertEqual(to_snake_case("HelloWorld"), "hello_world")
        self.assertEqual(to_snake_case("HelloHTMLWorld"), "hello_html_world")
        self.assertEqual(to_snake_case("Already_Snake_Case"), "already_snake_case")
        self.assertEqual(to_snake_case("ProductItem"), "product_item")

    def test_to_pascal_case(self):
        self.assertEqual(to_pascal_case("hello_world"), "HelloWorld")
        self.assertEqual(to_pascal_case("hello_html_world"), "HelloHtmlWorld")
        self.assertEqual(to_pascal_case("ProductItem"), "ProductItem")
        self.assertEqual(to_pascal_case("project"), "Project")

    def test_map_sqlalchemy_type(self):
        self.assertEqual(map_sqlalchemy_type("string"), "String")
        self.assertEqual(map_sqlalchemy_type("integer"), "Integer")
        self.assertEqual(map_sqlalchemy_type("datetime"), "DateTime")
        self.assertEqual(map_sqlalchemy_type("unknown"), "String") # Test default

    def test_map_pydantic_type(self):
        self.assertEqual(map_pydantic_type("string"), "str")
        self.assertEqual(map_pydantic_type("integer"), "int")
        self.assertEqual(map_pydantic_type("datetime"), "datetime")
        self.assertEqual(map_pydantic_type("unknown"), "str") # Test default

    def test_map_pydantic_default(self):
        self.assertEqual(map_pydantic_default(None), "None")
        self.assertEqual(map_pydantic_default(True), "True")
        self.assertEqual(map_pydantic_default(10), "10")
        self.assertEqual(map_pydantic_default("test"), '"test"')
        self.assertEqual(map_pydantic_default(0.5), "0.5")


class TestEntityGeneration(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory to act as the project root for tests
        self.test_dir = tempfile.mkdtemp()
        self.templates_dir = os.path.join(self.test_dir, "templates")

        # Create dummy template structure (simplified)
        os.makedirs(os.path.join(self.templates_dir, "models"), exist_ok=True)
        os.makedirs(os.path.join(self.templates_dir, "schemas"), exist_ok=True)
        os.makedirs(os.path.join(self.templates_dir, "routers"), exist_ok=True)
        os.makedirs(os.path.join(self.templates_dir, "services"), exist_ok=True)
        os.makedirs(os.path.join(self.templates_dir, "repositories"), exist_ok=True)

        # Create very basic dummy templates for testing generation paths
        with open(os.path.join(self.templates_dir, "models/model.py.j2"), "w") as f:
            f.write("Model: {{ entity_name }}\nSnake: {{ entity_name_snake }}\nDesc: {{ entity_description }}\n{% for prop in properties %}{{prop.name}}:{{prop.type|map_sqlalchemy_type}}\n{% endfor %}{% for rel in relationships %}Rel: {{ rel.name }} to {{ rel.target_entity_pascal }} ({{ rel.type }}) BP: {{rel.back_populates}}{% if rel.type == 'many-to-one' %} FK: {{rel.foreign_key_column}}{% endif %}{% if rel.type == 'many-to-many' %} Assoc: {{ entity_name_snake }}_{{ rel.target_entity_snake }}_association{% endif %}\n{% endfor %}")
        with open(os.path.join(self.templates_dir, "schemas/schema.py.j2"), "w") as f:
            f.write("Schema: {{ entity_name }}\n{% for prop in properties %}{{prop.name}}:{{prop.type|map_pydantic_type}}={{prop.default_value|map_pydantic_default}}\n{% endfor %}")
        with open(os.path.join(self.templates_dir, "routers/router.py.j2"), "w") as f:
            f.write("Router: {{ entity_name_snake }}")
        with open(os.path.join(self.templates_dir, "services/service.py.j2"), "w") as f:
            f.write("Service: {{ entity_name }}")
        with open(os.path.join(self.templates_dir, "repositories/repository.py.j2"), "w") as f:
            f.write("Repository: {{ entity_name }}")

        # Path to the test.json file from the actual project structure
        # This assumes the tests are run from the project root or test.json is accessible
        self.test_json_path = "test.json"
        if not os.path.exists(self.test_json_path):
            # Create a dummy test.json in the temp dir if the real one is not found
            # This is a fallback for isolated testing, but ideally, it uses the real one.
            self.test_json_path = os.path.join(self.test_dir, "test.json")
            with open(self.test_json_path, "w") as f:
                json.dump([{"name": "Dummy", "properties": [{"name": "field1", "type": "string"}]}], f)
                print(f"WARNING: Using dummy test.json for tests: {self.test_json_path}")


    def tearDown(self):
        # Remove the temporary directory after tests
        shutil.rmtree(self.test_dir)

    def test_generate_single_entity_no_relationships(self):
        single_entity_json_string = json.dumps([
            {
                "name": "MyTestEntity",
                "description": "A simple test entity.",
                "properties": [
                    {"name": "id", "type": "uuid", "is_nullable": False, "is_unique": True, "description": "Primary key"},
                    {"name": "name", "type": "string", "is_nullable": False, "description": "Name of the entity"}
                ],
                "relationships": []
            }
        ])

        generate_entity_files(single_entity_json_string, base_output_path=self.test_dir)

        # Check if files are created
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "models/my_test_entity.py")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "schemas/my_test_entity_schema.py")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "routers/my_test_entity.py")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "services/my_test_entity.py")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "repositories/my_test_entity.py")))

        # Check some content (basic check based on dummy templates)
        with open(os.path.join(self.test_dir, "models/my_test_entity.py"), "r") as f:
            content = f.read()
            self.assertIn("Model: MyTestEntity", content)
            self.assertIn("name:String", content)

        # Check SQL privileges file
        sql_file_path = os.path.join(self.test_dir, "generated_privileges.sql")
        self.assertTrue(os.path.exists(sql_file_path))
        with open(sql_file_path, "r") as f:
            sql_content = f.read()
            self.assertIn("my_test_entity:create", sql_content)
            self.assertIn("my_test_entity:read", sql_content)
            self.assertIn("my_test_entity:update", sql_content)
            self.assertIn("my_test_entity:delete", sql_content)
            self.assertEqual(sql_content.count("INSERT INTO privilege"), 4)


    def test_generate_from_test_json_file(self):
        # This test uses the test.json created in the previous plan step
        # Ensure utils/entity_generator.py can find 'templates' relative to base_output_path

        # We need to make sure the 'templates' dir used by the generator is the one in self.test_dir
        # The generator constructs template_dir = os.path.join(base_output_path, "templates")

        with open(self.test_json_path, "r") as f:
            json_string = f.read()

        generate_entity_files(json_string, base_output_path=self.test_dir)

        # Check for Project entity files
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "models/project.py")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "schemas/project_schema.py")))

        # Check for Task entity files
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "models/task.py")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "schemas/task_schema.py")))

        # Check for Tag entity files
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "models/tag.py")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "schemas/tag_schema.py")))

        # Verify some relationship content in generated model (Project and Task)
        with open(os.path.join(self.test_dir, "models/project.py"), "r") as f:
            content = f.read()
            self.assertIn("Rel: tasks to Task (one-to-many) BP: project", content)

        with open(os.path.join(self.test_dir, "models/task.py"), "r") as f:
            content = f.read()
            self.assertIn("Rel: project to Project (many-to-one) BP: tasks FK: project_id", content)
            self.assertIn("Rel: tags to Tag (many-to-many) BP: tasks Assoc: task_tag_association", content)

        # Verify association table name in Tag model
        with open(os.path.join(self.test_dir, "models/tag.py"), "r") as f:
            content = f.read()
            self.assertIn("Rel: tasks to Task (many-to-many) BP: tags Assoc: tag_task_association", content) # Note: entity_name_snake is 'tag', rel.target_entity_snake is 'task'

        # Verify SQL privileges
        sql_file_path = os.path.join(self.test_dir, "generated_privileges.sql")
        self.assertTrue(os.path.exists(sql_file_path))
        with open(sql_file_path, "r") as f:
            sql_content = f.read()
            self.assertIn("project:create", sql_content)
            self.assertIn("task:read", sql_content)
            self.assertIn("tag:delete", sql_content)
            self.assertEqual(sql_content.count("INSERT INTO privilege"), 3 * 4) # 3 entities, 4 actions each

if __name__ == "__main__":
    # This allows running the tests directly
    # Ensure that utils.entity_generator can be imported.
    # May need to adjust PYTHONPATH or run as 'python -m tests.unit.utils.test_entity_generator' from project root.
    unittest.main()
