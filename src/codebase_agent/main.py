"""Main CLI entry point for the AutoGen Codebase Understanding Agent."""

import click
import logging
from pathlib import Path
from typing import Optional

from codebase_agent.config.configuration import ConfigurationManager, ConfigurationError


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.group()
@click.option('--debug', is_flag=True, help='Enable debug logging')
def cli(debug: bool):
    """AutoGen Codebase Understanding Agent CLI."""
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")


@cli.command()
@click.argument('codebase_path', type=click.Path(exists=True), default='.')
def setup(codebase_path: str):
    """Setup project environment and validate configuration."""
    try:
        project_root = Path(codebase_path).resolve()
        config_manager = ConfigurationManager(project_root)
        
        # Try to create .env file if missing
        if config_manager.create_env_file_if_missing():
            click.echo(f"✅ Created .env file from .env.example")
        
        # Get setup instructions
        instructions = config_manager.get_setup_instructions()
        click.echo(instructions)
        
        # If configuration is valid, show success
        if "✅" in instructions:
            # Test LLM configuration
            try:
                llm_config = config_manager.get_llm_config()
                autogen_config = config_manager.get_autogen_config()
                click.echo(f"✅ LLM Configuration validated for model: {llm_config.model}")
                click.echo(f"✅ AutoGen configuration ready")
                
                agent_config = config_manager.get_agent_config()
                click.echo(f"✅ Agent configuration loaded (timeout: {agent_config['agent_timeout']}s)")
                
            except ConfigurationError as e:
                click.echo(f"❌ Configuration error: {e}", err=True)
                raise click.Abort()
                
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        click.echo(f"❌ Setup failed: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument('task_description')
@click.option('--codebase-path', type=click.Path(exists=True), default='.',
              help='Path to the codebase to analyze')
def analyze(task_description: str, codebase_path: str):
    """Analyze codebase for specific development task."""
    try:
        project_root = Path(codebase_path).resolve()
        config_manager = ConfigurationManager(project_root)
        
        # Validate configuration first
        validation_errors = config_manager.validate_configuration()
        if validation_errors:
            click.echo("❌ Configuration validation failed:")
            for error in validation_errors:
                click.echo(f"  - {error}")
            click.echo("\nRun 'codebase-agent setup' to configure the environment.")
            raise click.Abort()
        
        # Get configurations
        llm_config = config_manager.get_llm_config()
        agent_config = config_manager.get_agent_config()
        
        click.echo(f"🔍 Analyzing codebase at: {project_root}")
        click.echo(f"📝 Task: {task_description}")
        click.echo(f"🤖 Using model: {llm_config.model}")
        
        # TODO: Implement actual analysis with AutoGen agents
        click.echo("⚠️  Analysis implementation coming in next tasks...")
        click.echo("✅ Configuration validated successfully!")
        
    except ConfigurationError as e:
        click.echo(f"❌ Configuration error: {e}", err=True)
        raise click.Abort()
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        click.echo(f"❌ Analysis failed: {e}", err=True)
        raise click.Abort()


if __name__ == '__main__':
    cli()
