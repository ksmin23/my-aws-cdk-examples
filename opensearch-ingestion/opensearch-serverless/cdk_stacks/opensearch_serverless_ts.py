#!/usr/bin/env python3
import json

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_opensearchserverless as aws_opss
)
from constructs import Construct


class OpsServerlessTimeSeriesStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, pipeline_role_arn, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    USER_NAME = self.node.try_get_context('iam_user_name')
    collection_name = self.node.try_get_context('collection_name') or "ingestion-collection"

    network_security_policy = json.dumps([{
      "Rules": [
        {
          "Resource": [
            f"collection/{collection_name}"
          ],
          "ResourceType": "dashboard"
        },
        {
          "Resource": [
            f"collection/{collection_name}"
          ],
          "ResourceType": "collection"
        }
      ],
      "AllowFromPublic": True
    }], indent=2)

    #XXX: max length of policy name is 32
    network_security_policy_name = f"{collection_name}-net-policy"
    assert len(network_security_policy_name) <= 32

    cfn_network_security_policy = aws_opss.CfnSecurityPolicy(self, "NetworkSecurityPolicy",
      policy=network_security_policy,
      name=network_security_policy_name,
      type="network"
    )

    encryption_security_policy = json.dumps({
      "Rules": [
        {
          "Resource": [
            f"collection/{collection_name}"
          ],
          "ResourceType": "collection"
        }
      ],
      "AWSOwnedKey": True
    }, indent=2)

    #XXX: max length of policy name is 32
    encryption_security_policy_name = f"{collection_name}-encr-policy"
    assert len(encryption_security_policy_name) <= 32

    cfn_encryption_security_policy = aws_opss.CfnSecurityPolicy(self, "EncryptionSecurityPolicy",
      policy=encryption_security_policy,
      name=encryption_security_policy_name,
      type="encryption"
    )

    cfn_collection = aws_opss.CfnCollection(self, "OpssTSCollection",
      name=collection_name,
      description="Collection to be used for time-series analysis using OpenSearch Serverless",
      type="TIMESERIES" # [SEARCH, TIMESERIES]
    )
    cfn_collection.add_dependency(cfn_network_security_policy)
    cfn_collection.add_dependency(cfn_encryption_security_policy)

    data_access_policy = json.dumps([
      {
        "Rules": [
          {
            "Resource": [
              f"collection/{collection_name}"
            ],
            "Permission": [
              "aoss:CreateCollectionItems",
              "aoss:DeleteCollectionItems",
              "aoss:UpdateCollectionItems",
              "aoss:DescribeCollectionItems"
            ],
            "ResourceType": "collection"
          },
          {
            "Resource": [
              f"index/{collection_name}/*"
            ],
            "Permission": [
              "aoss:CreateIndex",
              "aoss:DeleteIndex",
              "aoss:UpdateIndex",
              "aoss:DescribeIndex",
              "aoss:ReadDocument",
              "aoss:WriteDocument"
            ],
            "ResourceType": "index"
          }
        ],
        "Principal": [
          f"{pipeline_role_arn}",
          f"arn:aws:iam::{cdk.Aws.ACCOUNT_ID}:user/{USER_NAME}"
        ],
        "Description": "data-access-rule"
      }
    ], indent=2)

    #XXX: max length of policy name is 32
    data_access_policy_name = f"{collection_name}-policy"
    assert len(data_access_policy_name) <= 32

    cfn_access_policy = aws_opss.CfnAccessPolicy(self, "OpssDataAccessPolicy",
      name=data_access_policy_name,
      description="Policy for data access",
      policy=data_access_policy,
      type="data"
    )

    self.collection_endpoint = cfn_collection.attr_collection_endpoint

    cdk.CfnOutput(self, f'{self.stack_name}-Endpoint', value=cfn_collection.attr_collection_endpoint)
    cdk.CfnOutput(self, f'{self.stack_name}-DashboardsURL', value=cfn_collection.attr_dashboard_endpoint)

