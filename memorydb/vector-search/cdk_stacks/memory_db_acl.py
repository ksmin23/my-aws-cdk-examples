#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import json
import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_memorydb,
  aws_secretsmanager
)
from constructs import Construct


class MemoryDBAclStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    MEMORYDB_USER_NAME = self.node.try_get_context('memorydb_user_name') or 'memdb-admin'

    memorydb_secret = aws_secretsmanager.Secret(self, 'MemoryDBSecret',
      generate_secret_string=aws_secretsmanager.SecretStringGenerator(
        secret_string_template=json.dumps({"username": MEMORYDB_USER_NAME}),
        generate_string_key="password",
        exclude_punctuation=True,
        password_length=16
      )
    )

    memorydb_user = aws_memorydb.CfnUser(self, 'MemoryDBUser',
      # user_name=MEMORYDB_USER_NAME,
      user_name=memorydb_secret.secret_value_from_json("username").unsafe_unwrap(),
      # refer to https://redis.io/topics/acl
      access_string='on ~* &* +@all',
      # refer to https://docs.aws.amazon.com/cli/latest/reference/memorydb/create-user.html
      authentication_mode={
        "Type": "password",
        "Passwords": [memorydb_secret.secret_value_from_json("password").unsafe_unwrap()]
      }
    )

    self.memorydb_acl = aws_memorydb.CfnACL(self, 'MemoryDBAcl',
      acl_name=f'memorydb-acl-for-{self.stack_name.lower()}',
      user_names=[memorydb_user.user_name]
    )
    self.memorydb_acl.add_dependency(memorydb_user)


    cdk.CfnOutput(self, 'MemoryDBSecretName',
      value=memorydb_secret.secret_name,
      export_name=f'{self.stack_name}-MemoryDBSecretName')
    cdk.CfnOutput(self, 'MemoryDBACL',
      value=self.memorydb_acl.acl_name,
      export_name=f'{self.stack_name}-MemoryDBACL')
