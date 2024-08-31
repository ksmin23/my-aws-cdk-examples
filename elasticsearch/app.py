#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os
import random
import string

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_elasticsearch
)
from constructs import Construct

random.seed(37)

class ElasticsearchStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    #XXX: For creating this CDK Stack in the existing VPC,
    # remove comments from the below codes and
    # comments out vpc = aws_ec2.Vpc(..) codes,
    # then pass -c vpc_name=your-existing-vpc to cdk command
    # for example,
    # cdk -c vpc_name=your-existing-vpc syth
    #
    # if you encounter an error such as:
    #  jsii.errors.JavaScriptError:
    #    Error: When providing vpc options you need to provide a subnet for each AZ you are using at new Domain
    # check https://github.com/aws/aws-cdk/issues/12078
    # This error occurs when ZoneAwarenessEnabled in aws_opensearch.Domain(..) is set `true`
    #
    if str(os.environ.get('USE_DEFAULT_VPC', 'false')).lower() == 'true':
      vpc_name = self.node.try_get_context('vpc_name') or "default"
      vpc = aws_ec2.Vpc.from_lookup(self, 'ExistingVPC',
        is_default=True,
        vpc_name=vpc_name
      )
    else:
      vpc = aws_ec2.Vpc(self, "ElasticsearchHolVPC",
        max_azs=3,
        gateway_endpoints={
          "S3": aws_ec2.GatewayVpcEndpointOptions(
            service=aws_ec2.GatewayVpcEndpointAwsService.S3
          )
        }
      )

    #XXX: https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_ec2/InstanceClass.html
    #XXX: https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_ec2/InstanceSize.html#aws_cdk.aws_ec2.InstanceSize
    ec2_instance_type = aws_ec2.InstanceType.of(aws_ec2.InstanceClass.BURSTABLE3, aws_ec2.InstanceSize.MEDIUM)

    sg_bastion_host = aws_ec2.SecurityGroup(self, "BastionHostSG",
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for an bastion host',
      security_group_name='bastion-host-sg'
    )
    cdk.Tags.of(sg_bastion_host).add('Name', 'bastion-host-sg')

    #XXX: As there are no SSH public keys deployed on this machine,
    # you need to use EC2 Instance Connect with the command
    #  'aws ec2-instance-connect send-ssh-public-key' to provide your SSH public key.
    # https://aws.amazon.com/de/blogs/compute/new-using-amazon-ec2-instance-connect-for-ssh-access-to-your-ec2-instances/
    bastion_host = aws_ec2.BastionHostLinux(self, "BastionHost",
      vpc=vpc,
      instance_type=ec2_instance_type,
      subnet_selection=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PUBLIC),
      security_group=sg_bastion_host
    )

    #TODO: SHOULD restrict IP range allowed to ssh acces
    bastion_host.allow_ssh_access_from(aws_ec2.Peer.ipv4("0.0.0.0/0"))

    sg_use_es = aws_ec2.SecurityGroup(self, "ElasticSearchClientSG",
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for an elasticsearch client',
      security_group_name='use-es-cluster-sg'
    )
    cdk.Tags.of(sg_use_es).add('Name', 'use-es-cluster-sg')

    sg_es = aws_ec2.SecurityGroup(self, "ElasticSearchSG",
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for an elasticsearch cluster',
      security_group_name='es-cluster-sg'
    )
    cdk.Tags.of(sg_es).add('Name', 'es-cluster-sg')

    sg_es.add_ingress_rule(peer=sg_es, connection=aws_ec2.Port.all_tcp(), description='es-cluster-sg')
    sg_es.add_ingress_rule(peer=sg_use_es, connection=aws_ec2.Port.all_tcp(), description='use-es-cluster-sg')
    sg_es.add_ingress_rule(peer=sg_bastion_host, connection=aws_ec2.Port.all_tcp(), description='bastion-host-sg')

    #XXX: aws cdk elastsearch example - https://github.com/aws/aws-cdk/issues/2873
    es_domain_name = 'es-{}'.format(''.join(random.sample((string.ascii_lowercase), k=5)))
    es_cfn_domain = aws_elasticsearch.CfnDomain(self, "ElasticSearch",
      #XXX: Amazon OpenSearch Service - Current generation instance types
      # https://docs.aws.amazon.com/opensearch-service/latest/developerguide/supported-instance-types.html#latest-gen
      elasticsearch_cluster_config={
        "dedicatedMasterCount": 3,
        "dedicatedMasterEnabled": True,
        "dedicatedMasterType": "t3.medium.elasticsearch",
        "instanceCount": 3,
        "instanceType": "t3.medium.elasticsearch",
        "zoneAwarenessConfig": {
          #XXX: az_count must be equal to vpc subnets count.
          "availabilityZoneCount": 3,
        },
        "zoneAwarenessEnabled": True
      },
      ebs_options={
        "ebsEnabled": True,
        "volumeSize": 10,
        "volumeType": "gp3"
      },
      domain_name=es_domain_name,
      #XXX: Supported versions of OpenSearch and Elasticsearch
      # https://docs.aws.amazon.com/opensearch-service/latest/developerguide/what-is.html#choosing-version
      elasticsearch_version="7.10",
      encryption_at_rest_options={
        "enabled": False
      },
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
            "Resource": self.format_arn(service="es", resource="domain", resource_name="{}/*".format(es_domain_name))
          }
        ]
      },
      #XXX: For domains running OpenSearch or Elasticsearch 5.3 and later, OpenSearch Service takes hourly automated snapshots
      # Only applies for Elasticsearch versions below 5.3
      # snapshot_options={
      #   "automatedSnapshotStartHour": 17
      # },
      vpc_options={
        "securityGroupIds": [sg_es.security_group_id],
        #XXX: az_count must be equal to vpc subnets count.
        "subnetIds": vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS).subnet_ids
      }
    )
    cdk.Tags.of(es_cfn_domain).add('Name', 'es-hol')

    cdk.CfnOutput(self, 'BastionHostId', value=bastion_host.instance_id, export_name='BastionHostId')
    cdk.CfnOutput(self, 'BastionHostPublicDNSName', value=bastion_host.instance_public_dns_name, export_name='BastionHostPublicDNSName')
    cdk.CfnOutput(self, 'ESDomainEndpoint', value=es_cfn_domain.attr_domain_endpoint, export_name='ESDomainEndpoint')
    cdk.CfnOutput(self, 'ESDashboardsURL', value=f"{es_cfn_domain.attr_domain_endpoint}/_dashboards/", export_name='ESDashboardsURL')


app = cdk.App()
ElasticsearchStack(app, "AmazonElasticsearchStack", env=cdk.Environment(
  account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION')))

app.synth()

