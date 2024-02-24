#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_iam,
  aws_s3_assets
)
from constructs import Construct


class JupyterOnDLAMIStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    EC2_KEY_PAIR_NAME = self.node.try_get_context('ec2_key_pair_name')
    ec2_key_pair = aws_ec2.KeyPair.from_key_pair_attributes(self, 'EC2KeyPair',
      key_pair_name=EC2_KEY_PAIR_NAME
    )

    JUPYTER_NOTEBOOK_INSTANCE_TYPE = self.node.try_get_context('jupyter_notebook_instance_type') or 'g4dn.xlarge'

    dlami_name = self.node.try_get_context('dlami_name')

    sg_dl_notebook_host = aws_ec2.SecurityGroup(self, "DLNotebookInstanceSG",
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for an DL Notebook instance',
      security_group_name=f'dl-notebook-host-sg-{self.stack_name}'
    )
    cdk.Tags.of(sg_dl_notebook_host).add('Name', 'dl-notebook-host-sg')

    #TODO: SHOULD restrict IP range allowed to ssh acces
    sg_dl_notebook_host.add_ingress_rule(peer=aws_ec2.Peer.ipv4("0.0.0.0/0"),
      connection=aws_ec2.Port.tcp(22), description='SSH access')
    sg_dl_notebook_host.add_ingress_rule(peer=aws_ec2.Peer.ipv4("0.0.0.0/0"),
      connection=aws_ec2.Port.tcp(8080), description='Jupyter Notebook access')

    #XXX: https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_ec2/InstanceClass.html
    #XXX: https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_ec2/InstanceSize.html#aws_cdk.aws_ec2.InstanceSize
    # ec2_instance_type = aws_ec2.InstanceType.of(aws_ec2.InstanceClass.BURSTABLE3, aws_ec2.InstanceSize.MEDIUM)
    ec2_instance_type = aws_ec2.InstanceType(JUPYTER_NOTEBOOK_INSTANCE_TYPE)

    #XXX: Release Notes for DLAMI
    # https://docs.aws.amazon.com/dlami/latest/devguide/appendix-ami-release-notes.html
    ec2_machine_image = aws_ec2.MachineImage.lookup(
      name=dlami_name,
      owners=["amazon"]
    )

    dl_nb_instance_role = aws_iam.Role(self, 'DLNotebookInstanceSSM',
      role_name=f'EC2InstanceRole-{self.stack_name}',
      assumed_by=aws_iam.ServicePrincipal('ec2.amazonaws.com'),
      managed_policies=[
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonSSMManagedInstanceCore'),
        #XXX: EC2 instance should be able to access S3 for user data
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonS3ReadOnlyAccess')
      ]
    )

    dl_nb_instance = aws_ec2.Instance(self, "DLNotebookInstance",
      vpc=vpc,
      role=dl_nb_instance_role,
      instance_type=ec2_instance_type,
      machine_image=ec2_machine_image,
      vpc_subnets=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PUBLIC),
      security_group=sg_dl_notebook_host,
      key_pair=ec2_key_pair,
    )

    work_dirname = os.path.dirname(__file__)
    cdk_asset = aws_s3_assets.Asset(self, "Asset",
      path=os.path.join(work_dirname, "../user-data/ec2user-dlami-amzlinux2-jupyter-config.sh"))
    local_path = dl_nb_instance.user_data.add_s3_download_command(
      bucket=cdk_asset.bucket,
      bucket_key=cdk_asset.s3_object_key,
      local_file='/tmp/ec2user-dlami-amzlinux2-jupyter-config.sh'
    )

    cdk_asset.grant_read(dl_nb_instance.role)

    JUPYTER_PASSWORD = self.node.try_get_context('jupyter_password')

    commands = '''
set -x

exec > >(tee /var/log/bootstrap.log|logger -t user-data ) 2>&1
chmod +x {file_path}
sudo su - ec2-user bash -c '{file_path} $@' {AWS_Region} '{jupyter_password}'
/opt/aws/bin/cfn-signal -e $? --stack {cfn_stack} --resource {cfn_resource} --region {AWS_Region}
'''.format(AWS_Region=cdk.Aws.REGION, file_path=local_path, jupyter_password=JUPYTER_PASSWORD,
  cfn_stack=self.stack_name, cfn_resource=self.get_logical_id(dl_nb_instance.instance))

    dl_nb_instance.user_data.add_commands(commands)


    cdk.CfnOutput(self, 'CDKAssetS3BucketName',
      value=cdk_asset.s3_bucket_name,
      export_name=f'{self.stack_name}-CDKAssetS3BucketName')
    cdk.CfnOutput(self, 'CDKAssetS3ObjectKey',
      value=cdk_asset.s3_object_key,
      export_name=f'{self.stack_name}-CDKAssetS3ObjectKey')
    cdk.CfnOutput(self, 'DLNotebookInstanceId',
      value=dl_nb_instance.instance_id,
      export_name=f'{self.stack_name}-DLNBInstanceId')
    cdk.CfnOutput(self, 'DLNotebookInstancePublicDnsName',
      value=dl_nb_instance.instance_public_dns_name,
      export_name=f'{self.stack_name}-DLNBInstancePublicDnsName')
    cdk.CfnOutput(self, 'DLNotebookInstancePublicIP',
      value=dl_nb_instance.instance_public_ip,
      export_name=f'{self.stack_name}-DLNBInstancePublicIP')
    cdk.CfnOutput(self, 'JupyterURL',
      value=f'https://{dl_nb_instance.instance_public_dns_name}:8080/lab',
      export_name=f'{self.stack_name}-JupyterURL')
