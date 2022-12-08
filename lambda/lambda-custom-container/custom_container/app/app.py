#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
#vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import json
import os

os.system("whereis java")
os.system("readlink -f /usr/bin/java")
print("JAVA_HOME=", os.getenv("JAVA_HOME", "Not exist"))

def lambda_handler(event, context):
  from konlpy.tag import Komoran

  komoran = Komoran()
  print(komoran.morphs(u'우왕 코모란도 오픈소스가 되었어요'))

  # TODO implement
  return {
    'statusCode': 200,
    'body': json.dumps('Hello from Lambda!')
  }


if __name__ == '__main__':
  lambda_handler({}, None)

