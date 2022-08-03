#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import sys
import traceback

try:
  from elasticsearch import Elasticsearch
  from elasticsearch import RequestsHttpConnection
except ImportError as ex:
  print('[ERROR] Fail to import elasticsearch')
  print('[ERROR] sys.path:\n', '\n'.join(sys.path))
  traceback.print_exec()
  raise ex


def lambda_handler(event, context):
  print('[INFO] sys.path:\n', '\n'.join(sys.path))


if __name__ == '__main__':
  event = {}
  lambda_handler(event, {})
