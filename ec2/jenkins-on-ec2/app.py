#!/usr/bin/env python3
import os

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_s3_assets
)
from constructs import Construct


class JenkinsOnEC2Stack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    EC2_KEY_PAIR_NAME = cdk.CfnParameter(self, 'EC2KeyPairName',
      type='String',
      description='Amazon EC2 Instance KeyPair name'
    )

    #XXX: For creating this CDK Stack in the existing VPC,
    # remove comments from the below codes and
    # comments out vpc = aws_ec2.Vpc(..) codes,
    # then pass -c vpc_name=your-existing-vpc to cdk command
    # for example,
    # cdk -c vpc_name=your-existing-vpc syth
    #
    # vpc_name = self.node.try_get_context("vpc_name")
    # vpc = aws_ec2.Vpc.from_lookup(self, "ExistingVPC",
    #   is_default=True,
    #   vpc_name=vpc_name)

    #XXX: To use more than 2 AZs, be sure to specify the account and region on your stack.
    #XXX: https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_ec2/Vpc.html
    vpc = aws_ec2.Vpc(self, "JenkinsOnEC2Stack",
      ip_addresses=aws_ec2.IpAddresses.cidr("10.0.0.0/21"),
      max_azs=3,

      # 'subnetConfiguration' specifies the "subnet groups" to create.
      # Every subnet group will have a subnet for each AZ, so this
      # configuration will create `2 groups × 3 AZs = 6` subnets.
      subnet_configuration=[
        {
          "cidrMask": 24,
          "name": "Public",
          "subnetType": aws_ec2.SubnetType.PUBLIC,
        },
        {
          "cidrMask": 24,
          "name": "Private",
          "subnetType": aws_ec2.SubnetType.PRIVATE_WITH_EGRESS
        }
      ],
      gateway_endpoints={
        "S3": aws_ec2.GatewayVpcEndpointOptions(
          service=aws_ec2.GatewayVpcEndpointAwsService.S3
        )
      }
    )

    #XXX: https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_ec2/InstanceClass.html
    #XXX: https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_ec2/InstanceSize.html#aws_cdk.aws_ec2.InstanceSize
    ec2_instance_type = aws_ec2.InstanceType.of(aws_ec2.InstanceClass.BURSTABLE3, aws_ec2.InstanceSize.MEDIUM)

    sg_jenkins_host = aws_ec2.SecurityGroup(self, "JenkinsHostSG",
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for an jenkins host',
      security_group_name='jenkins-host-sg'
    )
    cdk.Tags.of(sg_jenkins_host).add('Name', 'jenkins-host-sg')

    #TODO: SHOULD restrict IP range allowed to ssh acces
    sg_jenkins_host.add_ingress_rule(peer=aws_ec2.Peer.ipv4("0.0.0.0/0"), connection=aws_ec2.Port.tcp(22), description='SSH access')
    sg_jenkins_host.add_ingress_rule(peer=aws_ec2.Peer.ipv4("0.0.0.0/0"), connection=aws_ec2.Port.tcp(80), description='HTTP access')

    jenkins_host = aws_ec2.Instance(self, "JenkinsHost",
      vpc=vpc,
      instance_type=ec2_instance_type,
      machine_image=aws_ec2.MachineImage.latest_amazon_linux(
        generation=aws_ec2.AmazonLinuxGeneration.AMAZON_LINUX_2,
        edition=aws_ec2.AmazonLinuxEdition.STANDARD,
        kernel=aws_ec2.AmazonLinuxKernel.KERNEL5_X
      ),
      vpc_subnets=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PUBLIC),
      #XXX: Create a jenkins in the private subnets
      # vpc_subnets=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS),
      security_group=sg_jenkins_host,
      key_name=EC2_KEY_PAIR_NAME.value_as_string
    )

    # Script in S3 as Asset
    user_data_asset = aws_s3_assets.Asset(self, "JenkinsEC2UserData",
      path=os.path.join(os.path.dirname(__file__), "user-data/install_jenkins.sh"))

    local_path = jenkins_host.user_data.add_s3_download_command(
      bucket=user_data_asset.bucket,
      bucket_key=user_data_asset.s3_object_key
    )

    # Userdata executes script from S3
    jenkins_host.user_data.add_execute_file_command(
      file_path=local_path
    )
    user_data_asset.grant_read(jenkins_host.role)

    cdk.CfnOutput(self, 'JenkinsHostId', value=jenkins_host.instance_id, export_name='JenkinsHostId')
    #XXX: comments out the follwing line if you create a jenkins in the private subnets
    cdk.CfnOutput(self, 'JenkinsHostPublicDNSName', value=jenkins_host.instance_public_dns_name, export_name='JenkinsHostPublicDNSName')


app = cdk.App()
JenkinsOnEC2Stack(app, "JenkinsOnEC2Stack", env=cdk.Environment(
  account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION')))

app.synth()
