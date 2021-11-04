"""
    The primary use of the ContainerUtil class is to connect to and communicate with
    the running docker daemon.
"""

from pathlib import Path
import docker
import shutil
import click
import gzip
import time
import sys
import os

class ContainerUtil:
  def __init__(self):
    try:
      self.client = docker.DockerClient(base_url='unix://var/run/docker.sock')
    except Exception as e:
      click.echo(click.style("When this error happens it's usualy because Docker is not running, OR there are leftover \
        references to the pip docker-py package on the machine.", fg='yellow'))
      click.echo(click.style("If it's the latter, make sure to remove all references of docker-py. \
        These can often persist in multiple versions of python on your machine even after a pip uninstall.", fg='yellow'))
      click.echo(" ")
      raise click.ClickException(click.style("Error communicating with the docker daemon. {}".format(e), fg='red'))

  def save_image(self, image_name):
    try:
      image = self.client.images.get(image_name)
    except Exception as e:
      raise Exception(click.style('Error getting image: {}'.format(e), fg='red'))

    file_path = '{}/{}'.format(str(Path.home()), image_name.replace('/', '_').replace('.', '_').replace(':', '_'))

    with open(file_path, 'wb') as image_tar:
      for chunk in image.save(named=True):
        image_tar.write(chunk)

    zipped_file_path = self.zip_image(file_path)

    # Cleanup
    os.remove(file_path)

    return zipped_file_path

  def zip_image(self, file_path):
    with open(file_path, 'rb') as f_in:
      with gzip.open('{}.tar.gz'.format(file_path), 'w+b') as f_out:
        shutil.copyfileobj(f_in, f_out)

    return '{}.tar.gz'.format(file_path)

