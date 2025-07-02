import os
import re
import shutil
from jinja2 import Environment, FileSystemLoader

# Helper function to convert service_name to snake_case for folder names
def to_snake_case(name: str) -> str:
    if not name:
        return ""
    # Replace spaces and hyphens with underscores
    name = name.replace(" ", "_").replace("-", "_")
    # Add an underscore before an uppercase letter if it's preceded by a lowercase letter or digit
    name = re.sub(r'(?<=[a-z0-9])(?=[A-Z])', r'_', name)
    # Add an underscore before an uppercase letter if it's preceded by another uppercase letter
    # and followed by a lowercase letter
    name = re.sub(r'(?<=[A-Z])(?=[A-Z][a-z])', r'_', name)
    return name.lower().replace('__', '_')

# Helper function to convert service_name to PascalCase for class/app names
def to_pascal_case(name: str) -> str:
    if not name:
        return ""
    # Handle cases like "user-service" or "User Service"
    name = name.replace("-", " ").replace("_", " ")
    return "".join(word.capitalize() for word in name.split())

def generate_microservice(service_name: str, base_output_path: str = "."):
    '''
    Generates a new microservice structure.

    Args:
        service_name (str): The name of the microservice (e.g., "Order Service", "user-service").
        base_output_path (str): The base path where the 'microservices' directory exists or will be created.
                                 Defaults to the current directory.
    '''
    if not service_name:
        print("Error: Service name cannot be empty.")
        return

    service_name_pascal = to_pascal_case(service_name)
    service_name_snake = to_snake_case(service_name)

    # Determine project root dynamically to find templates
    # Assumes this script is in project_root/utils/
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir) # This should be the project root

    template_dir = os.path.join(project_root, "templates", "microservice")
    output_dir_base = os.path.join(base_output_path, "microservices")
    service_output_dir = os.path.join(output_dir_base, service_name_snake)

    if not os.path.isdir(template_dir):
        print(f"Error: Templates directory not found at {template_dir}")
        print("Please ensure the microservice templates are in 'project_root/templates/microservice/'")
        return

    if os.path.exists(service_output_dir):
        print(f"Error: Service directory {service_output_dir} already exists.")
        return

    try:
        os.makedirs(service_output_dir, exist_ok=True)
        print(f"Created directory: {service_output_dir}")
    except OSError as e:
        print(f"Error creating directory {service_output_dir}: {e}")
        return

    env = Environment(loader=FileSystemLoader(template_dir))
    env.filters['to_snake_case'] = to_snake_case
    env.filters['to_pascal_case'] = to_pascal_case

    context = {
        "service_name": service_name_pascal, # For display names, class names if needed
        "service_name_pascal": service_name_pascal, # Explicitly PascalCase
        "service_name_snake": service_name_snake,   # For file names, variable names
        "service_folder_name": service_name_snake,  # For README paths etc.
    }

    template_files = [
        "main.py.j2",
        "Dockerfile.j2",
        "requirements.txt.j2",
        ".env.example.j2",
        "README.md.j2",
    ]

    for template_file_j2 in template_files:
        try:
            template = env.get_template(template_file_j2)
            rendered_content = template.render(context)

            # Remove .j2 extension for the output file
            output_filename = template_file_j2[:-3] if template_file_j2.endswith(".j2") else template_file_j2

            output_path = os.path.join(service_output_dir, output_filename)

            with open(output_path, "w") as f:
                f.write(rendered_content)
            print(f"Generated: {output_path}")

        except Exception as e:
            print(f"Error generating {template_file_j2} for {service_name_pascal}: {e}")
            # Optional: clean up created directory if a file fails
            # shutil.rmtree(service_output_dir)
            # print(f"Cleaned up directory {service_output_dir} due to error.")
            return

    print(f"Successfully generated microservice '{service_name_pascal}' in '{service_output_dir}'")

if __name__ == "__main__":
    print("Starting microservice generator...")

    # Example usage:
    # Ensure the script is run from the project root or adjust path for 'base_output_path'
    # For this example, we assume the 'microservices' folder should be in the project root.

    # To run this example directly, you might need to be in the 'utils' directory
    # or adjust Python's path to find this module.
    # A common way to run from project root: python -m utils.microservice_generator

    # Determine project root for example usage (assuming utils/microservice_generator.py structure)
    example_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Clean up previous example service if it exists, for idempotency of the example
    example_service_name = "Test Example Service"
    example_service_snake = to_snake_case(example_service_name)
    example_service_dir = os.path.join(example_project_root, "microservices", example_service_snake)

    if os.path.exists(example_service_dir):
        print(f"Cleaning up previous example service: {example_service_dir}")
        shutil.rmtree(example_service_dir)

    print(f"Attempting to generate an example service: '{example_service_name}'")
    print(f"Expected output directory for example: {example_service_dir}")

    # Ensure microservices directory exists for the example
    os.makedirs(os.path.join(example_project_root, "microservices"), exist_ok=True)

    generate_microservice(example_service_name, base_output_path=example_project_root)

    print("\n--- Example Generation Complete ---")
    print(f"Check the '{example_service_dir}' directory.")
    print("To generate another service, you can call the function like:")
    print("from utils.microservice_generator import generate_microservice")
    print("generate_microservice('My New Awesome Service', base_output_path='.')")
