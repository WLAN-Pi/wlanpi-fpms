"""
    These sub-commands and their corresponding logic are both implamented in this file.
    TO DO: Break out the logic for these commands into a seperate behavior file.
"""

import behavior
import click
import json
import pyke

@click.group(help='All api subcommands take one url argument. This is the relative path. The CLI will handle your app name and the auth headers. \
For example, to GET all containers (a combination of widgets and microservices) the command would be < luma api get /iot/v1/containers >. \
For PUT and POST commands there is a --data option. The value for --data must be valid json.')
def api():
    pass

@click.command()
@click.argument('url')
@click.option('--profile', '-p', help=pyke.helptxt.PROFILE, callback=pyke.select_profile, autocompletion=pyke.auth.get_profile_names)
def get(url, profile):
    util = pyke.Util(profile=profile)

    if url.startswith('/auth'):
      resp = util.cli_request('GET',
          util.build_url('{authUri}{url}', {'url': url}))
    else:
      resp = util.cli_request('GET',
          util.build_url('{experienceCloudUri}{url}', {'url': url}))

    click.echo(json.dumps(resp))

@click.command()
@click.argument('url')
@click.option('--profile', '-p', help=pyke.helptxt.PROFILE, callback=pyke.select_profile, autocompletion=pyke.auth.get_profile_names)
@click.option('--data', '-d', help='Must be valid json surrounded by single quotes. Will be sent as the payload for the request.')
def put(url, profile, data):
    util = pyke.Util(profile=profile)

    req_data = serialize_data(data)

    if url.startswith('/auth'):
      resp = util.cli_request('PUT',\
          util.build_url('{authUri}{url}', {'url': url}), data=json.dumps(req_data))
    else:
      resp = util.cli_request('PUT',\
          util.build_url('{experienceCloudUri}{url}', {'url': url}), data=json.dumps(req_data))

    click.echo(json.dumps(resp))

@click.command()
@click.argument('url')
@click.option('--profile', '-p', help=pyke.helptxt.PROFILE, callback=pyke.select_profile, autocompletion=pyke.auth.get_profile_names)
@click.option('--data', '-d', help='Must be valid json surrounded by single quotes. Will be sent as the payload for the request.')
def post(url, profile, data):
    util = pyke.Util(profile=profile)

    req_data = serialize_data(data)

    if url.startswith('/auth'):
      resp = util.cli_request('POST',\
          util.build_url('{authUri}{url}', {'url': url}), data=json.dumps(req_data))
    else:
      resp = util.cli_request('POST',\
          util.build_url('{experienceCloudUri}{url}', {'url': url}), data=json.dumps(req_data))

    click.echo(json.dumps(resp))

@click.command()
@click.argument('url')
@click.option('--profile', '-p', help=pyke.helptxt.PROFILE, callback=pyke.select_profile, autocompletion=pyke.auth.get_profile_names)
def delete(url, profile):
    util = pyke.Util(profile=profile)

    if url.startswith('/auth'):
      resp = util.cli_request('DELETE',
          util.build_url('{authUri}{url}', {'url': url}))
    else:
      resp = util.cli_request('DELETE',
          util.build_url('{experienceCloudUri}{url}', {'url': url}))

    click.echo(json.dumps(resp))

api.add_command(get)
api.add_command(put)
api.add_command(post)
api.add_command(delete)

def serialize_data(data):
    req_data = {}
    if not data:
      raise click.ClickException(click.style("You must provide --data for this command.", fg='red'))

    for var in data:
        try:
            data_dict = json.loads(data)
            req_data = { **req_data, **data_dict}
        except Exception as e:
            click.echo("Could not serialize data")
            click.echo(e)

    return req_data
