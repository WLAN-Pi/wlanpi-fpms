from .version import __version__
import commands
import click

"""
    This is the top level of the CLI command tree. The CLI group is created and the
    subcommands are imported from the commands dir and added to the group. This allows
    these commands to be run with 'luma <command>'.
"""

@click.group(help='This CLI will allow you to interact with the Lumavate platform from your terminal. For setup instructions, look in github. \
Each command below has subcommands. Pass the --help flag to those commands for more information on how to use them.')
@click.version_option(version=__version__, prog_name="Lumavate CLI")
def cli():
    pass

cli.add_command(commands.env)
cli.add_command(commands.profile)
cli.add_command(commands.organization)
cli.add_command(commands.widget)
cli.add_command(commands.widget_version)
cli.add_command(commands.app_builder)
cli.add_command(commands.app_builder_version)
cli.add_command(commands.asset)
cli.add_command(commands.asset_version)
cli.add_command(commands.component_set)
cli.add_command(commands.component_set_version)
cli.add_command(commands.microservice)
cli.add_command(commands.microservice_version)
cli.add_command(commands.api)
cli.add_command(commands.experience)
cli.add_command(commands.experience_collection)

if __name__ == '__main__':
    cli()
