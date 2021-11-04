from .menu import Menu
from .auth import auth
import pyke
import click

class LumaCommand(click.Command):
  """
  Currently not used. Experimental override of defualt click command to add auth
  """
  def __init__(self, *args, **kwargs):
    ctx = self.make_context(kwargs.get('name'), list(args))
    do_auth = kwargs.get('auth')
    if do_auth is None or do_auth is True:
      profile_option = click.Option(['--profile', '-p'], help='The name of the profile to use as the context for the command.', autocompletion=auth.get_profile_names)
      ctx.params.update(profile_option)
    if do_auth is not None:
      del kwargs['auth']

    if 'profile' in ctx.params.keys():
      profile_name = ctx.params['profile']
      if not profile_name:
        profiles = auth.list_profiles()
        profile_data = Menu().get_user_select(profiles, format, sort='profileName')
        profile_name = profile_data.get('profileName')
      else:
        profile_data = auth.get_profile_data(profile_name)

      env_name = profile_data.get('env')
      env_data = Menu().sanatize_data(auth.get_env_data(env_name))

      ctx.obj = {**profile_data, **env_data}
      ctx.invoke(self.callback, *args, **kwargs)

def select_profile(ctx, param, value):
  profiles = auth.list_profiles()
  profile_names = [x.get('profileName') for x in profiles]
  if not value:
    format = "{Option} {profileName} {env} {orgName} {orgId}"
    titles = {"profileName": "Profile Name", "env": "Env", "orgName": "Org Name", "orgId": "Org ID"}
    profile_data = Menu().get_user_select(profiles, format, sort='profileName', titles=titles)
  else:
    if value not in profile_names:
      raise click.BadParameter(click.style('You must provide the name of a profile that you have configured', fg='red'))

    # Use this to update old profiles
    profile_data = auth.get_profile_data(value)
    if 'profileName' not in profile_data.keys():
      profile_data['profileName'] = value
      auth.update_profile(value, profile_data)

    if profile_data.get('orgId') is None or profile_data.get('orgId') == '':
      raise click.BadParameter(click.style('You must finish configuring this profile before you can use it', fg='red'))

  env_name = profile_data.get('env')
  env_data = Menu().sanatize_data(auth.get_env_data(env_name))

  ctx.obj = {**profile_data, **env_data}

  return pyke.Util(ctx=ctx.obj)
