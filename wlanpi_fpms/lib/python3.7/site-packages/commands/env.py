"""
    These sub-commands and their corresponding logic are both implamented in this file.
    TO DO: Break out the logic for these commands into a seperate behavior file.
"""

from pathlib import Path
import click
import pyke
import json
import os

@click.group(help='An environment tells the CLI where to get valid tokens for calls to the platform. \
Environments are analogous to auth realms.')
def env():
    pass

@click.command('config')
@click.option('--env-name', prompt=True, help='The environment name')
@click.option('--app', prompt=True, help='The App URL')
@click.option('--token', prompt=True, help='The URL for auth tokens')
@click.option('--audience', prompt=True)
@click.option('--client-id', prompt=True)
@click.option('--client-secret', prompt=True)
@click.option('--json', 'json_flag', is_flag=True, help='Return raw json from the platform.')
def config(app, token, audience, client_id, client_secret, env_name, json_flag):
    config_data = pyke.auth.load_config()

    env_data = {
      'app': app,
      'token': token,
      'audience': audience,
      'clientId': client_id,
      'clientSecret': client_secret
    }
    util = pyke.Util(env_data)

    config_data['envs'][env_name] = env_data
    util.login_without_context()
    pyke.auth.save_config(config_data)

    if json_flag:
        click.echo(json.dumps(config_data))
        return
    else:
        util.print_table(pyke.auth.list_envs(), '{envName} {app} {audience} {token}')

@click.command('ls')
@click.option('--format', '-f', default='{envName} {app} {audience} {token}', help='The --format option takes the column name of the returned table wrapped in \
{} and returns only that column. It is not compatible with --json flag.')
@click.option('--json', 'json_flag', is_flag=True, help='Return raw json.')
def list(format, json_flag):
    config = pyke.auth.load_config()

    data = []
    for key in config['envs'].keys():
        config['envs'][key]['envName'] = str(key)
        data.append(config['envs'][key])

    if json_flag:
        click.echo(json.dumps(config['envs']))
        return

    pyke.Util().print_table(data, format)

@click.command('rm')
@click.argument('env_name')
@click.option('--force', is_flag=True, help='Skip input and delete all profiles using the environment being deleted')
def delete(env_name, force):
    config_data = pyke.auth.load_config()

    env_data = pyke.auth.get_env_data(env_name)
    del config_data["envs"][env_name]

    profiles = config_data['profiles']
    profiles_to_del = []
    for profile in profiles:
      if profiles[profile].get('env') == env_name:
        profiles_to_del.append(profile)

    if len(profiles_to_del) > 0:
      click.echo(click.style("The following profiles are using this environment. Would you like to delete these profiles?", fg='white'))
      click.echo(click.style(str(profiles_to_del), fg='yellow'))
      click.echo(' ')

      if not force:
        try:
          cascade = input("Yes/No: ")
          cascade = str(cascade).lower()
        except:
          raise click.ClickException(click.style("The CLI expects either a 'Yes' or a 'No' as input", fg='red'))

        truthy_input = ['y', 'yes', 'true']
        if cascade in truthy_input:
          for profile in profiles_to_del:
            del config_data['profiles'][profile]

          if len(profiles_to_del) > 0:
            click.echo(' ')
            click.echo(click.style("Deleted profiles: {}".format(profiles_to_del), fg='white'))
          else:
            click.echo(' ')
            click.echo(click.style("No associated profiles", fg='white'))

      else:
        for profile in profiles_to_del:
          del config_data['profiles'][profile]

        if len(profiles_to_del) > 0:
          click.echo(' ')
          click.echo(click.style("Deleted profiles: {}".format(profiles_to_del), fg='white'))
        else:
          click.echo(' ')
          click.echo(click.style("No associated profiles", fg='white'))

    pyke.auth.save_config(config_data)
    click.echo(click.style("Deleted Environment: {}".format(env_name), fg='white'))


env.add_command(config)
env.add_command(list)
env.add_command(delete)
