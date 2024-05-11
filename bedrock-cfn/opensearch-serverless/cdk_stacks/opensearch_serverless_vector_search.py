#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import json

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_opensearchserverless as aws_opss
)
from constructs import Construct


class OpsServerlessVectorSearchStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, kb_role_arn, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    collection_name = self.node.try_get_context('opensearch_collection_name')

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
    network_security_policy_name = f"{collection_name}-security-policy"
    assert len(network_security_policy_name) <= 32, f"Network Security Policy: {network_security_policy_name}"

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
    encryption_security_policy_name = f"{collection_name}-security-policy"
    assert len(encryption_security_policy_name) <= 32, f"Encryption Security Policy: {encryption_security_policy_name}"

    cfn_encryption_security_policy = aws_opss.CfnSecurityPolicy(self, "EncryptionSecurityPolicy",
      policy=encryption_security_policy,
      name=encryption_security_policy_name,
      type="encryption"
    )

    cfn_collection = aws_opss.CfnCollection(self, "OpssSearchCollection",
      name=collection_name,
      description="Collection to be used for vector search using OpenSearch Serverless",
      type="VECTORSEARCH" # [SEARCH, TIMESERIES, VECTORSEARCH]
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
          f"{kb_role_arn}"
        ],
        "Description": "data-access-rule"
      }
    ], indent=2)

    #XXX: max length of policy name is 32
    data_access_policy_name = f"{collection_name}-policy"
    assert len(data_access_policy_name) <= 32, f"Data Access Policy Name: {data_access_policy_name}"

    cfn_access_policy = aws_opss.CfnAccessPolicy(self, "OpssDataAccessPolicy",
      name=data_access_policy_name,
      description="Policy for data access",
      policy=data_access_policy,
      type="data"
    )

    self.opensearch_collection_arn = cfn_collection.attr_arn
    self.opensearch_collection_endpoint = cfn_collection.attr_collection_endpoint
    self.opensearch_data_access_policy_name = cfn_access_policy.name

    cdk.CfnOutput(self, 'OpenSearchEndpoint',
      # value=cfn_collection.attr_collection_endpoint,
      # https://{collection-id}.{region}.aoss.amazonaws.com
      value=self.opensearch_collection_endpoint,
      export_name=f'{self.stack_name}-OpenSearchEndpoint')
    cdk.CfnOutput(self, 'DashboardsURL',
      value=cfn_collection.attr_dashboard_endpoint,
      export_name=f'{self.stack_name}-DashboardsURL')
    cdk.CfnOutput(self, 'OpenSearchCollectionArn',
      value=self.opensearch_collection_arn,
      export_name=f'{self.stack_name}-OpenSearchCollectionArn')
    cdk.CfnOutput(self, 'DataAccessPolicyName',
      value=self.opensearch_data_access_policy_name,
      export_name=f'{self.stack_name}-DataAccessPolicyName')
