"""
    These sub-commands and their corresponding logic are both implamented in this file.
    TO DO: Break out the logic for these commands into a seperate behavior file.
"""

from pathlib import Path
import requests
import urllib3
import click
import pyke
import json
import os

verify_tls = os.environ.get('LUMA_CLI_VERIFY_TLS', None)
if verify_tls == 'false' or verify_tls == 'False':
  verify_tls = False
  urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
else:
  verify_tls = None

@click.group('org', help='Get information about Orgs such as parent-child org relationships')
def organization():
  pass

@click.command('ls', help="List the Orgs you can make profiles for. \
The 'isTest' column in the returned table indicates if a studio is a test org or a prod org.")
@click.option('--env', help='The Env to point to')
@click.option('--format', '-f', default='{id} {name} {instanceType} {isTest}', help='The --format option takes the column name of the returned table wrapped in \
{} and returns only that column. It is not compatible with --json flag.')
@click.option('--filter', default='')
@click.option('--json', 'json_flag', is_flag=True, help='Return raw json from the platform.')
def list(env, format, filter, json_flag):
  handlers = {
    'instanceType': lambda x: 'dev' if x == 'cc' else x
  }

  if 'instanceType=dev' in filter:
    filter = filter.replace('instanceType=dev', 'instanceType=cc')

  if 'isTest=None' in filter:
    filter = filter.replace('isTest=None', 'instanceType=cc')
  
  env_format = '{envName} {app}'
  titles = {'envName': 'Env Name', 'app': 'App'}

  if not env:
    envs = pyke.auth.list_envs()
    env_data = pyke.Menu().get_user_select(envs, env_format, titles=titles)
  else:
    env_data = pyke.auth.get_env_data(env)

  util = pyke.Util(ctx=env_data)

  access_token = util.login_without_context()
  util.ctx.update({'accessToken': access_token})

  headers = {
      'Authorization': 'Bearer ' + access_token,
      'Content-Type': 'application/json'
  }

  app_name = env_data.get('app')
  if not app_name:
    raise click.ClickException(click.style("Env not configured", fg='red'))

  resp = requests.get('{}/auth/v1/me/companies?sort=name&{}'.format(app_name, filter), headers=headers, verify=verify_tls)

  if json_flag:
      click.echo(resp.text)
      return

  pyke.Menu().print_menu(resp.json()['payload']['data'], format, handlers=handlers)

@click.command('child-orgs', help='List the Orgs that a parent Org can share objects with')
@click.option('--profile', '-p', help=pyke.helptxt.PROFILE, callback=pyke.select_profile, autocompletion=pyke.auth.get_profile_names)
@click.option('--format', '-f', default='{id} {name} {instanceType} {isTest}', help='The --format option takes the column name of the returned table wrapped in \
{} and returns only that column. It is not compatible with --json flag.')
@click.option('--filter', default='')
@click.option('--json', 'json_flag', is_flag=True, help='Return raw json from the platform.')
def child_companies(profile, format, filter, json_flag):
  util = pyke.Util()

  if 'instanceType=dev' in filter:
    filter = filter.replace('instanceType=dev', 'instanceType=cc')

  if 'isTest=None' in filter:
      filter = filter.replace('isTest=None', 'instanceType=cc')

  handlers = {
    'instanceType': lambda x: 'dev' if x == 'cc' else x
  }

  resp = util.cli_request('GET',
    util.build_url('{app}/auth/v1/company/child-companies?{filter}', {'filter': filter}))

  if json_flag:
    click.echo(json.dumps(resp))
    return

  util.print_table(resp['payload']['data'], format, handlers=handlers)

organization.add_command(list)
organization.add_command(child_companies)
