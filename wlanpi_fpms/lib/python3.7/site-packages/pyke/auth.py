"""
    The auth class is resposible for storing, reading and updating tokens and config settings.
    The CLI should cache tokens until a new one is required. If that's the case the auth class
    retrieves the config variables so a new token can be requested from the platform. Upon success
    the new token is cached and used for subsequent commandsself.
"""

from functools import wraps
from pathlib import Path
import dateutil.parser
from .menu import Menu
import functools
import click
import copy
import json
import os


class auth:

  @staticmethod
  def list_profiles():
    profile_data = auth.load_config().get('profiles')
    for profile_name in profile_data.keys():
      # Migrate to new authUrl
      if 'experienceCloudUri' in profile_data[profile_name].keys() and 'authUri' not in profile_data[profile_name].keys():
        auth_uri = profile_data[profile_name].get('experienceCloudUri').replace('experience', 'auth')
        auth.update_profile(profile_name, {'authUri': auth_uri})

      profile_data[profile_name]['profileName'] = profile_name

    profiles = [profile_data.get(k) for k in profile_data.keys()]
    return profiles

  @staticmethod
  def list_envs():
    env_data = auth.load_config().get('envs')
    for env_name in env_data.keys():
      env_data[env_name]['envName'] = env_name

    envs = [env_data.get(k) for k in env_data.keys()]
    return envs

  @staticmethod
  def update_profile(name, profile_data):
    config = auth.load_config()
    profiles = config['profiles']

    if profiles.get(name):
      profiles[name].update(profile_data)
    else:
      profiles[name] = profile_data

    auth.save_config(config)
    return config

  @staticmethod
  def get_profile(config_data, name):
    return config_data['profiles'].get(name)

  @staticmethod
  def get_profile_data(key):
    config_data = auth.load_config()
    profile_data = config_data['profiles'].get(key)
    return Menu().sanatize_data(profile_data)

  @staticmethod
  def get_env_data(key):
    config_data = auth.load_config()
    env_data = config_data['envs'].get(key)
    if not env_data:
      raise click.ClickException(click.style(f"Could not find an environment named {key}", fg="red"))
    env_data['envName'] = key
    return Menu().sanatize_data(env_data)

  @staticmethod
  def get_env(config_data, name):
    return config_data['envs'].get(name)

  @staticmethod
  def get_profile_names(ctx, args, incomplete):
    config = auth.load_config()
    names = config['profiles'].keys()
    return [k for k in names if incomplete in k]

  @staticmethod
  def sanatize_data(data):
    skip = ['orgName', 'env', 'envName']
    return { k:v.replace(" ", "") if isinstance(v, str) and k not in skip else v for k,v in data.items() }

  @staticmethod
  def set_profile_token(profile, token):
    profile_data = auth.get_profile_data(profile)
    profile_data['accessToken'] = token
    auth.update_profile(profile, profile_data)

  @staticmethod
  def save_config(data):
    for k in data['envs'].keys():
      data['envs'][k] = auth.sanatize_data(data['envs'][k])

    with open(auth.get_config_file(), 'w+') as outfile:
      json.dump(data, outfile, indent=4, sort_keys=True)

  @staticmethod
  def load_config():
    config_path = auth.get_config_file()
    try:
      with open(config_path) as json_file:
        data = json.load(json_file)
      return data
    except Exception as e:
      raise click.ClickException(click.style('Bad config file found. Please manually fix your congif. Path: {}'.format(config_path), fg='red'))

  @staticmethod
  def get_config_file():
    config_path = f"{Path.home()}/.luma/luma_cli_config.json"
    if not os.path.exists(config_path):
      with open(config_path, 'w') as config:
        json.dump({ "envs": {}, "profiles": {} }, config)

    return config_path
