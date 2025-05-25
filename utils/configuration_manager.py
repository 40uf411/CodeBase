import os
import sys
import json
import argparse
from typing import Dict, List, Optional, Any
import inquirer
from inquirer import errors
from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

class ConfigurationManager:
    """
    Configuration manager for handling JSON and manual configuration.
    
    Features:
    - JSON configuration loading and saving
    - Manual configuration with interactive prompts
    - Configuration validation
    - Configuration visualization
    """
    
    def __init__(self, console: Console):
        """
        Initialize the configuration manager.
        
        Args:
            console: Rich console for output
        """
        self.console = console
        self.config = {}
    
    def load_json_config(self, file_path: str) -> Dict[str, Any]:
        """
        Load configuration from JSON file.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Configuration dictionary
        """
        try:
            with open(file_path, 'r') as f:
                config = json.load(f)
            self.console.print(f"[green]Configuration loaded from {file_path}[/green]")
            self.config = config
            return config
        except Exception as e:
            self.console.print(f"[red]Error loading configuration: {str(e)}[/red]")
            return {}
    
    def save_json_config(self, config: Dict[str, Any], file_path: str) -> bool:
        """
        Save configuration to JSON file.
        
        Args:
            config: Configuration dictionary
            file_path: Path to JSON file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(file_path, 'w') as f:
                json.dump(config, f, indent=2)
            self.console.print(f"[green]Configuration saved to {file_path}[/green]")
            return True
        except Exception as e:
            self.console.print(f"[red]Error saving configuration: {str(e)}[/red]")
            return False
    
    def generate_json_template(self) -> Dict[str, Any]:
        """
        Generate a JSON template for configuration.
        
        Returns:
            Template configuration dictionary
        """
        template = {
            "codebase_config": {
                "project_name": "FastAPI Project",
                "project_dir": "./fastapi_project",
                "database": {
                    "postgres_server": "localhost",
                    "postgres_port": 5432,
                    "postgres_db": "fastapi_db",
                    "postgres_user": "postgres",
                    "postgres_password": "postgres"
                },
                "jwt": {
                    "secret_key": "generate_random_secret_key",
                    "algorithm": "HS256",
                    "access_token_expire_minutes": 30,
                    "refresh_token_expire_days": 7
                },
                "google_oauth": {
                    "enabled": True,
                    "client_id": "",
                    "client_secret": "",
                    "redirect_uri": ""
                },
                "dragonfly": {
                    "host": "localhost",
                    "port": 6379,
                    "db": 0,
                    "password": ""
                },
                "kafka": {
                    "bootstrap_servers": "localhost:9092"
                }
            },
            "models_config": [
                {
                    "name": "Sample",
                    "fields": [
                        {
                            "name": "name",
                            "type": "string",
                            "nullable": False,
                            "unique": True,
                            "index": True
                        },
                        {
                            "name": "description",
                            "type": "text",
                            "nullable": True
                        },
                        {
                            "name": "is_active",
                            "type": "boolean",
                            "nullable": False,
                            "default": True
                        }
                    ],
                    "relationships": [],
                    "cache": {
                        "enabled": True,
                        "duration": 60
                    }
                }
            ]
        }
        
        return template
    
    def display_config(self, config: Dict[str, Any]):
        """
        Display configuration in a visually appealing format.
        
        Args:
            config: Configuration dictionary
        """
        self.console.print(Panel(Text("Configuration", style="bold cyan")))
        
        # Display codebase config
        if "codebase_config" in config:
            codebase_table = Table(title="Codebase Configuration")
            codebase_table.add_column("Setting", style="cyan")
            codebase_table.add_column("Value", style="green")
            
            codebase_config = config["codebase_config"]
            
            # Add simple key-value pairs
            for key, value in codebase_config.items():
                if not isinstance(value, dict):
                    codebase_table.add_row(key, str(value))
            
            # Add nested configurations
            for key, value in codebase_config.items():
                if isinstance(value, dict):
                    nested_table = Table(title=f"{key} Configuration")
                    nested_table.add_column("Setting", style="cyan")
                    nested_table.add_column("Value", style="green")
                    
                    for nested_key, nested_value in value.items():
                        nested_table.add_row(nested_key, str(nested_value))
                    
                    self.console.print(nested_table)
            
            self.console.print(codebase_table)
        
        # Display models config
        if "models_config" in config:
            for i, model in enumerate(config["models_config"]):
                model_table = Table(title=f"Model: {model['name']}")
                model_table.add_column("Setting", style="cyan")
                model_table.add_column("Value", style="green")
                
                # Add simple key-value pairs
                for key, value in model.items():
                    if not isinstance(value, (dict, list)):
                        model_table.add_row(key, str(value))
                
                self.console.print(model_table)
                
                # Display fields
                if "fields" in model:
                    fields_table = Table(title=f"Fields for {model['name']}")
                    fields_table.add_column("Name", style="cyan")
                    fields_table.add_column("Type", style="green")
                    fields_table.add_column("Nullable", style="yellow")
                    fields_table.add_column("Unique", style="magenta")
                    fields_table.add_column("Index", style="blue")
                    
                    for field in model["fields"]:
                        fields_table.add_row(
                            field["name"],
                            field["type"],
                            str(field.get("nullable", True)),
                            str(field.get("unique", False)),
                            str(field.get("index", False))
                        )
                    
                    self.console.print(fields_table)
                
                # Display relationships
                if "relationships" in model and model["relationships"]:
                    rel_table = Table(title=f"Relationships for {model['name']}")
                    rel_table.add_column("Type", style="cyan")
                    rel_table.add_column("Target", style="green")
                    rel_table.add_column("Field Name", style="yellow")
                    
                    for rel in model["relationships"]:
                        rel_table.add_row(
                            rel["type"],
                            rel["target"],
                            rel["field_name"]
                        )
                    
                    self.console.print(rel_table)
                
                # Display cache config
                if "cache" in model:
                    cache_table = Table(title=f"Cache Configuration for {model['name']}")
                    cache_table.add_column("Setting", style="cyan")
                    cache_table.add_column("Value", style="green")
                    
                    for key, value in model["cache"].items():
                        cache_table.add_row(key, str(value))
                    
                    self.console.print(cache_table)
    
    def prompt_for_config(self) -> Dict[str, Any]:
        """
        Prompt user for configuration.
        
        Returns:
            Configuration dictionary
        """
        config = {"codebase_config": {}, "models_config": []}
        
        # Project configuration
        self.console.print(Panel(Text("Project Configuration", style="bold cyan")))
        
        questions = [
            inquirer.Text('project_name', message="Project name", default="FastAPI Project"),
            inquirer.Text('project_dir', message="Project directory", default="./fastapi_project"),
        ]
        
        answers = inquirer.prompt(questions)
        config["codebase_config"]["project_name"] = answers["project_name"]
        config["codebase_config"]["project_dir"] = answers["project_dir"]
        
        # Database configuration
        self.console.print(Panel(Text("Database Configuration", style="bold cyan")))
        
        db_questions = [
            inquirer.Text('postgres_server', message="PostgreSQL server", default="localhost"),
            inquirer.Text('postgres_port', message="PostgreSQL port", default="5432"),
            inquirer.Text('postgres_db', message="PostgreSQL database name", default=answers["project_name"].lower().replace(" ", "_")),
            inquirer.Text('postgres_user', message="PostgreSQL username", default="postgres"),
            inquirer.Password('postgres_password', message="PostgreSQL password", default="postgres"),
        ]
        
        db_answers = inquirer.prompt(db_questions)
        config["codebase_config"]["database"] = {
            "postgres_server": db_answers["postgres_server"],
            "postgres_port": int(db_answers["postgres_port"]),
            "postgres_db": db_answers["postgres_db"],
            "postgres_user": db_answers["postgres_user"],
            "postgres_password": db_answers["postgres_password"],
        }
        
        # Google OAuth configuration
        self.console.print(Panel(Text("Google OAuth Configuration", style="bold cyan")))
        
        oauth_questions = [
            inquirer.Confirm('enabled', message="Enable Google OAuth?", default=True),
        ]
        
        oauth_answers = inquirer.prompt(oauth_questions)
        
        if oauth_answers["enabled"]:
            oauth_details = [
                inquirer.Text('client_id', message="Google Client ID"),
                inquirer.Password('client_secret', message="Google Client Secret"),
                inquirer.Text('redirect_uri', message="Google Redirect URI", default="http://localhost:8000/auth/google/auth"),
            ]
            
            oauth_details_answers = inquirer.prompt(oauth_details)
            
            config["codebase_config"]["google_oauth"] = {
                "enabled": True,
                "client_id": oauth_details_answers["client_id"],
                "client_secret": oauth_details_answers["client_secret"],
                "redirect_uri": oauth_details_answers["redirect_uri"],
            }
        else:
            config["codebase_config"]["google_oauth"] = {
                "enabled": False,
                "client_id": "",
                "client_secret": "",
                "redirect_uri": "",
            }
        
        # JWT configuration
        config["codebase_config"]["jwt"] = {
            "algorithm": "HS256",
            "access_token_expire_minutes": 30,
            "refresh_token_expire_days": 7,
        }
        
        # DragonFly configuration
        self.console.print(Panel(Text("DragonFly Configuration", style="bold cyan")))
        
        dragonfly_questions = [
            inquirer.Text('host', message="DragonFly host", default="localhost"),
            inquirer.Text('port', message="DragonFly port", default="6379"),
            inquirer.Text('db', message="DragonFly database", default="0"),
            inquirer.Password('password', message="DragonFly password (optional)"),
        ]
        
        dragonfly_answers = inquirer.prompt(dragonfly_questions)
        config["codebase_config"]["dragonfly"] = {
            "host": dragonfly_answers["host"],
            "port": int(dragonfly_answers["port"]),
            "db": int(dragonfly_answers["db"]),
            "password": dragonfly_answers["password"],
        }
        
        # Kafka configuration
        self.console.print(Panel(Text("Kafka Configuration", style="bold cyan")))
        
        kafka_questions = [
            inquirer.Text('bootstrap_servers', message="Kafka bootstrap servers", default="localhost:9092"),
        ]
        
        kafka_answers = inquirer.prompt(kafka_questions)
        config["codebase_config"]["kafka"] = {
            "bootstrap_servers": kafka_answers["bootstrap_servers"],
        }
        
        # Model configuration
        self.console.print(Panel(Text("Model Configuration", style="bold cyan")))
        
        while True:
            model_questions = [
                inquirer.Text('name', message="Model name (leave empty to finish)"),
            ]
            
            model_answers = inquirer.prompt(model_questions)
            
            if not model_answers["name"]:
                break
            
            model_config = {"name": model_answers["name"], "fields": [], "relationships": []}
            
            # Fields configuration
            self.console.print(f"[cyan]Configuring fields for {model_answers['name']}[/cyan]")
            
            while True:
                field_questions = [
                    inquirer.Text('name', message="Field name (leave empty to finish)"),
                ]
                
                field_answers = inquirer.prompt(field_questions)
                
                if not field_answers["name"]:
                    break
                
                field_type_question = [
                    inquirer.List('type',
                                 message="Field type",
                                 choices=["string", "integer", "float", "boolean", "text", "date", "datetime", "uuid"],
                                 default="string"),
                ]
                
                field_type_answer = inquirer.prompt(field_type_question)
                
                field_options = [
                    inquirer.Confirm('nullable', message="Is this field nullable?", default=True),
                    inquirer.Confirm('unique', message="Is this field unique?", default=False),
                    inquirer.Confirm('index', message="Create an index for this field?", default=False),
                ]
                
                field_options_answers = inquirer.prompt(field_options)
                
                field = {
                    "name": field_answers["name"],
                    "type": field_type_answer["type"],
                    "nullable": field_options_answers["nullable"],
                    "unique": field_options_answers["unique"],
                    "index": field_options_answers["index"],
                }
                
                model_config["fields"].append(field)
            
            # Relationships configuration
            self.console.print(f"[cyan]Configuring relationships for {model_answers['name']}[/cyan]")
            
            while True:
                rel_questions = [
                    inquirer.Confirm('add_relationship', message="Add a relationship?", default=False),
                ]
                
                rel_answers = inquirer.prompt(rel_questions)
                
                if not rel_answers["add_relationship"]:
                    break
                
                rel_details = [
                    inquirer.List('type',
                                 message="Relationship type",
                                 choices=["one-to-many", "many-to-one", "many-to-many", "one-to-one"],
                                 default="many-to-one"),
                    inquirer.Text('target', message="Target model name"),
                    inquirer.Text('field_name', message="Field name for this relationship"),
                ]
                
                rel_details_answers = inquirer.prompt(rel_details)
                
                relationship = {
                    "type": rel_details_answers["type"],
                    "target": rel_details_answers["target"],
                    "field_name": rel_details_answers["field_name"],
                }
                
                model_config["relationships"].append(relationship)
            
            # Cache configuration
            self.console.print(f"[cyan]Configuring cache for {model_answers['name']}[/cyan]")
            
            cache_questions = [
                inquirer.Confirm('enabled', message="Enable caching for this model?", default=True),
            ]
            
            cache_answers = inquirer.prompt(cache_questions)
            
            if cache_answers["enabled"]:
                cache_duration_question = [
                    inquirer.List('duration',
                                 message="Cache duration",
                                 choices=["30 seconds", "1 minute", "5 minutes", "15 minutes", "30 minutes", "1 hour", "Custom"],
                                 default="1 minute"),
                ]
                
                cache_duration_answer = inquirer.prompt(cache_duration_question)
                
                duration_map = {
                    "30 seconds": 30,
                    "1 minute": 60,
                    "5 minutes": 300,
                    "15 minutes": 900,
                    "30 minutes": 1800,
                    "1 hour": 3600,
                }
                
                if cache_duration_answer["duration"] == "Custom":
                    custom_duration_question = [
                        inquirer.Text('seconds', message="Custom duration in seconds", default="60"),
                    ]
                    
                    custom_duration_answer = inquirer.prompt(custom_duration_question)
                    duration = int(custom_duration_answer["seconds"])
                else:
                    duration = duration_map[cache_duration_answer["duration"]]
                
                model_config["cache"] = {
                    "enabled": True,
                    "duration": duration,
                }
            else:
                model_config["cache"] = {
                    "enabled": False,
                    "duration": 0,
                }
            
            config["models_config"].append(model_config)
        
        return config
    
    def edit_config_item(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Allow user to edit a single configuration item.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Updated configuration dictionary
        """
        # Display current configuration
        self.display_config(config)
        
        # Choose what to edit
        edit_choices = [
            "Codebase Configuration",
            "Model Configuration",
            "Cancel"
        ]
        
        edit_question = [
            inquirer.List('choice',
                         message="What would you like to edit?",
                         choices=edit_choices),
        ]
        
        edit_answer = inquirer.prompt(edit_question)
        
        if edit_answer["choice"] == "Cancel":
            return config
        
        if edit_answer["choice"] == "Codebase Configuration":
            # Choose which section to edit
            codebase_sections = list(config["codebase_config"].keys())
            
            section_question = [
                inquirer.List('section',
                             message="Which section would you like to edit?",
                             choices=codebase_sections + ["Cancel"]),
            ]
            
            section_answer = inquirer.prompt(section_question)
            
            if section_answer["section"] == "Cancel":
                return config
            
            section = section_answer["section"]
            
            if isinstance(config["codebase_config"][section], dict):
                # Edit a nested section
                keys = list(config["codebase_config"][section].keys())
                
                key_question = [
                    inquirer.List('key',
                                 message=f"Which {section} setting would you like to edit?",
                                 choices=keys + ["Cancel"]),
                ]
                
                key_answer = inquirer.prompt(key_question)
                
                if key_answer["key"] == "Cancel":
                    return config
                
                key = key_answer["key"]
                current_value = config["codebase_config"][section][key]
                
                # Prompt for new value
                if isinstance(current_value, bool):
                    value_question = [
                        inquirer.Confirm('value', message=f"New value for {key}", default=current_value),
                    ]
                elif isinstance(current_value, int):
                    value_question = [
                        inquirer.Text('value', message=f"New value for {key}", default=str(current_value)),
                    ]
                else:
                    value_question = [
                        inquirer.Text('value', message=f"New value for {key}", default=str(current_value)),
                    ]
                
                value_answer = inquirer.prompt(value_question)
                
                # Update config
                if isinstance(current_value, int):
                    config["codebase_config"][section][key] = int(value_answer["value"])
                elif isinstance(current_value, bool):
                    config["codebase_config"][section][key] = value_answer["value"]
                else:
                    config["codebase_config"][section][key] = value_answer["value"]
            else:
                # Edit a simple value
                current_value = config["codebase_config"][section]
                
                # Prompt for new value
                if isinstance(current_value, bool):
                    value_question = [
                        inquirer.Confirm('value', message=f"New value for {section}", default=current_value),
                    ]
                elif isinstance(current_value, int):
                    value_question = [
                        inquirer.Text('value', message=f"New value for {section}", default=str(current_value)),
                    ]
                else:
                    value_question = [
                        inquirer.Text('value', message=f"New value for {section}", default=str(current_value)),
                    ]
                
                value_answer = inquirer.prompt(value_question)
                
                # Update config
                if isinstance(current_value, int):
                    config["codebase_config"][section] = int(value_answer["value"])
                elif isinstance(current_value, bool):
                    config["codebase_config"][section] = value_answer["value"]
                else:
                    config["codebase_config"][section] = value_answer["value"]
        
        elif edit_answer["choice"] == "Model Configuration":
            # Choose which model to edit
            if not config["models_config"]:
                self.console.print("[yellow]No models to edit[/yellow]")
                return config
            
            model_names = [model["name"] for model in config["models_config"]]
            
            model_question = [
                inquirer.List('model',
                             message="Which model would you like to edit?",
                             choices=model_names + ["Cancel"]),
            ]
            
            model_answer = inquirer.prompt(model_question)
            
            if model_answer["model"] == "Cancel":
                return config
            
            model_name = model_answer["model"]
            model_index = model_names.index(model_name)
            
            # Choose what to edit in the model
            model_edit_choices = [
                "Model Name",
                "Fields",
                "Relationships",
                "Cache Configuration",
                "Cancel"
            ]
            
            model_edit_question = [
                inquirer.List('choice',
                             message=f"What would you like to edit in {model_name}?",
                             choices=model_edit_choices),
            ]
            
            model_edit_answer = inquirer.prompt(model_edit_question)
            
            if model_edit_answer["choice"] == "Cancel":
                return config
            
            if model_edit_answer["choice"] == "Model Name":
                # Edit model name
                name_question = [
                    inquirer.Text('name', message="New model name", default=model_name),
                ]
                
                name_answer = inquirer.prompt(name_question)
                
                config["models_config"][model_index]["name"] = name_answer["name"]
            
            elif model_edit_answer["choice"] == "Fields":
                # Edit fields
                if not config["models_config"][model_index]["fields"]:
                    self.console.print("[yellow]No fields to edit. Add a new field.[/yellow]")
                    
                    # Add a new field
                    field_questions = [
                        inquirer.Text('name', message="Field name"),
                    ]
                    
                    field_answers = inquirer.prompt(field_questions)
                    
                    field_type_question = [
                        inquirer.List('type',
                                     message="Field type",
                                     choices=["string", "integer", "float", "boolean", "text", "date", "datetime", "uuid"],
                                     default="string"),
                    ]
                    
                    field_type_answer = inquirer.prompt(field_type_question)
                    
                    field_options = [
                        inquirer.Confirm('nullable', message="Is this field nullable?", default=True),
                        inquirer.Confirm('unique', message="Is this field unique?", default=False),
                        inquirer.Confirm('index', message="Create an index for this field?", default=False),
                    ]
                    
                    field_options_answers = inquirer.prompt(field_options)
                    
                    field = {
                        "name": field_answers["name"],
                        "type": field_type_answer["type"],
                        "nullable": field_options_answers["nullable"],
                        "unique": field_options_answers["unique"],
                        "index": field_options_answers["index"],
                    }
                    
                    config["models_config"][model_index]["fields"].append(field)
                else:
                    # Choose a field to edit or add a new one
                    field_names = [field["name"] for field in config["models_config"][model_index]["fields"]]
                    
                    field_question = [
                        inquirer.List('field',
                                     message="Which field would you like to edit?",
                                     choices=field_names + ["Add New Field", "Cancel"]),
                    ]
                    
                    field_answer = inquirer.prompt(field_question)
                    
                    if field_answer["field"] == "Cancel":
                        return config
                    
                    if field_answer["field"] == "Add New Field":
                        # Add a new field
                        field_questions = [
                            inquirer.Text('name', message="Field name"),
                        ]
                        
                        field_answers = inquirer.prompt(field_questions)
                        
                        field_type_question = [
                            inquirer.List('type',
                                         message="Field type",
                                         choices=["string", "integer", "float", "boolean", "text", "date", "datetime", "uuid"],
                                         default="string"),
                        ]
                        
                        field_type_answer = inquirer.prompt(field_type_question)
                        
                        field_options = [
                            inquirer.Confirm('nullable', message="Is this field nullable?", default=True),
                            inquirer.Confirm('unique', message="Is this field unique?", default=False),
                            inquirer.Confirm('index', message="Create an index for this field?", default=False),
                        ]
                        
                        field_options_answers = inquirer.prompt(field_options)
                        
                        field = {
                            "name": field_answers["name"],
                            "type": field_type_answer["type"],
                            "nullable": field_options_answers["nullable"],
                            "unique": field_options_answers["unique"],
                            "index": field_options_answers["index"],
                        }
                        
                        config["models_config"][model_index]["fields"].append(field)
                    else:
                        # Edit an existing field
                        field_name = field_answer["field"]
                        field_index = field_names.index(field_name)
                        
                        # Choose what to edit in the field
                        field_edit_choices = [
                            "Field Name",
                            "Field Type",
                            "Field Options",
                            "Delete Field",
                            "Cancel"
                        ]
                        
                        field_edit_question = [
                            inquirer.List('choice',
                                         message=f"What would you like to edit in {field_name}?",
                                         choices=field_edit_choices),
                        ]
                        
                        field_edit_answer = inquirer.prompt(field_edit_question)
                        
                        if field_edit_answer["choice"] == "Cancel":
                            return config
                        
                        if field_edit_answer["choice"] == "Field Name":
                            # Edit field name
                            name_question = [
                                inquirer.Text('name', message="New field name", default=field_name),
                            ]
                            
                            name_answer = inquirer.prompt(name_question)
                            
                            config["models_config"][model_index]["fields"][field_index]["name"] = name_answer["name"]
                        
                        elif field_edit_answer["choice"] == "Field Type":
                            # Edit field type
                            current_type = config["models_config"][model_index]["fields"][field_index]["type"]
                            
                            type_question = [
                                inquirer.List('type',
                                             message="New field type",
                                             choices=["string", "integer", "float", "boolean", "text", "date", "datetime", "uuid"],
                                             default=current_type),
                            ]
                            
                            type_answer = inquirer.prompt(type_question)
                            
                            config["models_config"][model_index]["fields"][field_index]["type"] = type_answer["type"]
                        
                        elif field_edit_answer["choice"] == "Field Options":
                            # Edit field options
                            current_options = config["models_config"][model_index]["fields"][field_index]
                            
                            options_questions = [
                                inquirer.Confirm('nullable', message="Is this field nullable?", default=current_options.get("nullable", True)),
                                inquirer.Confirm('unique', message="Is this field unique?", default=current_options.get("unique", False)),
                                inquirer.Confirm('index', message="Create an index for this field?", default=current_options.get("index", False)),
                            ]
                            
                            options_answers = inquirer.prompt(options_questions)
                            
                            config["models_config"][model_index]["fields"][field_index]["nullable"] = options_answers["nullable"]
                            config["models_config"][model_index]["fields"][field_index]["unique"] = options_answers["unique"]
                            config["models_config"][model_index]["fields"][field_index]["index"] = options_answers["index"]
                        
                        elif field_edit_answer["choice"] == "Delete Field":
                            # Delete field
                            confirm_question = [
                                inquirer.Confirm('confirm', message=f"Are you sure you want to delete the field {field_name}?", default=False),
                            ]
                            
                            confirm_answer = inquirer.prompt(confirm_question)
                            
                            if confirm_answer["confirm"]:
                                del config["models_config"][model_index]["fields"][field_index]
            
            elif model_edit_answer["choice"] == "Relationships":
                # Edit relationships
                if not config["models_config"][model_index]["relationships"]:
                    self.console.print("[yellow]No relationships to edit. Add a new relationship.[/yellow]")
                    
                    # Add a new relationship
                    rel_details = [
                        inquirer.List('type',
                                     message="Relationship type",
                                     choices=["one-to-many", "many-to-one", "many-to-many", "one-to-one"],
                                     default="many-to-one"),
                        inquirer.Text('target', message="Target model name"),
                        inquirer.Text('field_name', message="Field name for this relationship"),
                    ]
                    
                    rel_details_answers = inquirer.prompt(rel_details)
                    
                    relationship = {
                        "type": rel_details_answers["type"],
                        "target": rel_details_answers["target"],
                        "field_name": rel_details_answers["field_name"],
                    }
                    
                    config["models_config"][model_index]["relationships"].append(relationship)
                else:
                    # Choose a relationship to edit or add a new one
                    rel_names = [f"{rel['type']} to {rel['target']}" for rel in config["models_config"][model_index]["relationships"]]
                    
                    rel_question = [
                        inquirer.List('relationship',
                                     message="Which relationship would you like to edit?",
                                     choices=rel_names + ["Add New Relationship", "Cancel"]),
                    ]
                    
                    rel_answer = inquirer.prompt(rel_question)
                    
                    if rel_answer["relationship"] == "Cancel":
                        return config
                    
                    if rel_answer["relationship"] == "Add New Relationship":
                        # Add a new relationship
                        rel_details = [
                            inquirer.List('type',
                                         message="Relationship type",
                                         choices=["one-to-many", "many-to-one", "many-to-many", "one-to-one"],
                                         default="many-to-one"),
                            inquirer.Text('target', message="Target model name"),
                            inquirer.Text('field_name', message="Field name for this relationship"),
                        ]
                        
                        rel_details_answers = inquirer.prompt(rel_details)
                        
                        relationship = {
                            "type": rel_details_answers["type"],
                            "target": rel_details_answers["target"],
                            "field_name": rel_details_answers["field_name"],
                        }
                        
                        config["models_config"][model_index]["relationships"].append(relationship)
                    else:
                        # Edit an existing relationship
                        rel_index = rel_names.index(rel_answer["relationship"])
                        
                        # Choose what to edit in the relationship
                        rel_edit_choices = [
                            "Relationship Type",
                            "Target Model",
                            "Field Name",
                            "Delete Relationship",
                            "Cancel"
                        ]
                        
                        rel_edit_question = [
                            inquirer.List('choice',
                                         message=f"What would you like to edit in this relationship?",
                                         choices=rel_edit_choices),
                        ]
                        
                        rel_edit_answer = inquirer.prompt(rel_edit_question)
                        
                        if rel_edit_answer["choice"] == "Cancel":
                            return config
                        
                        if rel_edit_answer["choice"] == "Relationship Type":
                            # Edit relationship type
                            current_type = config["models_config"][model_index]["relationships"][rel_index]["type"]
                            
                            type_question = [
                                inquirer.List('type',
                                             message="New relationship type",
                                             choices=["one-to-many", "many-to-one", "many-to-many", "one-to-one"],
                                             default=current_type),
                            ]
                            
                            type_answer = inquirer.prompt(type_question)
                            
                            config["models_config"][model_index]["relationships"][rel_index]["type"] = type_answer["type"]
                        
                        elif rel_edit_answer["choice"] == "Target Model":
                            # Edit target model
                            current_target = config["models_config"][model_index]["relationships"][rel_index]["target"]
                            
                            target_question = [
                                inquirer.Text('target', message="New target model name", default=current_target),
                            ]
                            
                            target_answer = inquirer.prompt(target_question)
                            
                            config["models_config"][model_index]["relationships"][rel_index]["target"] = target_answer["target"]
                        
                        elif rel_edit_answer["choice"] == "Field Name":
                            # Edit field name
                            current_field_name = config["models_config"][model_index]["relationships"][rel_index]["field_name"]
                            
                            field_name_question = [
                                inquirer.Text('field_name', message="New field name for this relationship", default=current_field_name),
                            ]
                            
                            field_name_answer = inquirer.prompt(field_name_question)
                            
                            config["models_config"][model_index]["relationships"][rel_index]["field_name"] = field_name_answer["field_name"]
                        
                        elif rel_edit_answer["choice"] == "Delete Relationship":
                            # Delete relationship
                            confirm_question = [
                                inquirer.Confirm('confirm', message=f"Are you sure you want to delete this relationship?", default=False),
                            ]
                            
                            confirm_answer = inquirer.prompt(confirm_question)
                            
                            if confirm_answer["confirm"]:
                                del config["models_config"][model_index]["relationships"][rel_index]
            
            elif model_edit_answer["choice"] == "Cache Configuration":
                # Edit cache configuration
                current_cache = config["models_config"][model_index].get("cache", {"enabled": False, "duration": 0})
                
                cache_questions = [
                    inquirer.Confirm('enabled', message="Enable caching for this model?", default=current_cache.get("enabled", False)),
                ]
                
                cache_answers = inquirer.prompt(cache_questions)
                
                if cache_answers["enabled"]:
                    current_duration = current_cache.get("duration", 60)
                    
                    # Map duration to choice
                    duration_map = {
                        30: "30 seconds",
                        60: "1 minute",
                        300: "5 minutes",
                        900: "15 minutes",
                        1800: "30 minutes",
                        3600: "1 hour",
                    }
                    
                    default_choice = duration_map.get(current_duration, "Custom")
                    
                    cache_duration_question = [
                        inquirer.List('duration',
                                     message="Cache duration",
                                     choices=["30 seconds", "1 minute", "5 minutes", "15 minutes", "30 minutes", "1 hour", "Custom"],
                                     default=default_choice),
                    ]
                    
                    cache_duration_answer = inquirer.prompt(cache_duration_question)
                    
                    reverse_duration_map = {
                        "30 seconds": 30,
                        "1 minute": 60,
                        "5 minutes": 300,
                        "15 minutes": 900,
                        "30 minutes": 1800,
                        "1 hour": 3600,
                    }
                    
                    if cache_duration_answer["duration"] == "Custom":
                        custom_duration_question = [
                            inquirer.Text('seconds', message="Custom duration in seconds", default=str(current_duration)),
                        ]
                        
                        custom_duration_answer = inquirer.prompt(custom_duration_question)
                        duration = int(custom_duration_answer["seconds"])
                    else:
                        duration = reverse_duration_map[cache_duration_answer["duration"]]
                    
                    config["models_config"][model_index]["cache"] = {
                        "enabled": True,
                        "duration": duration,
                    }
                else:
                    config["models_config"][model_index]["cache"] = {
                        "enabled": False,
                        "duration": 0,
                    }
        
        self.console.print("[green]Configuration updated successfully[/green]")
        return config
