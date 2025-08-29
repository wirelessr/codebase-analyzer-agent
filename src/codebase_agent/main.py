"""Command-line interface for the AutoGen Codebase Understanding Agent.

This module provides the main entry point for the codebase analysis system,
offering commands for analyzing codebases and validating system configuration.
"""

import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.text import Text

from .config.configuration import ConfigurationManager, ConfigurationError
from .agents.manager import AgentManager
from .utils.logging import setup_logging


console = Console()
logger = logging.getLogger(__name__)


@click.group()
@click.option('--log-level', default='INFO', 
              type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']),
              help='Set the logging level')
@click.option('--logs-dir', default='logs', type=click.Path(),
              help='Logs directory path (default: logs)')
def cli(log_level: str, logs_dir: str):
    """AutoGen Codebase Understanding Agent CLI.
    
    An intelligent agent system that analyzes codebases using multi-agent
    collaboration and provides targeted insights for development tasks.
    """
    # Setup logging
    try:
        setup_logging(log_level, logs_dir)
        logger.info("AutoGen Codebase Agent CLI started")
    except Exception as e:
        console.print(f"[red]Error setting up logging: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('codebase_path', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.argument('task_description')
@click.option('--output-format', default='text', 
              type=click.Choice(['text', 'json']),
              help='Output format for results')
@click.option('--working-dir', default=None, type=click.Path(exists=True, file_okay=False, dir_okay=True),
              help='Working directory for analysis (default: codebase_path)')
def analyze(codebase_path: str, task_description: str, output_format: str, working_dir: Optional[str]):
    """Analyze codebase for specific development task.
    
    CODEBASE_PATH: Path to the codebase directory to analyze
    TASK_DESCRIPTION: Description of the development task or query
    
    Examples:
        codebase-agent analyze ./my-project "implement OAuth authentication"
        codebase-agent analyze /path/to/project "add payment processing module"
    """
    start_time = time.time()
    codebase_path = Path(codebase_path).resolve()
    
    # Use working directory or default to codebase path
    working_directory = Path(working_dir).resolve() if working_dir else codebase_path
    
    console.print(Panel.fit(
        f"[bold blue]AutoGen Codebase Analysis[/bold blue]\n"
        f"[cyan]Codebase:[/cyan] {codebase_path}\n"
        f"[cyan]Task:[/cyan] {task_description}\n"
        f"[cyan]Working Directory:[/cyan] {working_directory}",
        border_style="blue"
    ))
    
    try:
        # Initialize configuration
        with console.status("[bold green]Loading configuration..."):
            config_manager = ConfigurationManager(codebase_path)
            config_manager.load_environment()
            
            # Validate configuration
            missing_keys = config_manager.validate_configuration()
            if missing_keys:
                console.print(f"[red]Error: Missing configuration keys: {', '.join(missing_keys)}[/red]")
                console.print("[yellow]Please check your .env file and configure the required variables.[/yellow]")
                console.print("[cyan]Use 'codebase-agent setup <path>' to validate your configuration.[/cyan]")
                sys.exit(1)
        
        # Initialize agent manager
        with console.status("[bold green]Initializing AI agents..."):
            agent_manager = AgentManager(config_manager)
            agent_manager.initialize_agents()
        
        # Perform analysis with progress indication
        console.print("\n[bold green]Starting codebase analysis...[/bold green]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=False
        ) as progress:
            task = progress.add_task("Analyzing codebase with AI agents...", total=None)
            
            # Execute the analysis
            result = agent_manager.process_query_with_review_cycle(
                task_description, 
                str(working_directory)
            )
            
            progress.update(task, description="Analysis complete!")
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        # Format and display results
        console.print("\n" + "="*80 + "\n")
        
        if output_format == 'json':
            import json
            output = {
                "codebase_path": str(codebase_path),
                "task_description": task_description,
                "analysis_result": result,
                "execution_time": execution_time,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            console.print(json.dumps(output, indent=2))
        else:
            # Text format (default)
            console.print(Panel(
                result,
                title="[bold green]Analysis Results[/bold green]",
                border_style="green",
                padding=(1, 2)
            ))
            
            # Display summary statistics
            console.print(f"\n[dim]Analysis completed in {execution_time:.2f} seconds[/dim]")
        
        logger.info(f"Analysis completed successfully in {execution_time:.2f} seconds")
        
    except ConfigurationError as e:
        console.print(f"[red]Configuration Error: {e}[/red]")
        console.print("[yellow]Please check your .env file and ensure all required variables are set.[/yellow]")
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
        
    except FileNotFoundError as e:
        console.print(f"[red]File not found: {e}[/red]")
        console.print("[yellow]Please check that the codebase path exists and is accessible.[/yellow]")
        logger.error(f"File not found: {e}")
        sys.exit(1)
        
    except PermissionError as e:
        console.print(f"[red]Permission denied: {e}[/red]")
        console.print("[yellow]Please check that you have read access to the codebase directory.[/yellow]")
        logger.error(f"Permission error: {e}")
        sys.exit(1)
        
    except Exception as e:
        console.print(f"[red]Unexpected error during analysis: {e}[/red]")
        console.print("[yellow]Please check the logs for more details.[/yellow]")
        logger.exception("Unexpected error during analysis")
        sys.exit(1)


@cli.command()
@click.argument('codebase_path', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--check-api', is_flag=True, help='Test API connectivity')
def setup(codebase_path: str, check_api: bool):
    """Setup and validate project environment and configuration.
    
    CODEBASE_PATH: Path to the project directory to validate
    
    This command checks:
    - Environment variable configuration
    - API key validity and format
    - Required dependencies
    - File permissions
    """
    codebase_path = Path(codebase_path).resolve()
    
    console.print(Panel.fit(
        f"[bold blue]Environment Setup Validation[/bold blue]\n"
        f"[cyan]Project Path:[/cyan] {codebase_path}",
        border_style="blue"
    ))
    
    success = True
    
    try:
        # Check configuration
        console.print("\n[bold]Checking configuration...[/bold]")
        config_manager = ConfigurationManager(codebase_path)
        
        # Check if .env file exists
        env_file = codebase_path / ".env"
        if not env_file.exists():
            console.print("[yellow]⚠ No .env file found[/yellow]")
            console.print(f"[cyan]Please create a .env file at: {env_file}[/cyan]")
            
            # Check for .env.example
            env_example = codebase_path / ".env.example"
            if env_example.exists():
                console.print(f"[green]✓ Found .env.example template at: {env_example}[/green]")
                console.print("[cyan]Copy .env.example to .env and configure your API settings.[/cyan]")
            else:
                console.print("[yellow]⚠ No .env.example template found[/yellow]")
            success = False
        else:
            console.print(f"[green]✓ Found .env file at: {env_file}[/green]")
        
        # Load and validate environment
        config_manager.load_environment()
        missing_keys = config_manager.validate_configuration()
        
        if missing_keys:
            console.print(f"[red]✗ Missing required environment variables:[/red]")
            for key in missing_keys:
                description = config_manager.REQUIRED_KEYS.get(key, "Required configuration")
                console.print(f"  [red]• {key}[/red] - {description}")
            success = False
        else:
            console.print("[green]✓ All required environment variables are set[/green]")
        
        # Check API configuration if requested
        if check_api and not missing_keys:
            console.print("\n[bold]Testing API connectivity...[/bold]")
            try:
                with console.status("[bold green]Testing API connection..."):
                    # Get model client to test configuration
                    model_client = config_manager.get_model_client()
                    console.print("[green]✓ API configuration appears valid[/green]")
                    
                    # Display configuration details (without sensitive info)
                    llm_config = config_manager.get_llm_config()
                    console.print(f"[cyan]Model:[/cyan] {llm_config.get('model', 'Unknown')}")
                    console.print(f"[cyan]Base URL:[/cyan] {llm_config.get('base_url', 'Unknown')}")
                    
            except Exception as e:
                console.print(f"[red]✗ API configuration error: {e}[/red]")
                console.print("[yellow]Please check your API key and base URL settings.[/yellow]")
                success = False
        
        # Check file permissions
        console.print("\n[bold]Checking file permissions...[/bold]")
        if codebase_path.is_dir() and os.access(codebase_path, os.R_OK):
            console.print("[green]✓ Read access to codebase directory[/green]")
        else:
            console.print(f"[red]✗ Cannot read codebase directory: {codebase_path}[/red]")
            success = False
        
        # Summary
        console.print("\n" + "="*50)
        if success:
            console.print("[bold green]✓ Setup validation successful![/bold green]")
            console.print("[cyan]You can now run analysis with:[/cyan]")
            console.print(f"[dim]  codebase-agent analyze {codebase_path} \"your task description\"[/dim]")
        else:
            console.print("[bold red]✗ Setup validation failed[/bold red]")
            console.print("[yellow]Please fix the issues above before running analysis.[/yellow]")
            sys.exit(1)
            
    except Exception as e:
        console.print(f"[red]Error during setup validation: {e}[/red]")
        logger.exception("Error during setup validation")
        sys.exit(1)


def main():
    """Main entry point for the CLI."""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        logger.exception("Unexpected error in main")
        sys.exit(1)


if __name__ == "__main__":
    main()
