"""
    These sub-commands and their corresponding logic are both implamented in this file.
    TO DO: Break out the logic for these commands into a seperate behavior file.
"""

from pathlib import Path
import requests
import urllib3
import click
import json
import pyke
import sys
import os

verify_tls = os.environ.get('LUMA_CLI_VERIFY_TLS', None)
if verify_tls == 'false' or verify_tls == 'False':
  verify_tls = False
  urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
else:
  verify_tls = None

@click.group(help="Profiles add company context to commands. Almost all calls to Lumavate require context. \
Profiles use Envs to get tokens and then give those tokens context using the Org ID.")
def profile():
    pass

@click.command('ls', help="List the profiles you have configured.")
@click.option('--format', '-f', default='{profileName} {env} {orgName} {orgId}', help='The --format option takes the column name of the returned table wrapped in \
{} and returns only that column. It is not compatible with --json flag.')
@click.option('--json', 'json_flag', is_flag=True, help='Return raw json.')
def list(format, json_flag):
  profile_data = pyke.auth.list_profiles()
  if json_flag:
    click.echo(json.dumps(profile_data))
    return

  titles = {"profileName": "Profile Name", "env": "Env", "orgName": "Org Name", "orgId": "Org ID"}
  pyke.Menu().print_menu(profile_data, format, titles=titles)

@click.command()
@click.option('--profile-name', help='Profile Name')
@click.option('--env', default=None, help='The name of the environment you want to use with this profile')
@click.option('--format', '-f', default='{profileName} {env} {orgName} {orgId}', help='The available column names for this command are {env} {orgName} {orgId}')
def add(profile_name, env, format):
  if not profile_name:
    profile_name = click.prompt(click.style("Profile Name", fg="white"), type=str)

  click.echo(' ')

  titles = {
      'envName': 'Env Name',
      'app': 'App',
      'audience': 'Audience',
      'token': 'Token'
  }

  headers = '{envName} {app} {audience} {token}'

  if env:
    env_data = pyke.auth.get_env_data(env)
  else:
    envs = pyke.auth.list_envs()
    env_data = pyke.Menu().get_user_select(envs, headers, sort='envName', titles=titles)

  util = pyke.Util(ctx=env_data)

  titles = {
      'name': 'Org Name',
      'instanceType': 'Org Type',
      'isTest': 'Test Org'
    }
  headers = "{name} {instanceType} {isTest}"
  company = pyke.Menu().get_user_select(util.get_companies(), headers, sort='orgName', titles=titles)

  profile_data = {}
  profile_data["orgId"] = company.get('id')
  profile_data["orgName"] = company.get('name')
  profile_data["env"] = util.ctx.get('envName')
  profile_data["instanceType"] = company.get('instanceType')
  profile_data["profileName"] = profile_name

  pyke.auth.update_profile(profile_name, profile_data)
  util.ctx.update(profile_data)

  company_context = get_company_context(util.ctx).get('company')

  if company_context:
    profile_data = pyke.auth.get_profile_data(profile_name)
    profile_data['experienceCloudUri'] = company_context['experienceCloudUri']
    pyke.auth.update_profile(profile_name, profile_data)

  else:
    raise click.ClickException(click.style('Error getting company context', fg='red'))

  titles = {
      'profileName': 'Profile',
      'env': 'Environment',
      'orgName': 'Org Name',
      'orgId': 'Org ID'
  }

  pyke.Menu().print_menu([profile_data], format, titles=titles)

def get_company_context(ctx):
  util = pyke.Util(ctx=ctx)
  token_resp = util.login()
  headers = {
        'Authorization': 'Bearer ' + token_resp.get('access_token'),
        'Content-Type': 'application/json'
      }

  resp = requests.get(util.build_url('{app}/auth/v1/context'), headers=headers, verify=verify_tls)

  if resp.status_code == 200:
    return resp.json()['payload']['data']
  else:
    raise click.ClickException(click.style('Error getting company context', fg='red'))

@click.command('refresh-token', help="Refreshes the access token stored in the config - Adds 'experienceCloudUri' and 'instanceType' to the profile if they are not present." )
@click.option('--profile', '-p', help='Profile to refresh.', callback=pyke.select_profile, autocompletion=pyke.auth.get_profile_names)
def refresh_token(profile):
  profile.login()
  profile_name = profile.ctx.get('profileName')
  click.echo(f"Refreshed '{profile_name}' access token.")

  # Migration path for old profile data without experienceCloudUri
  if 'experienceCloudUri' not in profile.ctx.keys():
    company_context = get_company_context(profile.ctx).get('company')

    if company_context:
      profile_data = pyke.auth.get_profile_data(profile_name)
      profile_data['experienceCloudUri'] = company_context.get('experienceCloudUri')
      pyke.auth.update_profile(profile_name, profile_data)

  if 'instanceType' not in profile.ctx.keys():
    company_context = get_company_context(profile.ctx).get('company')

    if company_context:
      profile_data = pyke.auth.get_profile_data(profile_name)
      profile_data['instanceType'] = company_context.get('instanceType')
      pyke.auth.update_profile(profile_name, profile_data)

@click.command('rm')
@click.argument('profile')
def delete(profile):
  config_data = pyke.auth.load_config()
  profile_data = config_data["profiles"].get(profile)
  if not profile_data:
    raise click.ClickException(click.style(f"Could not find the profile {profile} to delete", fg='red'))

  del config_data["profiles"][profile]
  pyke.auth.save_config(config_data)
  click.echo(click.style(f"Deleted profile: {profile}", fg="white"))

profile.add_command(list)
profile.add_command(delete)
profile.add_command(add)
profile.add_command(refresh_token)
