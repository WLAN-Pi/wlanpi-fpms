from pyparsing import Literal, Word, nums, Combine, Optional,\
  delimitedList, oneOf, alphas, Suppress
import dateutil.parser
import click
import pyke
import re

ESC = Literal('\x1b')
integer = Word(nums)
escapeSeq = Combine(ESC + '[' + Optional(delimitedList(integer,';')) +
                oneOf(list(alphas)))

uncolor = lambda s : Suppress(escapeSeq).transformString(s)

class Menu:
  def __init__(self, json=False):
    self.json = json

  def camel_to_underscore(self, name):
    camel_pat = re.compile(r'([A-Z0-9])')
    click.echo(camel_pat.sub(lambda x: ' ' + x.group(1).lower(), name))
    return camel_pat.sub(lambda x: ' ' + x.group(1).lower(), name)

  def underscore_to_camelcase(self, value):
    def camelcase():
      yield str.lower
      while True:
        yield str.capitalize

    c = camelcase()
    return "".join(c.next()(x) if x else '_' for x in value.split("_"))

  def sanatize_data(self, data, skip=None):
    if not skip:
      skip = ['orgName', 'name']

    data = { k:v.replace(" ", "") if isinstance(v, str) and k not in skip else v.strip() if k == 'orgName' or k =='name' else v for k,v in data.items() }
    if 'Option' in data.keys():
      del data['Option']

    return data

  def _process_data(self, data, sort=None):
    if sort:
      data = sorted(data, key=lambda k: (sort not in k, k.get(sort, None)))

    # Add option Column
    ct = 1
    for rec in data:
      rec['Option'] = ct
      ct = ct + 1

    return data

  def get_user_select(self, data, format, sort=None, titles=None, skip=None):
    if '{Option}' not in format:
      format = '{Option} ' + format
    data = self._process_data(data, sort)
    data = self.print_menu(data, format, titles)
    return self._get_selection(data, skip=skip)

  def print_menu(self, data, format, titles={}, handlers={}):
    if not titles:
      titles = {}

    headers = {}
    stats = {}

    for c in data:
      child_records = {}
      for k in c:
        if isinstance(c[k], dict):
          for sk in c[k]:
            child_records[k + '__' + sk] = c[k][sk]

      c.update(child_records)

    if len(data) > 0:
      for k in data[0]:
        headers[k] = titles.get(k, k)
    else:
      click.echo('No Records Found')
      return

    for k in headers:
      stats[k] = len(uncolor(headers[k]))

    for c in data:
      for k in c:
        if k in ['createdAt', 'lastModifiedAt']:
          cd = dateutil.parser.parse(c[k])
          c[k] = cd.strftime('%x %X')
        if stats.get(k, 0) < len(str(uncolor(handlers[k](c[k])) if k in handlers else c[k])):
          stats[k] = len(str(uncolor(handlers[k](c[k])) if k in handlers else c[k]))

    for k in headers:
      headers[k] = titles.get(k, k).ljust(stats[k])

    for c in data:
      for k in c:
        c[k] = str(handlers[k](c[k]) if k in handlers else c[k])
        c[k] = c[k] + ' ' * (stats[k] - len(uncolor(c[k])))

    try:
      col_headers = format.format(**headers)
    except KeyError as ke:
      raise click.ClickException(click.style(f'You passed in a header that did not exsist in the response: {ke}', fg='red'))

    click.echo(click.style(col_headers, fg='white'))

    for c in data:
      click.echo(format.format(**c))

    click.echo(" ")

    return data

  def validate_num(self, val, min_val=None):
    try:
      int_val = int(val)
      if min_val:
        if int_val < min_val:
          raise click.ClickException(click.style(f"Expected an interger greater than {min_val} as input", fg='red'))

      return int_val

    except:
      if min_val:
        raise click.ClickException(click.style(f"Expected an interger greater than {min_val} as input", fg='red'))
      else:
        raise click.ClickException(click.style("Expected an interger as input", fg='red'))

  def _get_selection(self, data, skip=None):
    user_num = click.prompt(click.style("Enter the Option #", fg="white"), type=int)
    click.echo(' ')

    selection = None
    for rec in data:
      rec_num = rec.get('Option').strip()
      user_num = str(user_num).strip()

      if rec_num == user_num:
        selection = rec
        break

    if not selection:
      raise click.ClickException(click.style(f"{user_num} was not in the list of options", fg='red'))

    return self.sanatize_data(selection, skip=skip)
