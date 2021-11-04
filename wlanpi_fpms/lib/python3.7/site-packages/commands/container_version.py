import commands
import behavior
import click
import pyke

@click.command('add', help='Create a new version of a container')
@click.option('--profile', '-p', help=pyke.helptxt.PROFILE, callback=pyke.select_profile, autocompletion=pyke.auth.get_profile_names)
@click.option('--container', '-c', prompt=True)
@click.option('--port', type=int, help='The port to expose on your container')
@click.option('--editor-port', type=int, help="The port to connect to the container's editor")
@click.option('--is-editable', is_flag=True, help="Set if this is an editable container. Must come from a version with an editor port")
@click.option('--docker-image', '-image', type=str, help='The name (including the tag) of a docker image from the docker daemon. You must have docker running locally to use this option.')
@click.option('--container-file-path', '-path', type=click.Path(), help='The image must be a gzipped tar file. Ex: {file_name}.tar.gz')
@click.option('--from-version', '-fv', type=str, help=pyke.helptxt.FROM_VERSION)
@click.option('--version', '-v', type=str, default=None, help="The version number of the new version")
@click.option('--patch', 'version_bump', flag_value='patch', default=True)
@click.option('--minor', 'version_bump', flag_value='minor')
@click.option('--major', 'version_bump', flag_value='major')
@click.option('--env', '-e', default=None, multiple=True, help="The environment variables to add to the docker image when it is run -- Syntax: envVar=value")
@click.option('--label', '-l', type=click.Choice(['prod', 'dev', 'old']))
@click.option('--format', '-f', default='{id} {actualState} {versionNumber} {label} {isEditable} {createdAt}', help=pyke.helptxt.FORMAT)
@click.option('--json', is_flag=True, help='Return raw json from the platform')
def create(**kwargs):
  behavior.ContainerVersionBehavior(**kwargs).create()

@click.command('ls', help='List versions for a container')
@click.option('--profile', '-p', help=pyke.helptxt.PROFILE, callback=pyke.select_profile, autocompletion=pyke.auth.get_profile_names)
@click.option('--container', '-c', prompt=True)
@click.option('--format', '-f', default='{id} {actualState} {versionNumber} {label} {isEditable} {createdAt}', help=pyke.helptxt.FORMAT)
@click.option('--filter', default='')
@click.option('--page', default=1)
@click.option('--pagesize', default=100)
@click.option('--json', is_flag=True, help='Return raw json from the platform')
def list(**kwargs):
  behavior.ContainerVersionBehavior(**kwargs).list()

@click.command('start', help='Start a container version')
@click.option('--profile', '-p', help=pyke.helptxt.PROFILE, callback=pyke.select_profile, autocompletion=pyke.auth.get_profile_names)
@click.option('--container', '-c', prompt=True)
@click.option('--version', '-v', prompt=True, help='The version ID or the version-number')
@click.option('--format', '-f', default='{id} {actualState} {versionNumber} {createdAt}', help=pyke.helptxt.FORMAT)
@click.option('--json', is_flag=True, help='Return raw json from the platform')
def start(**kwargs):
  behavior.ContainerVersionBehavior(**kwargs).start_stop()

@click.command('stop', help='Stop a container version')
@click.option('--profile', '-p', help=pyke.helptxt.PROFILE, callback=pyke.select_profile, autocompletion=pyke.auth.get_profile_names)
@click.option('--container', '-c', prompt=True)
@click.option('--version', '-v', prompt=True, help='The version ID or the version-number')
@click.option('--format', '-f', default='{id} {actualState} {versionNumber} {createdAt}', help=pyke.helptxt.FORMAT)
@click.option('--json', is_flag=True, help='Return raw json from the platform')
def stop(**kwargs):
  behavior.ContainerVersionBehavior(**kwargs).start_stop()

@click.command('exec', help='Pass in a command to be run directly on the docker container.')
@click.argument('command')
@click.option('--profile', '-p', help=pyke.helptxt.PROFILE, callback=pyke.select_profile, autocompletion=pyke.auth.get_profile_names)
@click.option('--container', '-c', prompt=True)
@click.option('--version', '-v', prompt=True, help='The version ID or the version-number')
@click.option('--json', is_flag=True, help='Return raw json from the platform')
def run(command, **kwargs):
  behavior.ContainerVersionBehavior(**kwargs).run(command)

@click.command(help='Update a container version')
@click.option('--profile', '-p', help=pyke.helptxt.PROFILE, callback=pyke.select_profile, autocompletion=pyke.auth.get_profile_names)
@click.option('--container', '-c', prompt=True)
@click.option('--version', '-v', prompt=True, help='The version ID or the version-number')
@click.option('--label', '-l', prompt=True)
@click.option('--format', '-f', default='{id} {versionNumber} {label} {isEditable} {createdAt}', help=pyke.helptxt.FORMAT)
@click.option('--json', is_flag=True, help='Return raw json from the platform')
def update(**kwargs):
  behavior.ContainerVersionBehavior(**kwargs).update()

@click.command('rm', help='Delete a container version')
@click.option('--profile', '-p', help=pyke.helptxt.PROFILE, callback=pyke.select_profile, autocompletion=pyke.auth.get_profile_names)
@click.option('--container', '-c', prompt=True)
@click.option('--version', '-v', prompt=True, help='The version ID, the version number or a version mask')
@click.option('--format', '-f', default='{id} {versionNumber} {label} {isEditable} {createdAt}', help=pyke.helptxt.FORMAT)
@click.option('--json', is_flag=True, help='Return raw json from the platform')
def delete(**kwargs):
  behavior.ContainerVersionBehavior(**kwargs).delete()

@click.command('logs', help='Tail logs for an editable container')
@click.option('--profile', '-p', help=pyke.helptxt.PROFILE, callback=pyke.select_profile, autocompletion=pyke.auth.get_profile_names)
@click.option('--container', '-c', prompt=True, help='The ID or the url-ref of the container associated with the editable version')
@click.option('--version', '-v', prompt=True, help='The version ID or the version-number')
@click.option('--tail-number', '-n', type=int, help='The number of lines to show')
@click.option('--editor', is_flag=True, help='Return raw json from the platform')
def tail(editor, **kwargs):
  tn = kwargs.get('tail_number')
  if not tn or tn < 1:
    tn = 100

  if editor:
    behavior.ContainerVersionBehavior(**kwargs).run(f"tail /logs/editor.log -n {tn}")
  else:
    behavior.ContainerVersionBehavior(**kwargs).run(f"tail /logs/app.log -n {tn}")

@click.command('editorInfo', help='Get version info from the editor')
@click.option('--profile', '-p', help=pyke.helptxt.PROFILE, callback=pyke.select_profile, autocompletion=pyke.auth.get_profile_names)
@click.option('--container', '-c', prompt=True, help='The ID or the url-ref of the container associated with the editable version')
@click.option('--version', '-v', prompt=True, help='The version ID or the version-number')
@click.option('--tail-number', '-n', type=int, help='The number of lines to show')
def editor_info(**kwargs):
  behavior.ContainerVersionBehavior(**kwargs).editor_info()

@click.command(help='This force updates your docker service. This can recover a process in a bad state')
@click.option('--profile', '-p', help=pyke.helptxt.PROFILE, callback=pyke.select_profile, autocompletion=pyke.auth.get_profile_names)
@click.option('--container', '-c', prompt=True, help='The ID or the url-ref of the container associated with the editable version')
@click.option('--version', '-v', prompt=True, help='The version ID or the version-number')
def restart(**kwargs):
  behavior.ContainerVersionBehavior(**kwargs).force_update()

@click.command('download', help='Download a zip file that contains this containers application source code')
@click.option('--profile', '-p', help=pyke.helptxt.PROFILE, callback=pyke.select_profile, autocompletion=pyke.auth.get_profile_names)
@click.option('--container', '-c', prompt=True, help='The ID or the url-ref of the container associated with the editable version')
@click.option('--version', '-v', prompt=True, help='The version ID or the version-number')
@click.option('--path', '-path', type=click.Path(), help='Path to save zip file')
def download_app_zip(**kwargs):
  behavior.ContainerVersionBehavior(**kwargs).download_app_zip()


commands.microservice_version.add_command(create)
commands.widget_version.add_command(create)
commands.app_builder_version.add_command(create)
commands.asset_version.add_command(create)

commands.microservice_version.add_command(list)
commands.widget_version.add_command(list)
commands.app_builder_version.add_command(list)
commands.asset_version.add_command(list)

commands.microservice_version.add_command(start)
commands.widget_version.add_command(start)
commands.app_builder_version.add_command(start)
commands.asset_version.add_command(start)

commands.microservice_version.add_command(stop)
commands.widget_version.add_command(stop)
commands.app_builder_version.add_command(stop)
commands.asset_version.add_command(stop)

commands.microservice_version.add_command(delete)
commands.widget_version.add_command(delete)
commands.app_builder_version.add_command(delete)
commands.asset_version.add_command(delete)

commands.microservice_version.add_command(update)
commands.widget_version.add_command(update)
commands.app_builder_version.add_command(update)
commands.asset_version.add_command(update)

commands.microservice_version.add_command(run)
commands.widget_version.add_command(run)
commands.app_builder_version.add_command(run)
commands.asset_version.add_command(run)

commands.microservice_version.add_command(download_app_zip)
commands.widget_version.add_command(download_app_zip)
commands.app_builder_version.add_command(download_app_zip)
commands.asset_version.add_command(download_app_zip)

commands.microservice_version.add_command(restart)
commands.widget_version.add_command(restart)
commands.app_builder_version.add_command(restart)
commands.asset_version.add_command(restart)

commands.microservice_version.add_command(tail)
commands.widget_version.add_command(tail)
commands.app_builder_version.add_command(tail)
commands.asset_version.add_command(tail)

commands.microservice_version.add_command(editor_info)
commands.widget_version.add_command(editor_info)
commands.app_builder_version.add_command(editor_info)
commands.asset_version.add_command(editor_info)
