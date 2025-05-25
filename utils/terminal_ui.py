import os
import sys
import json
from typing import Dict, List, Optional, Any
import colorama
from colorama import Fore, Style
import pyfiglet

# Initialize colorama
colorama.init()

class TerminalUI:
    """
    Terminal UI for improved user experience.
    
    Features:
    - Terminal artwork
    - Colored output
    - Interactive prompts
    - Configuration visualization
    """
    
    def __init__(self):
        """Initialize the Terminal UI."""
        self.config = {}
    
    def display_welcome(self):
        """Display welcome message with ASCII art."""
        # Clear screen
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Display ASCII art
        ascii_art = pyfiglet.figlet_format("FastAPI Generator", font="isometric2")
        print(f"{Fore.CYAN}{ascii_art}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}Welcome to the FastAPI Codebase Generator!{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}A powerful tool to generate FastAPI projects with DDD architecture.{Style.RESET_ALL}")
        print("\n" + "=" * 80 + "\n")
    
    def display_section_header(self, title: str):
        """
        Display a section header.
        
        Args:
            title: Section title
        """
        print(f"\n{Fore.BLUE}{'=' * 20} {title} {'=' * 20}{Style.RESET_ALL}\n")
    
    def display_success(self, message: str):
        """
        Display a success message.
        
        Args:
            message: Success message
        """
        print(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")
    
    def display_error(self, message: str):
        """
        Display an error message.
        
        Args:
            message: Error message
        """
        print(f"{Fore.RED}✗ {message}{Style.RESET_ALL}")
    
    def display_info(self, message: str):
        """
        Display an info message.
        
        Args:
            message: Info message
        """
        print(f"{Fore.CYAN}ℹ {message}{Style.RESET_ALL}")
    
    def display_warning(self, message: str):
        """
        Display a warning message.
        
        Args:
            message: Warning message
        """
        print(f"{Fore.YELLOW}⚠ {message}{Style.RESET_ALL}")
    
    def prompt_yes_no(self, question: str) -> bool:
        """
        Prompt for a yes/no answer.
        
        Args:
            question: Question to ask
            
        Returns:
            True if yes, False if no
        """
        while True:
            answer = input(f"{Fore.YELLOW}{question} (y/n): {Style.RESET_ALL}").strip().lower()
            if answer in ['y', 'yes']:
                return True
            elif answer in ['n', 'no']:
                return False
            else:
                self.display_error("Please enter 'y' or 'n'")
    
    def prompt_choice(self, question: str, options: List[str]) -> int:
        """
        Prompt for a choice from a list of options.
        
        Args:
            question: Question to ask
            options: List of options
            
        Returns:
            Index of selected option
        """
        print(f"{Fore.YELLOW}{question}{Style.RESET_ALL}")
        for i, option in enumerate(options, 1):
            print(f"{Fore.CYAN}{i}) {option}{Style.RESET_ALL}")
        
        while True:
            try:
                choice = int(input(f"{Fore.YELLOW}Enter your choice (1-{len(options)}): {Style.RESET_ALL}"))
                if 1 <= choice <= len(options):
                    return choice - 1
                else:
                    self.display_error(f"Please enter a number between 1 and {len(options)}")
            except ValueError:
                self.display_error("Please enter a valid number")
    
    def prompt_string(self, prompt: str, default: Optional[str] = None) -> str:
        """
        Prompt for a string input.
        
        Args:
            prompt: Prompt message
            default: Default value
            
        Returns:
            User input string
        """
        default_display = f" [{default}]" if default else ""
        user_input = input(f"{Fore.YELLOW}{prompt}{default_display}: {Style.RESET_ALL}").strip()
        return user_input if user_input else default
    
    def prompt_integer(self, prompt: str, default: Optional[int] = None, min_value: Optional[int] = None, max_value: Optional[int] = None) -> int:
        """
        Prompt for an integer input.
        
        Args:
            prompt: Prompt message
            default: Default value
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            
        Returns:
            User input integer
        """
        default_display = f" [{default}]" if default is not None else ""
        range_display = ""
        if min_value is not None and max_value is not None:
            range_display = f" ({min_value}-{max_value})"
        elif min_value is not None:
            range_display = f" (min: {min_value})"
        elif max_value is not None:
            range_display = f" (max: {max_value})"
        
        while True:
            try:
                user_input = input(f"{Fore.YELLOW}{prompt}{range_display}{default_display}: {Style.RESET_ALL}").strip()
                if not user_input and default is not None:
                    return default
                
                value = int(user_input)
                
                if min_value is not None and value < min_value:
                    self.display_error(f"Value must be at least {min_value}")
                    continue
                
                if max_value is not None and value > max_value:
                    self.display_error(f"Value must be at most {max_value}")
                    continue
                
                return value
            except ValueError:
                self.display_error("Please enter a valid integer")
    
    def display_config(self, config: Dict[str, Any]):
        """
        Display configuration in a visually appealing format.
        
        Args:
            config: Configuration dictionary
        """
        self.display_section_header("Configuration")
        
        for section, items in config.items():
            print(f"{Fore.MAGENTA}{section}:{Style.RESET_ALL}")
            
            if isinstance(items, dict):
                for key, value in items.items():
                    print(f"  {Fore.CYAN}{key}: {Fore.WHITE}{value}{Style.RESET_ALL}")
            else:
                print(f"  {Fore.WHITE}{items}{Style.RESET_ALL}")
            
            print()
    
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
        
        # Get section
        sections = list(config.keys())
        section_idx = self.prompt_choice("Select section to edit:", sections)
        section = sections[section_idx]
        
        # Get item
        if isinstance(config[section], dict):
            items = list(config[section].keys())
            item_idx = self.prompt_choice(f"Select item in {section} to edit:", items)
            item = items[item_idx]
            
            # Get current value
            current_value = config[section][item]
            
            # Prompt for new value
            if isinstance(current_value, bool):
                new_value = self.prompt_yes_no(f"New value for {item}")
            elif isinstance(current_value, int):
                new_value = self.prompt_integer(f"New value for {item}", default=current_value)
            else:
                new_value = self.prompt_string(f"New value for {item}", default=str(current_value))
            
            # Update config
            config[section][item] = new_value
        else:
            # Section is a single value
            current_value = config[section]
            
            # Prompt for new value
            if isinstance(current_value, bool):
                new_value = self.prompt_yes_no(f"New value for {section}")
            elif isinstance(current_value, int):
                new_value = self.prompt_integer(f"New value for {section}", default=current_value)
            else:
                new_value = self.prompt_string(f"New value for {section}", default=str(current_value))
            
            # Update config
            config[section] = new_value
        
        self.display_success("Configuration updated")
        return config
    
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
            self.display_success(f"Configuration loaded from {file_path}")
            return config
        except Exception as e:
            self.display_error(f"Error loading configuration: {str(e)}")
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
            self.display_success(f"Configuration saved to {file_path}")
            return True
        except Exception as e:
            self.display_error(f"Error saving configuration: {str(e)}")
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
                    "enabled": False,
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
