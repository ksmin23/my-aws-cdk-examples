#!/usr/bin/env python3
import os
import random
import string

from aws_cdk import (
  core as cdk,
  aws_ec2,
  aws_iam,
  aws_opensearchservice
)

random.seed(47)

class OpensearchStack(cdk.Stack):

  def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    OPENSEARCH_DOMAIN_NAME = cdk.CfnParameter(self, 'OpenSearchDomainName',
      type='String',
      description='Amazon OpenSearch Service domain name',
      default='opensearch-{}'.format(''.join(random.sample((string.ascii_letters), k=5))),
      allowed_pattern='[A-Za-z0-9\-]+'
    )

    #XXX: For createing Amazon MWAA in the existing VPC,
    # remove comments from the below codes and
    # comments out vpc = aws_ec2.Vpc(..) codes,
    # then pass -c vpc_name=your-existing-vpc to cdk command
    # for example,
    # cdk -c vpc_name=your-existing-vpc syth
    #
    vpc_name = self.node.try_get_context('vpc_name')
    vpc = aws_ec2.Vpc.from_lookup(self, 'ExistingVPC',
      is_default=True,
      vpc_name=vpc_name
    )

    # vpc = aws_ec2.Vpc(self, "ElasticsearchHolVPC",
    #   max_azs=2,
    #   gateway_endpoints={
    #     "S3": aws_ec2.GatewayVpcEndpointOptions(
    #       service=aws_ec2.GatewayVpcEndpointAwsService.S3
    #     )
    #   }
    # )

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

    sg_use_opensearch = aws_ec2.SecurityGroup(self, "OpenSearchClientSG",
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for an opensearch client',
      security_group_name='use-opensearch-cluster-sg'
    )
    cdk.Tags.of(sg_use_opensearch).add('Name', 'use-opensearch-cluster-sg')

    sg_opensearch_cluster = aws_ec2.SecurityGroup(self, "OpenSearchSG",
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for an opensearch cluster',
      security_group_name='opensearch-cluster-sg'
    )
    cdk.Tags.of(sg_opensearch_cluster).add('Name', 'opensearch-cluster-sg')

    sg_opensearch_cluster.add_ingress_rule(peer=sg_opensearch_cluster, connection=aws_ec2.Port.all_tcp(), description='opensearch-cluster-sg')
    sg_opensearch_cluster.add_ingress_rule(peer=sg_use_opensearch, connection=aws_ec2.Port.all_tcp(), description='use-opensearch-cluster-sg')
    sg_opensearch_cluster.add_ingress_rule(peer=sg_bastion_host, connection=aws_ec2.Port.all_tcp(), description='bastion-host-sg')

    opensearch_access_policy = aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      # "resources": [self.format_arn(service="es", resource="domain", resource_name="{}/*".format(opensearch_domain_name))],
      #XXX: https://docs.aws.amazon.com/cdk/latest/guide/tokens.html
      "resources": [self.format_arn(service="es", resource="domain", resource_name=OPENSEARCH_DOMAIN_NAME.value_as_string + "/*")],
      "actions": [
        "es:Describe*",
        "es:List*",
        "es:Get*",
        "es:ESHttp*"
      ]
    })

    #XXX: aws cdk elastsearch example - https://github.com/aws/aws-cdk/issues/2873
    # You should camelCase the property names instead of PascalCase
    opensearch_domain = aws_opensearchservice.Domain(self, "OpenSearch",
      domain_name=OPENSEARCH_DOMAIN_NAME.value_as_string,
      version=aws_opensearchservice.EngineVersion.OPENSEARCH_1_0,
      capacity={
        "master_nodes": 3,
        "data_nodes": 3
      },
      ebs={
        "volume_size": 10
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

      #XXX: If conflicting settings are encountered (like disabling encryption at rest) enabling this setting will cause a failure.
      # Default: - false
      # access_policies setting conficts use_unsigned_basic_auth setting.
      # Error setting policy will be occurred.
      use_unsigned_basic_auth=True,
      # access_policies=[opensearch_access_policy],

      security_groups=[sg_opensearch_cluster],
      automated_snapshot_start_hour=17, # 2 AM, GTM+9
      vpc=vpc,
      vpc_subnets=[aws_ec2.SubnetSelection(one_per_az=True, subnet_type=aws_ec2.SubnetType.PRIVATE)],
      removal_policy=cdk.RemovalPolicy.DESTROY # default: cdk.RemovalPolicy.RETAIN
    )
    cdk.Tags.of(opensearch_domain).add('Name', f'{OPENSEARCH_DOMAIN_NAME.value_as_string}')


app = cdk.App()
OpensearchStack(app, "OpensearchStack", env=cdk.Environment(
  account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION')))

app.synth()

