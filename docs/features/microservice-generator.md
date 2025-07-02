# Microservice Generator

The Microservice Generator is a utility script designed to quickly scaffold a new microservice within your project. It uses predefined templates to create a standard directory structure and essential files for a new service.

## Overview

The generator helps maintain consistency across your microservices and reduces the boilerplate setup required for each new service. It creates a FastAPI-based service by default, complete with a Dockerfile, requirements file, and example environment configuration.

## How to Use

The script `utils/microservice_generator.py` is used to generate new microservices.

### Prerequisites

- Ensure you have Python installed.
- Jinja2 is required for templating (`pip install Jinja2` - this should already be in the project's `requirements.txt`).

### Running the Generator

You can run the generator script from the root of your project directory:

```bash
python -m utils.microservice_generator
```
When run directly like this, the script will execute its `if __name__ == "__main__":` block, which typically generates a predefined example service (e.g., "Test Example Service") for demonstration or testing purposes.

To generate a custom microservice, you would typically import and use the `generate_microservice` function within another Python script or an interactive Python session.

**Example Python Usage:**

```python
from utils.microservice_generator import generate_microservice

# Define the name for your new service
service_name = "Order Processing Service"

# Specify the base output path (usually the project root)
# The generator will create a 'microservices/' directory here if it doesn't exist,
# and then 'microservices/<service_name_snake_case>/'
project_root_path = "."

try:
    generate_microservice(service_name, base_output_path=project_root_path)
    print(f"Microservice '{service_name}' generated successfully!")
except Exception as e:
    print(f"An error occurred: {e}")
```

This will create a new service in the `microservices/order_processing_service/` directory.

### Generated Structure

A typical generated microservice (`microservices/<your_service_name_snake_case>/`) will have the following structure:

```
your_service_name_snake_case/
├── .env.example        # Example environment variables
├── Dockerfile          # Docker configuration for the service
├── main.py             # Main FastAPI application
├── README.md           # Basic README for the service
└── requirements.txt    # Python dependencies
```

### Templates

The generator uses templates located in `templates/microservice/`. You can customize these templates if you need to change the default structure or content of generated services. The following variables are available in the templates:

-   `{{ service_name }}`: The PascalCase version of the service name (e.g., "OrderProcessingService").
-   `{{ service_name_pascal }}`: Same as `service_name`.
-   `{{ service_name_snake }}`: The snake_case version of the service name (e.g., "order_processing_service").
-   `{{ service_folder_name }}`: The snake_case folder name, same as `service_name_snake`.

## Customization

-   **Templates:** Modify files in `templates/microservice/` to change the generated output.
-   **Generator Script:** For more advanced changes to the generation logic, you can modify `utils/microservice_generator.py`.

Remember to add any new, common dependencies to `templates/microservice/requirements.txt.j2` if you want them included in all future generated services.
