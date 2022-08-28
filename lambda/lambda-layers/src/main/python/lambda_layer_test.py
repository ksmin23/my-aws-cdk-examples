#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import sys
import os
import traceback

try:
  from elasticsearch import Elasticsearch
  from elasticsearch import RequestsHttpConnection
except ImportError as ex:
  print('[ERROR] {}'.format(ex))
  print('[ERROR] sys.path:\n', '\n'.join(sys.path))
  traceback.print_exc()
  raise ex

try:
  from pytz import timezone
  import pytz
except ImportError as ex:
  print('[ERROR] {}'.format(ex))
  print('[ERROR] sys.path:\n', '\n'.join(sys.path))
  traceback.print_exc()
  raise ex


def lambda_handler(event, context):
  print('[INFO] sys.path:\n', '\n'.join(sys.path))

  PACKAGES = ['elasticsearch', 'pytz']
  for each in sys.path:
    try:
      with os.scandir(each) as it:
        for entry in it:
          if entry.name in PACKAGES:
            print('[INFO] {}\t{}'.format(entry.name, each))
    except FileNotFoundError as ex:
      pass


if __name__ == '__main__':
  event = {}
  lambda_handler(event, {})

