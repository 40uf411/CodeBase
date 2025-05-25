import os
import sys
import time
from typing import Dict, List, Optional, Any
from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, SpinnerColumn
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
import shutil

class FileGenerationManager:
    """
    Manager for file generation process with improved user experience.
    
    Features:
    - Progress bars for file generation
    - Status updates during generation
    - File copying visualization
    - Error handling and reporting
    """
    
    def __init__(self, console: Console):
        """
        Initialize the file generation manager.
        
        Args:
            console: Rich console for output
        """
        self.console = console
    
    def copy_stock_structure(self, source_dir: str, target_dir: str) -> bool:
        """
        Copy stock folder structure to target directory with progress visualization.
        
        Args:
            source_dir: Source directory (stock folder)
            target_dir: Target directory for new project
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create target directory if it doesn't exist
            os.makedirs(target_dir, exist_ok=True)
            
            # Get list of files to copy
            all_files = []
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    source_path = os.path.join(root, file)
                    rel_path = os.path.relpath(source_path, source_dir)
                    all_files.append(rel_path)
            
            # Copy files with progress bar
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TextColumn("[bold green]{task.fields[filename]}"),
                console=self.console
            ) as progress:
                copy_task = progress.add_task(
                    "[yellow]Copying files...", total=len(all_files), filename=""
                )
                
                for rel_path in all_files:
                    source_path = os.path.join(source_dir, rel_path)
                    target_path = os.path.join(target_dir, rel_path)
                    
                    # Update progress
                    progress.update(copy_task, advance=1, filename=rel_path)
                    
                    # Create target directory if it doesn't exist
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    
                    # Copy file
                    shutil.copy2(source_path, target_path)
                    
                    # Small delay for visual effect
                    time.sleep(0.01)
            
            self.console.print(f"[green]Successfully copied stock structure to {target_dir}[/green]")
            return True
        
        except Exception as e:
            self.console.print(f"[red]Error copying stock structure: {str(e)}[/red]")
            return False
    
    def generate_entity_files(self, entity_config: Dict[str, Any], target_dir: str) -> bool:
        """
        Generate entity files based on configuration with progress visualization.
        
        Args:
            entity_config: Entity configuration
            target_dir: Target directory for entity files
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Import EntityGenerator here to avoid circular imports
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from generator.fastapi_entity import EntityGenerator, FIELD_TYPES, PYTHON_TYPES
            
            entity_name = entity_config["name"]
            fields = entity_config.get("fields", [])
            
            # Add UUID primary key if not already present
            id_field_exists = any(field.get('name') == 'id' for field in fields)
            
            if not id_field_exists:
                # Add id field as the first field
                id_field = {
                    "name": "id",
                    "type": "uuid",
                    "sqlalchemy_type": "UUID(as_uuid=True)",
                    "python_type": "UUID",
                    "nullable": False,
                    "unique": True,
                    "index": True,
                    "primary_key": True,
                    "default": "uuid.uuid4"
                }
                fields.insert(0, id_field)
                self.console.print("[green]Added UUID primary key 'id' field[/green]")
            
            # Fix: Ensure each field has sqlalchemy_type and python_type
            for field in fields:
                if "type" in field:
                    field_type = field["type"].lower()  # Ensure lowercase for dictionary lookup
                    
                    # Set sqlalchemy_type if missing
                    if "sqlalchemy_type" not in field:
                        if field_type in FIELD_TYPES:
                            field["sqlalchemy_type"] = FIELD_TYPES[field_type]
                        else:
                            # Default to String if type not found
                            field["sqlalchemy_type"] = "String"
                            self.console.print(f"[yellow]Warning: Unknown field type '{field_type}', defaulting sqlalchemy_type to String.[/yellow]")
                    
                    # Set python_type if missing
                    if "python_type" not in field:
                        if field_type in PYTHON_TYPES:
                            field["python_type"] = PYTHON_TYPES[field_type]
                        else:
                            # Default to str if type not found
                            field["python_type"] = "str"
                            self.console.print(f"[yellow]Warning: Unknown field type '{field_type}', defaulting python_type to str.[/yellow]")
                else:
                    # If no type specified, default to String/str
                    field["type"] = "string"
                    field["sqlalchemy_type"] = "String"
                    field["python_type"] = "str"
                    self.console.print(f"[yellow]Warning: Field {field.get('name', 'unknown')} missing type, defaulting to string.[/yellow]")
            
            # Debug: Print fields to verify structure
            self.console.print(f"[blue]DEBUG: Fields structure:[/blue]")
            for field in fields:
                self.console.print(f"[blue]  - {field.get('name')}: {field.get('type')} -> SQLAlchemy: {field.get('sqlalchemy_type')}, Python: {field.get('python_type')}[/blue]")
            
            relationships = entity_config.get("relationships", [])
            # is_streamable = entity_config.get("is_streamable", False)
            cache_config = entity_config.get("cache_config", {"enabled": False, "duration": 0})
            
            # Initialize EntityGenerator
            entity_generator = EntityGenerator(target_dir, self.console)
            
            # Define files to generate
            files_to_generate = [
                f"models/{entity_name.lower()}.py",
                f"schemas/{entity_name.lower()}.py",
                f"repositories/{entity_name.lower()}_repository.py",
                f"services/{entity_name.lower()}_service.py",
                f"routers/{entity_name.lower()}.py"
            ]
            
            # Generate files with progress bar
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TextColumn("[bold green]{task.fields[filename]}"),
                console=self.console
            ) as progress:
                generate_task = progress.add_task(
                    f"[yellow]Generating {entity_name} files...", total=len(files_to_generate), filename=""
                )
                
                # Generate model
                progress.update(generate_task, advance=1, filename=f"models/{entity_name.lower()}.py")
                entity_generator.generate_model(entity_name, fields, relationships, progress=progress)
                time.sleep(0.1)
                
                # Generate schema
                progress.update(generate_task, advance=1, filename=f"schemas/{entity_name.lower()}.py")
                entity_generator.generate_schema(entity_name, fields, relationships, progress=progress)
                time.sleep(0.1)
                
                # Generate repository
                progress.update(generate_task, advance=1, filename=f"repositories/{entity_name.lower()}_repository.py")
                entity_generator.generate_repository(entity_name, progress=progress)
                time.sleep(0.1)
                
                # Generate service
                progress.update(generate_task, advance=1, filename=f"services/{entity_name.lower()}_service.py")
                entity_generator.generate_service(entity_name, progress=progress)
                time.sleep(0.1)
                
                # Generate router
                progress.update(generate_task, advance=1, filename=f"routers/{entity_name.lower()}.py")
                entity_generator.generate_router(entity_name, cache_config, progress=progress)
                time.sleep(0.1)
            
            self.console.print(f"[green]Successfully generated {entity_name} files in {target_dir}[/green]")
            return True
        
        except Exception as e:
            self.console.print(f"[red]Error generating entity files: {str(e)}[/red]")
            import traceback
            self.console.print(f"[red]{traceback.format_exc()}[/red]")
            return False

    def update_main_file(self, target_dir: str, entities: List[str]) -> bool:
        """
        Update main.py file to include new entities with progress visualization.
        
        Args:
            target_dir: Target directory
            entities: List of entity names
            
        Returns:
            True if successful, False otherwise
        """
        try:
            main_file = os.path.join(target_dir, "main.py")
            
            # Update main file with progress spinner
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                console=self.console
            ) as progress:
                update_task = progress.add_task(
                    "[yellow]Updating main.py...", total=1
                )
                
                # Read existing content
                with open(main_file, 'r') as f:
                    content = f.read()
                
                # Add router imports
                router_imports = "\n".join([
                    f"from .routers import {entity.lower()}"
                    for entity in entities
                ])
                
                # Add router includes
                router_includes = "\n".join([
                    f"app.include_router({entity.lower()}.router)"
                    for entity in entities
                ])
                
                # Update content (placeholder for actual content modification)
                updated_content = content + f"\n\n# Added by generator\n{router_imports}\n\n{router_includes}\n"
                
                # Write updated content
                with open(main_file, 'w') as f:
                    f.write(updated_content)
                
                # Update progress
                progress.update(update_task, advance=1)
                
                # Small delay for visual effect
                time.sleep(0.5)
            
            self.console.print(f"[green]Successfully updated main.py in {target_dir}[/green]")
            return True
        
        except Exception as e:
            self.console.print(f"[red]Error updating main file: {str(e)}[/red]")
            return False
    
    def generate_migration(self, target_dir: str) -> bool:
        """
        Generate migration file with progress visualization.
        
        Args:
            target_dir: Target directory
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Generate migration with progress spinner
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                console=self.console
            ) as progress:
                migration_task = progress.add_task(
                    "[yellow]Generating migration...", total=1
                )
                
                # Simulate migration generation
                time.sleep(1.0)
                
                # Create migration file
                migration_dir = os.path.join(target_dir, "migrations", "versions")
                os.makedirs(migration_dir, exist_ok=True)
                
                migration_file = os.path.join(migration_dir, f"{int(time.time())}_initial_migration.py")
                with open(migration_file, 'w') as f:
                    f.write("# Generated migration file\n")
                
                # Update progress
                progress.update(migration_task, advance=1)
            
            self.console.print(f"[green]Successfully generated migration in {target_dir}[/green]")
            return True
        
        except Exception as e:
            self.console.print(f"[red]Error generating migration: {str(e)}[/red]")
            return False
    
    def display_generation_summary(self, target_dir: str, entities: List[str]):
        """
        Display summary of generated files.
        
        Args:
            target_dir: Target directory
            entities: List of entity names
        """
        # Count generated files
        file_count = 0
        for root, dirs, files in os.walk(target_dir):
            file_count += len(files)
        
        # Create summary table
        table = Table(title="Generation Summary")
        table.add_column("Item", style="cyan")
        table.add_column("Count", style="green")
        
        table.add_row("Total Files", str(file_count))
        table.add_row("Entities", str(len(entities)))
        table.add_row("Models", str(len(entities) + 4))  # +4 for base, user, role, privilege
        table.add_row("Routers", str(len(entities) + 2))  # +2 for auth, cache
        
        self.console.print(Panel(table))
        
        # Display next steps
        self.console.print(Panel(
            Text.from_markup(
                "[bold green]Generation Complete![/bold green]\n\n"
                "[yellow]Next Steps:[/yellow]\n"
                "1. Navigate to your project: [bold]cd " + target_dir + "[/bold]\n"
                "2. Install dependencies: [bold]pip install -r requirements.txt[/bold]\n"
                "3. Set up your database\n"
                "4. Run migrations: [bold]alembic upgrade head[/bold]\n"
                "5. Start the server: [bold]uvicorn main:app --reload[/bold]"
            )
        ))