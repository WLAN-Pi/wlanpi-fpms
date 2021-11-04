"""
    These are the sub-commands for a top level object added to the CLI group in 'cli.py'.
    The commands and options are implemented here and the logic behind them resides in the corresponding behavior file.
"""

import behavior
import click
import pyke

@click.group('component-set', help='A component-set is comprised of component-set-versions. You can share component-sets with other orgs giving them access to use the associated versions.')
def component_set():
    pass

@click.command('ls')
@click.option('--profile', '-p', help=pyke.helptxt.PROFILE, callback=pyke.select_profile, autocompletion=pyke.auth.get_profile_names)
@click.option('--format', '-f', default='{id} {name} {urlRef} {createdAt}', help=pyke.helptxt.FORMAT)
@click.option('--filter', default='')
@click.option('--page', default=1)
@click.option('--pagesize', default=100)
@click.option('--json', is_flag=True, help='Return raw json from the platform')
def list(**kwargs):
    behavior.ComponentSetBehavior(**kwargs).list()

@click.command('rm')
@click.option('--profile', '-p', help=pyke.helptxt.PROFILE, callback=pyke.select_profile, autocompletion=pyke.auth.get_profile_names)
@click.option('--component-set', '-cs', prompt=True, help='The ID or the urlRef of the component-set to delete')
@click.option('--format', '-f', default='{id} {name} {urlRef} {createdAt}', help=pyke.helptxt.FORMAT)
@click.option('--json', is_flag=True, help='Return raw json from the platform')
def delete(**kwargs):
    behavior.ComponentSetBehavior(**kwargs).delete()

@click.command('add')
@click.option('--profile', '-p', help=pyke.helptxt.PROFILE, callback=pyke.select_profile, autocompletion=pyke.auth.get_profile_names)
@click.option('--name', prompt=True, help='The name of the component set')
@click.option('--url-ref', prompt=True, help="A unique value for how the component-set will be addressed in a URL.")
@click.option('--icon-file', '-path', type=click.Path(file_okay=True, dir_okay=False, exists=True), help='The path to an SVG icon for the component set')
@click.option('--format', '-f', default='{id} {name} {urlRef} {createdAt}', help=pyke.helptxt.FORMAT)
@click.option('--json', is_flag=True, help='Return raw json from the platform')
def create(**kwargs):
    behavior.ComponentSetBehavior(**kwargs).create()

@click.command()
@click.option('--profile', '-p', help=pyke.helptxt.PROFILE, callback=pyke.select_profile, autocompletion=pyke.auth.get_profile_names)
@click.option('--component-set', '-cs', prompt=True, help='The ID or the urlRef of the component-set to update')
@click.option('--name', default='', help='The name of the component set')
@click.option('--icon-file', '-path', type=click.Path(file_okay=True, dir_okay=False, exists=True), help='The path to an SVG icon for the component set')
@click.option('--format', '-f', default='{id} {name} {urlRef} {createdAt}', help=pyke.helptxt.FORMAT)
@click.option('--json', is_flag=True, help='Return raw json from the platform')
def update(**kwargs):
    behavior.ComponentSetBehavior(**kwargs).update()

@click.command('access', help="The access command shares and unshares objects with child orgs.")
@click.option('--profile', '-p', help=pyke.helptxt.PROFILE, callback=pyke.select_profile, autocompletion=pyke.auth.get_profile_names)
@click.option('--component-set', '-cs', prompt=True, help='The id or the urlRef of the component-set being shared/unshared')
@click.option('--add', multiple=True, help="Share with an org. (ID || Org Name)")
@click.option('--rm', multiple=True, help="Un-Share with an org. (ID || Org Name)")
@click.option('--absolute', multiple=True, help='Flush and fill shared with list. (ID || Org Name)')
@click.option('--format', '-f', default='{failed} {sharedWith} {unsharedFrom} {resultingGrantees}', help=pyke.helptxt.FORMAT)
@click.option('--current', is_flag=True, help="Returns a list of orgs currently shared with this object.")
@click.option('--json', is_flag=True, help='Return raw json from the platform')
def share(**kwargs):
    behavior.ComponentSetBehavior(**kwargs).share()

component_set.add_command(list)
component_set.add_command(create)
component_set.add_command(delete)
component_set.add_command(update)
component_set.add_command(share)
