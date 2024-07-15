#!/usr/bin/env python3
import os
import json
import random
import string

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_opensearchservice,
  aws_secretsmanager
)
from constructs import Construct

random.seed(47)


class OpensearchStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    OPENSEARCH_DEFAULT_DOMAIN_NAME = 'opensearch-{}'.format(''.join(random.sample((string.ascii_lowercase), k=5)))
    OPENSEARCH_DOMAIN_NAME = self.node.try_get_context("OpenSearchDomainName") or OPENSEARCH_DEFAULT_DOMAIN_NAME

    sg_opensearch_client = aws_ec2.SecurityGroup(self, "OpenSearchClientSG",
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for an opensearch client',
      security_group_name='use-opensearch-cluster-sg'
    )
    cdk.Tags.of(sg_opensearch_client).add('Name', 'use-opensearch-cluster-sg')

    sg_opensearch_cluster = aws_ec2.SecurityGroup(self, "OpenSearchSG",
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for an opensearch cluster',
      security_group_name='opensearch-cluster-sg'
    )
    cdk.Tags.of(sg_opensearch_cluster).add('Name', 'opensearch-cluster-sg')

    sg_opensearch_cluster.add_ingress_rule(peer=sg_opensearch_cluster, connection=aws_ec2.Port.all_tcp(), description='opensearch-cluster-sg')

    sg_opensearch_cluster.add_ingress_rule(peer=sg_opensearch_client, connection=aws_ec2.Port.tcp(443), description='use-opensearch-cluster-sg')
    sg_opensearch_cluster.add_ingress_rule(peer=sg_opensearch_client, connection=aws_ec2.Port.tcp_range(9200, 9300), description='use-opensearch-cluster-sg')

    master_user_secret = aws_secretsmanager.Secret(self, "OpenSearchMasterUserSecret",
      generate_secret_string=aws_secretsmanager.SecretStringGenerator(
        secret_string_template=json.dumps({"username": "admin"}),
        generate_string_key="password",
        # Master password must be at least 8 characters long and contain at least one uppercase letter,
        # one lowercase letter, one number, and one special character.
        password_length=8
      )
    )

    #XXX: aws cdk elastsearch example - https://github.com/aws/aws-cdk/issues/2873
    # You should camelCase the property names instead of PascalCase
    opensearch_domain = aws_opensearchservice.Domain(self, "OpenSearch",
      domain_name=OPENSEARCH_DOMAIN_NAME,
      #XXX: Supported versions of OpenSearch and Elasticsearch
      # https://docs.aws.amazon.com/opensearch-service/latest/developerguide/what-is.html#choosing-version
      version=aws_opensearchservice.EngineVersion.OPENSEARCH_2_13,
      #XXX: Amazon OpenSearch Service - Current generation instance types
      # https://docs.aws.amazon.com/opensearch-service/latest/developerguide/supported-instance-types.html#latest-gen
      # - The OR1 instance types require OpenSearch 2.11 or later.
      # - OR1 instances are only compatible with other Graviton instance types master nodes (C6g, M6g, R6g)
      capacity={
        "master_nodes": 3,
        "master_node_instance_type": "m6g.large.search",
        "data_nodes": 3,
        "data_node_instance_type": "or1.large.search"
      },
      ebs={
        # Volume size must be between 20 and 1536 for or1.large.search instance type and version OpenSearch_2.11
        "volume_size": 20,
        "volume_type": aws_ec2.EbsDeviceVolumeType.GP3
      },
      #XXX: az_count must be equal to vpc subnets count.
      zone_awareness={
        "availability_zone_count": 3
      },
      logging={
        "slow_search_log_enabled": True,
        "app_log_enabled": True,
        "slow_index_log_enabled": True
      },
      fine_grained_access_control=aws_opensearchservice.AdvancedSecurityOptions(
        master_user_name=master_user_secret.secret_value_from_json("username").unsafe_unwrap(),
        master_user_password=master_user_secret.secret_value_from_json("password")
      ),
      # Enforce HTTPS is required when fine-grained access control is enabled.
      enforce_https=True,
      # Node-to-node encryption is required when fine-grained access control is enabled
      node_to_node_encryption=True,
      # Encryption-at-rest is required when fine-grained access control is enabled.
      encryption_at_rest={
        "enabled": True
      },
      use_unsigned_basic_auth=True,
      security_groups=[sg_opensearch_cluster],
      #XXX: For domains running OpenSearch or Elasticsearch 5.3 and later, OpenSearch Service takes hourly automated snapshots
      # Only applies for Elasticsearch versions below 5.3
      # automated_snapshot_start_hour=17, # 2 AM (GTM+9)
      vpc=vpc,
      vpc_subnets=[aws_ec2.SubnetSelection(one_per_az=True, subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS)],
      removal_policy=cdk.RemovalPolicy.DESTROY # default: cdk.RemovalPolicy.RETAIN
    )
    cdk.Tags.of(opensearch_domain).add('Name', OPENSEARCH_DOMAIN_NAME)

    self.sg_opensearch_client = sg_opensearch_client


    cdk.CfnOutput(self, 'OpenSearchDomainEndpoint', value=opensearch_domain.domain_endpoint,
      export_name=f'{self.stack_name}-OpenSearchDomainEndpoint')
    cdk.CfnOutput(self, 'OpenSearchDashboardsURL', value=f"{opensearch_domain.domain_endpoint}/_dashboards/",
      export_name=f'{self.stack_name}-OpenSearchDashboardsURL')
    cdk.CfnOutput(self, 'MasterUserSecretId', value=master_user_secret.secret_name,
      export_name=f'{self.stack_name}-MasterUserSecretId')
    cdk.CfnOutput(self, 'OpenSearchClientSecurityGroupId', value=self.sg_opensearch_client.security_group_id,
      export_name=f'{self.stack_name}-CleintSecurityGroupId')