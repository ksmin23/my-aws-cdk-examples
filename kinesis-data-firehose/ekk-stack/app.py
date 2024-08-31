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
  aws_iam,
  aws_s3 as s3,
  aws_kinesisfirehose,
  aws_elasticsearch
)
from constructs import Construct

random.seed(47)

class EKKStack(Stack):

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
      vpc = aws_ec2.Vpc(self, "EKKStackVPC",
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
    ES_DOMAIN_NAME = self.node.try_get_context("es_domain_name")
    es_cfn_domain = aws_elasticsearch.CfnDomain(self, "ElasticSearch",
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
      domain_name=ES_DOMAIN_NAME,
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
            "Resource": self.format_arn(service="es", resource="domain", resource_name="{}/*".format(ES_DOMAIN_NAME))
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
    cdk.Tags.of(es_cfn_domain).add('Name', ES_DOMAIN_NAME)

    S3_BUCKET_SUFFIX = ''.join(random.sample((string.ascii_lowercase + string.digits), k=7))
    s3_bucket = s3.Bucket(self, "s3bucket",
      removal_policy=cdk.RemovalPolicy.DESTROY, #XXX: Default: cdk.RemovalPolicy.RETAIN - The bucket will be orphaned
      bucket_name="ekk-stack-{region}-{suffix}".format(
        region=cdk.Aws.REGION, suffix=S3_BUCKET_SUFFIX))

    firehose_role_policy_doc = aws_iam.PolicyDocument()
    firehose_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": [s3_bucket.bucket_arn, "{}/*".format(s3_bucket.bucket_arn)],
      "actions": ["s3:AbortMultipartUpload",
        "s3:GetBucketLocation",
        "s3:GetObject",
        "s3:ListBucket",
        "s3:ListBucketMultipartUploads",
        "s3:PutObject"]
    }))

    firehose_role_policy_doc.add_statements(aws_iam.PolicyStatement(
      effect=aws_iam.Effect.ALLOW,
      resources=["*"],
      actions=["ec2:DescribeVpcs",
        "ec2:DescribeVpcAttribute",
        "ec2:DescribeSubnets",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeNetworkInterfaces",
        "ec2:CreateNetworkInterface",
        "ec2:CreateNetworkInterfacePermission",
        "ec2:DeleteNetworkInterface"]
    ))

    firehose_role_policy_doc.add_statements(aws_iam.PolicyStatement(
      effect=aws_iam.Effect.ALLOW,
      resources=[es_cfn_domain.attr_arn, "{}/*".format(es_cfn_domain.attr_arn)],
      actions=["es:DescribeElasticsearchDomain",
        "es:DescribeElasticsearchDomains",
        "es:DescribeElasticsearchDomainConfig",
        "es:ESHttpPost",
        "es:ESHttpPut"]
    ))

    ES_INDEX_NAME = self.node.try_get_context("es_index_name")

    firehose_role_policy_doc.add_statements(aws_iam.PolicyStatement(
      effect=aws_iam.Effect.ALLOW,
      resources=[es_cfn_domain.attr_arn, "{}/*".format(es_cfn_domain.attr_arn)],
      # resources=[
      #   "{aes_arn}/_all/_settings".format(aes_arn=es_cfn_domain.attr_arn),
      #   "{aes_arn}/_cluster/stats".format(aes_arn=es_cfn_domain.attr_arn),
      #   "{aes_arn}/{es_index_name}*/_mapping".format(aes_arn=es_cfn_domain.attr_arn, es_index_name=ES_INDEX_NAME),
      #   "{aes_arn}/_nodes".format(aes_arn=es_cfn_domain.attr_arn),
      #   "{aes_arn}/_nodes/*/stats".format(aes_arn=es_cfn_domain.attr_arn),
      #   "{aes_arn}/_stats".format(aes_arn=es_cfn_domain.attr_arn),
      #   "{aes_arn}/{es_index_name}*/_stats".format(aes_arn=es_cfn_domain.attr_arn, es_index_name=ES_INDEX_NAME)
      # ],
      actions=["es:ESHttpGet"]
    ))

    firehose_log_group_name = "/aws/kinesisfirehose/{}".format(ES_INDEX_NAME)
    firehose_role_policy_doc.add_statements(aws_iam.PolicyStatement(
      effect=aws_iam.Effect.ALLOW,
      #XXX: The ARN will be formatted as follows:
      # arn:{partition}:{service}:{region}:{account}:{resource}{sep}}{resource-name}
      resources=[self.format_arn(service="logs", resource="log-group",
        resource_name="{}:log-stream:*".format(firehose_log_group_name), arn_format=cdk.ArnFormat.COLON_RESOURCE_NAME)],
      actions=["logs:PutLogEvents"]
    ))

    firehose_role = aws_iam.Role(self, "KinesisFirehoseServiceRole",
      role_name="KinesisFirehoseServiceRole-{es_index}-{region}".format(es_index=ES_INDEX_NAME, region=cdk.Aws.REGION),
      assumed_by=aws_iam.ServicePrincipal("firehose.amazonaws.com"),
      #XXX: use inline_policies to work around https://github.com/aws/aws-cdk/issues/5221
      inline_policies={
        "firehose_role_policy": firehose_role_policy_doc
      }
    )

    es_dest_vpc_config = aws_kinesisfirehose.CfnDeliveryStream.VpcConfigurationProperty(
      role_arn=firehose_role.role_arn,
      security_group_ids=[sg_use_es.security_group_id],
      subnet_ids=vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS).subnet_ids
    )

    es_dest_config = aws_kinesisfirehose.CfnDeliveryStream.ElasticsearchDestinationConfigurationProperty(
      index_name=ES_INDEX_NAME,
      role_arn=firehose_role.role_arn,
      s3_configuration={
        "bucketArn": s3_bucket.bucket_arn,
        "bufferingHints": {
          "intervalInSeconds": 60,
          "sizeInMBs": 1
        },
        "cloudWatchLoggingOptions": {
          "enabled": True,
          "logGroupName": firehose_log_group_name,
          "logStreamName": "S3Backup"
        },
        "compressionFormat": "UNCOMPRESSED", # [GZIP | HADOOP_SNAPPY | Snappy | UNCOMPRESSED | ZIP]
        # Kinesis Data Firehose automatically appends the “YYYY/MM/dd/HH/” UTC prefix to delivered S3 files. You can also specify
        # an extra prefix in front of the time format and add "/" to the end to have it appear as a folder in the S3 console.
        "prefix": "{}/".format(ES_INDEX_NAME),
        "roleArn": firehose_role.role_arn
      },
      buffering_hints={
        "intervalInSeconds": 60,
        "sizeInMBs": 1
      },
      cloud_watch_logging_options={
        "enabled": True,
        "logGroupName": firehose_log_group_name,
        "logStreamName": "ElasticsearchDelivery"
      },
      domain_arn=es_cfn_domain.attr_arn,
      #XXX: Index rotation appends a timestamp to the IndexName to facilitate the expiration of old data.
      # For more information, see https://docs.aws.amazon.com/firehose/latest/dev/create-destination.html#create-destination-elasticsearch
      # For more information about allowed values,
      # see https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-kinesisfirehose-deliverystream-elasticsearchdestinationconfiguration.html#cfn-kinesisfirehose-deliverystream-elasticsearchdestinationconfiguration-indexrotationperiod
      index_rotation_period="NoRotation", # [NoRotation | OneDay | OneHour | OneMonth | OneWeek]
      retry_options={
        "durationInSeconds": 60
      },
      s3_backup_mode="FailedDocumentsOnly", # [AllDocuments | FailedDocumentsOnly]
      vpc_configuration=es_dest_vpc_config
    )

    firehose_to_es_delivery_stream = aws_kinesisfirehose.CfnDeliveryStream(self, "KinesisFirehoseToES",
      delivery_stream_name=ES_INDEX_NAME,
      delivery_stream_type="DirectPut",
      elasticsearch_destination_configuration=es_dest_config,
      tags=[{"key": "Name", "value": ES_DOMAIN_NAME}]
    )

app = cdk.App()
EKKStack(app, "AmazonEKKStack", env=cdk.Environment(
  account=os.environ["CDK_DEFAULT_ACCOUNT"],
  region=os.environ["CDK_DEFAULT_REGION"]))

app.synth()
