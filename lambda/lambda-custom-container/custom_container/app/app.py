#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
#vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import json
import os

print("$ whereis java")
os.system("whereis java")

print("$ readlink -f /usr/bin/java")
os.system("readlink -f /usr/bin/java")

print(f"\nJAVA_HOME={os.getenv('JAVA_HOME', 'Non-exist')}")

def lambda_handler(event, context):
  from konlpy.tag import Komoran

  komoran = Komoran()
  print("\nKomoran.morphs:")
  print(komoran.morphs(u'우왕 코모란도 오픈소스가 되었어요'))

  # TODO implement
  return {
    'statusCode': 200,
    'body': json.dumps('Hello from Lambda!')
  }


if __name__ == '__main__':
  lambda_handler({}, None)

