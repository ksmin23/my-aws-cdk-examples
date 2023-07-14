#!/usr/bin/env python3
import os

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_s3_assets
)
from constructs import Construct


class NginxRDSProxyStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, sg_rds_client, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    #XXX: https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_ec2/InstanceClass.html
    #XXX: https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_ec2/InstanceSize.html#aws_cdk.aws_ec2.InstanceSize
    ec2_instance_type = aws_ec2.InstanceType.of(aws_ec2.InstanceClass.BURSTABLE3, aws_ec2.InstanceSize.MEDIUM)

    sg_nginx_rds_proxy = aws_ec2.SecurityGroup(self, "NginxRDSProxySG",
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for an nginx host',
      security_group_name='nginx-rds-proxy-sg'
    )
    cdk.Tags.of(sg_nginx_rds_proxy).add('Name', 'nginx-rds-proxy-sg')

    #TODO: SHOULD restrict IP range allowed to ssh acces
    sg_nginx_rds_proxy.add_ingress_rule(peer=aws_ec2.Peer.ipv4("0.0.0.0/0"), connection=aws_ec2.Port.tcp(22), description='SSH access')
    #TODO: SHOULD restrict IP range and Port range allowed to acces RDS
    sg_nginx_rds_proxy.add_ingress_rule(peer=aws_ec2.Peer.ipv4("0.0.0.0/0"), connection=aws_ec2.Port.tcp_range(4306, 5306), description='RDS access')

    ngnix_host = aws_ec2.Instance(self, "NginxHost",
      vpc=vpc,
      instance_type=ec2_instance_type,
      machine_image=aws_ec2.MachineImage.latest_amazon_linux2(),
      vpc_subnets=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PUBLIC),
      security_group=sg_nginx_rds_proxy
    )
    ngnix_host.add_security_group(sg_rds_client)

    # Script in S3 as Asset
    user_data_asset = aws_s3_assets.Asset(self, "NginxEC2UserData",
      path=os.path.join(os.path.dirname(__file__), "user-data/install_nginx.sh"))

    local_path = ngnix_host.user_data.add_s3_download_command(
      bucket=user_data_asset.bucket,
      bucket_key=user_data_asset.s3_object_key
    )

    # Userdata executes script from S3
    ngnix_host.user_data.add_execute_file_command(
      file_path=local_path
    )
    user_data_asset.grant_read(ngnix_host.role)

    cdk.CfnOutput(self, 'NginxRDSProxyHostId', value=ngnix_host.instance_id)
    #XXX: comments out the follwing line if you create a nginx rds proxy in the private subnets
    cdk.CfnOutput(self, 'NginxRDSProxyPublicDNSName', value=ngnix_host.instance_public_dns_name)
