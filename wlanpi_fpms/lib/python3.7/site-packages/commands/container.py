import commands
import behavior
import click
import pyke


@click.command('ls')
@click.option('--profile', '-p', help=pyke.helptxt.PROFILE, callback=pyke.select_profile, autocompletion=pyke.auth.get_profile_names)
@click.option('--format', '-f', default='{id} {name} {urlRef} {createdAt}', help=pyke.helptxt.FORMAT)
@click.option('--filter', default='')
@click.option('--page', default=1)
@click.option('--pagesize', default=100)
@click.option('--json/--table', default=False, help='Return raw json from the platform.')
def list(**kwargs):
    behavior.ContainerBehavior(**kwargs).list()

@click.command('rm')
@click.option('--profile', '-p', help=pyke.helptxt.PROFILE, callback=pyke.select_profile, autocompletion=pyke.auth.get_profile_names)
@click.option('--container', '-c', prompt=True, help='The id or the urlRef of the container.')
@click.option('--format', '-f', default='{id} {name} {urlRef} {createdAt}', help=pyke.helptxt.FORMAT)
@click.option('--json/--table', default=False, help='Return raw json from the platform.')
def delete(**kwargs):
    behavior.ContainerBehavior(**kwargs).delete()

@click.command('add')
@click.option('--profile', '-p', help=pyke.helptxt.PROFILE, callback=pyke.select_profile, autocompletion=pyke.auth.get_profile_names)
@click.option('--name', prompt=True, help='The name of the container to create.')
@click.option('--url-ref', prompt=True, help="A unique value for how the container will be addressed.")
@click.option('--icon-file', '-path', type=click.Path(), help='The path to an SVG icon for the container.')
@click.option('--format', '-f', default='{id} {name} {urlRef} {createdAt}', help=pyke.helptxt.FORMAT)
@click.option('--json/--table', default=False, help='Return raw json from the platform.')
def create(**kwargs):
    behavior.ContainerBehavior(**kwargs).create()

@click.command('access', help="The access command shares and unshares objects with child orgs.")
@click.option('--profile', '-p', help=pyke.helptxt.PROFILE, callback=pyke.select_profile, autocompletion=pyke.auth.get_profile_names)
@click.option('--container', '-c', prompt=True, help='The id or the urlRef of the container.')
@click.option('--add', multiple=True, help="Share with an org. (ID || Org Name)")
@click.option('--rm', multiple=True, help="Un-Share with an org. (ID || Org Name)")
@click.option('--absolute', multiple=True, help='Flush and fill shared with list. (ID || Org Name)')
@click.option('--format', '-f', default='{failed} {sharedWith} {unsharedFrom} {resultingGrantees}', help=pyke.helptxt.FORMAT)
@click.option('--json/--table', default=False, help='Return raw json from the platform.')
@click.option('--current', is_flag=True, help="Returns a list of orgs currently shared with this object.")
def share(**kwargs):
    behavior.ContainerBehavior(**kwargs).share()

@click.command()
@click.option('--profile', '-p', help=pyke.helptxt.PROFILE, callback=pyke.select_profile, autocompletion=pyke.auth.get_profile_names)
@click.option('--container', '-c', prompt=True, help='The id or the urlRef of the container.')
@click.option('--name', help='A new name for the container.')
@click.option('--icon-file', '-path', type=click.Path(), help='The path to a new SVG icon for the container.')
@click.option('--format', '-f', default='{id} {name} {urlRef} {createdAt}', help=pyke.helptxt.FORMAT)
@click.option('--json/--table', default=False, help='Return raw json from the platform.')
def update(**kwargs):
    behavior.ContainerBehavior(**kwargs).update()


commands.microservice.add_command(list)
commands.widget.add_command(list)
commands.app_builder.add_command(list)
commands.asset.add_command(list)

commands.microservice.add_command(share)
commands.widget.add_command(share)
commands.app_builder.add_command(share)
commands.asset.add_command(share)

commands.widget.add_command(create)
commands.microservice.add_command(create)
commands.app_builder.add_command(create)
commands.asset.add_command(create)

commands.widget.add_command(delete)
commands.microservice.add_command(delete)
commands.app_builder.add_command(delete)

commands.widget.add_command(update)
commands.microservice.add_command(update)
commands.app_builder.add_command(update)
commands.asset.add_command(update)
