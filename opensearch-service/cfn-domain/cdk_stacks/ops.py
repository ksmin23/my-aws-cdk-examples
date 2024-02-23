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

    #XXX: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-opensearchservice-domain.html
    opensearch_cfn_domain = aws_opensearchservice.CfnDomain(self, "OpenSearchCfnDomain",
      access_policies={
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {
              "AWS": "*"
            },
            "Action": [
              "es:Describe*",
              "es:List*",
              "es:Get*",
              "es:ESHttp*"
            ],
            "Resource": self.format_arn(service="es", resource="domain", resource_name=f"{OPENSEARCH_DOMAIN_NAME}/*")
          }
        ]
      },
      advanced_security_options=aws_opensearchservice.CfnDomain.AdvancedSecurityOptionsInputProperty(
        enabled=True,
        internal_user_database_enabled=True,
        master_user_options=aws_opensearchservice.CfnDomain.MasterUserOptionsProperty(
          master_user_name=master_user_secret.secret_value_from_json("username").to_string(),
          master_user_password=master_user_secret.secret_value_from_json("password").to_string()
        )
      ),
      #XXX: Amazon OpenSearch Service - Current generation instance types
      # https://docs.aws.amazon.com/opensearch-service/latest/developerguide/supported-instance-types.html#latest-gen
      cluster_config=aws_opensearchservice.CfnDomain.ClusterConfigProperty(
        dedicated_master_count=3,
        dedicated_master_enabled=True,
        dedicated_master_type="r6g.large.search",
        instance_count=3,
        instance_type="r6g.large.search",
        zone_awareness_config=aws_opensearchservice.CfnDomain.ZoneAwarenessConfigProperty(
          #XXX: az_count must be equal to vpc subnets count.
          availability_zone_count=3
        ),
        zone_awareness_enabled=True
      ),
      domain_endpoint_options=aws_opensearchservice.CfnDomain.DomainEndpointOptionsProperty(
        enforce_https=True,
        # optional
        tls_security_policy='Policy-Min-TLS-1-0-2019-07'
      ),
      domain_name=OPENSEARCH_DOMAIN_NAME,
      ebs_options=aws_opensearchservice.CfnDomain.EBSOptionsProperty(
        ebs_enabled=True,
        volume_size=10,
        volume_type="gp3"
      ),
      encryption_at_rest_options=aws_opensearchservice.CfnDomain.EncryptionAtRestOptionsProperty(
        enabled=True
      ),
      #XXX: Supported versions of OpenSearch and Elasticsearch
      # https://docs.aws.amazon.com/opensearch-service/latest/developerguide/what-is.html#choosing-version
      engine_version=aws_opensearchservice.EngineVersion.OPENSEARCH_2_5.version,
      node_to_node_encryption_options=aws_opensearchservice.CfnDomain.NodeToNodeEncryptionOptionsProperty(
        enabled=True
      ),
      #XXX: For domains running OpenSearch or Elasticsearch 5.3 and later, OpenSearch Service takes hourly automated snapshots
      # Only applies for Elasticsearch versions below 5.3
      # snapshot_options=aws_opensearchservice.CfnDomain.SnapshotOptionsProperty(
      #   automated_snapshot_start_hour=17
      # ),
      tags=[cdk.CfnTag(
        key='Name',
        value=OPENSEARCH_DOMAIN_NAME
      )],
      vpc_options=aws_opensearchservice.CfnDomain.VPCOptionsProperty(
        security_group_ids=[sg_opensearch_cluster.security_group_id],
        subnet_ids=vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS).subnet_ids
      )
    )
    opensearch_cfn_domain.apply_removal_policy(cdk.RemovalPolicy.DESTROY) # default: cdk.RemovalPolicy.RETAIN

    self.sg_opensearch_client = sg_opensearch_client


    cdk.CfnOutput(self, 'OpenSearchDomainEndpoint',
      value=opensearch_cfn_domain.attr_domain_endpoint,
      export_name=f'{self.stack_name}-OpenSearchDomainEndpoint')
    cdk.CfnOutput(self, 'OpenSearchDashboardsURL',
      value=f"{opensearch_cfn_domain.attr_domain_endpoint}/_dashboards/",
      export_name=f'{self.stack_name}-OpenSearchDashboardsURL')
    cdk.CfnOutput(self, 'MasterUserSecretId',
      value=master_user_secret.secret_name,
      export_name=f'{self.stack_name}-MasterUserSecretId')
