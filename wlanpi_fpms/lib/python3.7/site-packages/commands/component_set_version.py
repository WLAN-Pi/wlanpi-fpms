"""
    These are the sub-commands for a top level object added to the CLI group in 'cli.py'.
    The commands and options are implemented here and the logic behind them resides in the corresponding behavior file.
"""

import behavior
import click
import pyke

@click.group('component-set-version', help="A component-set-version is where the platform looks for components when used in a widget. \
The version also contains other details like CSS includes.")
def component_set_version():
    pass

@click.command('ls')
@click.option('--profile', '-p', help=pyke.helptxt.PROFILE, callback=pyke.select_profile, autocompletion=pyke.auth.get_profile_names)
@click.option('--component-set', '-cs', prompt=True, help='The id or the urlRef of the component-set')
@click.option('--format', '-f', default='{id} {versionNumber} {directIncludes} {directCssIncludes} {label} {expand__experiences} {createdAt}', help=pyke.helptxt.FORMAT)
@click.option('--filter', default='')
@click.option('--page', default=1)
@click.option('--pagesize', default=100)
@click.option('--json', is_flag=True, help='Return raw json from the platform')
def list(**kwargs):
    behavior.ComponentSetVersionBehavior(**kwargs).list()

@click.command('components', help="Given a --component-set and a --version, this will return the raw JSON contained in a component-set-version")
@click.option('--profile', '-p', help=pyke.helptxt.PROFILE, callback=pyke.select_profile, autocompletion=pyke.auth.get_profile_names)
@click.option('--component-set', '-cs', prompt=True, help='The id or the urlRef of the component-set associated with the version')
@click.option('--version', '-v', prompt=True)
@click.option('--json', is_flag=True, help='Return raw json from the platform')
def components(**kwargs):
    behavior.ComponentSetVersionBehavior(**kwargs).list_components()

@click.command('add', help="While adding a new component-set-version you must always upload a zipped file, even if you use the from-version option")
@click.option('--profile', '-p', help=pyke.helptxt.PROFILE, callback=pyke.select_profile, autocompletion=pyke.auth.get_profile_names)
@click.option('--component-set', '-cs', prompt=True, help='The ID or the urlRef of the component-set to associate with the new version')
@click.option('--component-set-file-path', '-path', prompt=True, required=True, type=click.Path(file_okay=True, dir_okay=False, exists=True), help='Must be the path to a zipped file.')
@click.option('--from-version', '-fv', type=str, help=pyke.helptxt.FROM_VERSION)
@click.option('--version', '-v', type=str, default=None, help="The version number of the new version")
@click.option('--patch', 'version_bump', flag_value='patch', default=True)
@click.option('--minor', 'version_bump', flag_value='minor')
@click.option('--major', 'version_bump', flag_value='major')
@click.option('--css-includes', type=str, default=None, multiple=True)
@click.option('--direct-includes', type=str, default=None, multiple=True)
@click.option('--label', '-l', type=click.Choice(['prod', 'dev', 'old']))
@click.option('--format', '-f', default='{id} {versionNumber} {directIncludes} {directCssIncludes} {label} {createdAt}', help=pyke.helptxt.FORMAT)
@click.option('--json', is_flag=True, help='Return raw json from the platform')
def create(**kwargs):
    behavior.ComponentSetVersionBehavior(**kwargs).create()

@click.command()
@click.option('--profile', '-p', help=pyke.helptxt.PROFILE, callback=pyke.select_profile, autocompletion=pyke.auth.get_profile_names)
@click.option('--component-set', '-cs', prompt=True, help='The ID or the urlRef of the component-set associated with the version')
@click.option('--version', '-v', prompt=True, help='The ID or the version number of the version to update')
@click.option('--label', '-l', prompt=True, type=click.Choice(['prod', 'dev', 'old']))
@click.option('--format', '-f', default='{id} {versionNumber} {directIncludes} {directCssIncludes} {label} {createdAt}', help=pyke.helptxt.FORMAT)
@click.option('--json', is_flag=True, help='Return raw json from the platform')
def update(**kwargs):
    behavior.ComponentSetVersionBehavior(**kwargs).update()

@click.command('rm')
@click.option('--profile', '-p', help=pyke.helptxt.PROFILE, callback=pyke.select_profile, autocompletion=pyke.auth.get_profile_names)
@click.option('--component-set', '-cs', prompt=True, help='The ID or the urlRef of the component-set associated with the version')
@click.option('--version', '-v', prompt=True, help='The version ID, the version number or a version mask')
@click.option('--format', '-f', default='{id} {versionNumber} {directIncludes} {directCssIncludes} {label} {createdAt}', help=pyke.helptxt.FORMAT)
@click.option('--json', is_flag=True, help='Return raw json from the platform')
def delete(**kwargs):
    behavior.ComponentSetVersionBehavior(**kwargs).delete()

component_set_version.add_command(list)
component_set_version.add_command(create)
component_set_version.add_command(delete)
component_set_version.add_command(update)
component_set_version.add_command(components)
