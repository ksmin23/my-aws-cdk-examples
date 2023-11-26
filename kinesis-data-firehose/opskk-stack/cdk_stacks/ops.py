#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import json
import random
import string

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_s3 as s3,
  aws_opensearchservice,
  aws_secretsmanager
)
from constructs import Construct

random.seed(47)


class OpenSearchDomainStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    OPENSEARCH_DEFAULT_DOMAIN_NAME = 'opensearch-{}'.format(''.join(random.sample((string.ascii_lowercase), k=5)))
    OPENSEARCH_DOMAIN_NAME = self.node.try_get_context("OpenSearchDomainName") or OPENSEARCH_DEFAULT_DOMAIN_NAME

    OPENSEARCH_INDEX_NAME = self.node.try_get_context("SearchIndexName") or "log-analysis"

    sg_opensearch_client = aws_ec2.SecurityGroup(self, "OpenSearchClientSG",
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for an opensearch client',
      security_group_name=f'opensearch-client-sg-{OPENSEARCH_DOMAIN_NAME}'
    )
    cdk.Tags.of(sg_opensearch_client).add('Name', 'opensearch-client-sg')

    sg_opensearch_cluster = aws_ec2.SecurityGroup(self, "OpenSearchSG",
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for an opensearch cluster',
      security_group_name=f'opensearch-cluster-sg-{OPENSEARCH_DOMAIN_NAME}'
    )
    cdk.Tags.of(sg_opensearch_cluster).add('Name', 'opensearch-cluster-sg')

    sg_opensearch_cluster.add_ingress_rule(peer=sg_opensearch_cluster, connection=aws_ec2.Port.all_tcp(), description='opensearch-cluster-sg')

    sg_opensearch_cluster.add_ingress_rule(peer=sg_opensearch_client, connection=aws_ec2.Port.tcp(443), description='opensearch-client-sg')
    sg_opensearch_cluster.add_ingress_rule(peer=sg_opensearch_client, connection=aws_ec2.Port.tcp_range(9200, 9300), description='opensearch-client-sg')

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
      version=aws_opensearchservice.EngineVersion.OPENSEARCH_2_5,
      #XXX: You cannot use graviton instances with non-graviton instances.
      # Use graviton instances as data nodes or use non-graviton instances as master nodes.
      capacity={
        "master_nodes": 3,
        "master_node_instance_type": "r6g.large.search",
        "data_nodes": 3,
        "data_node_instance_type": "r6g.large.search"
      },
      ebs={
        "volume_size": 10,
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
      #XXX: az_count must be equal to vpc subnets count.
      vpc_subnets=[aws_ec2.SubnetSelection(one_per_az=True, subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS)],
      removal_policy=cdk.RemovalPolicy.DESTROY # default: cdk.RemovalPolicy.RETAIN
    )
    cdk.Tags.of(opensearch_domain).add('Name', OPENSEARCH_DOMAIN_NAME)

    self.opensearch_domain = opensearch_domain
    self.sg_opensearch_client = sg_opensearch_client
    self.opensearch_index_name = OPENSEARCH_INDEX_NAME


    cdk.CfnOutput(self, 'OpenSearchDomainEndpoint',
      value=self.opensearch_domain.domain_endpoint,
      export_name=f'{self.stack_name}-Endpoint')
    cdk.CfnOutput(self, 'OpenSearchDashboardsURL',
      value=f"{self.opensearch_domain.domain_endpoint}/_dashboards/",
      export_name=f'{self.stack_name}-DashboardsURL')
    cdk.CfnOutput(self, 'OpenSearchIndexName',
      value=self.opensearch_index_name,
      export_name=f'{self.stack_name}-IndexName')
    cdk.CfnOutput(self, 'MasterUserSecretId',
      value=master_user_secret.secret_name,
      export_name=f'{self.stack_name}-MasterUserSecretId')
