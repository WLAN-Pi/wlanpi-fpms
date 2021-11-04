import tarfile
import hashlib
import shutil
import click
import gzip
import os

class Tarsum:
  def __init__(self, target_dir=None):
    self.target_dir = target_dir
    if not self.target_dir:
      self.target_dir = os.getcwd()

  def tar_working_dir(self):
    cwd = self.target_dir
    self.make_tarfile('test.tar.gz', cwd)
    tarfile_path = f'{cwd}/test.tar.gz'

    return tarfile_path

  def check_file(self):
    tarfile_path = self.tar_working_dir()
    stat = os.stat(tarfile_path)
    click.echo("Zipped tarfile size")
    click.echo(stat.st_size)

    checksum = self.get_checksum(tarfile_path)
    click.echo(checksum)

  def get_checksum(self, file_path):
    hash_md5 = hashlib.md5()

    with open(file_path, "rb") as f:
      for chunk in iter(lambda: f.read(4096), b""):
        hash_md5.update(chunk)

    return hash_md5.hexdigest()

  def gzip_file(self, file_path, file_name):
    with open(f'{file_path}/{file_name}', 'rb') as f_in:
      with gzip.open(f'{file_path}/{file_name}.gz', 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)

    click.echo(dir(f_out))

  def make_tarfile(self, output_filename, source_dir):
    def ignore_project_config(tarinfo):
      if '.lumavate' in tarinfo.path or '.git' in tarinfo.path:
        return None

      return tarinfo

    with tarfile.open(output_filename, "w:") as tar:
      tar.add(source_dir, arcname=os.path.basename(source_dir), filter=ignore_project_config)

    click.echo(dir(tar))
    click.echo(tar.fileobject)
    return tar
