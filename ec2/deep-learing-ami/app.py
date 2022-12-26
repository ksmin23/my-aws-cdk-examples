#!/usr/bin/env python3
import os

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_iam,
  aws_s3_assets
)
from constructs import Construct
# from aws_cdk.aws_s3_assets import Asset

class DeepLearningAMIStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    EC2_KEY_PAIR_NAME = self.node.try_get_context('ec2_key_pair_name')
    assert not EC2_KEY_PAIR_NAME.endswith(".pem")

    JUPYTER_NOTEBOOK_INSTANCE_TYPE = self.node.try_get_context('jupyter_notebook_instance_type') or 'g4dn.xlarge'

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

    # vpc = aws_ec2.Vpc(self, "DLAMIStackVPC",
    #   max_azs=3,
    #   gateway_endpoints={
    #     "S3": aws_ec2.GatewayVpcEndpointOptions(
    #       service=aws_ec2.GatewayVpcEndpointAwsService.S3
    #     )
    #   }
    # )

    dlami_name = self.node.try_get_context('dlami_name')

    sg_dl_notebook_host = aws_ec2.SecurityGroup(self, "DLNotebookInstanceSG",
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for an DL Notebook instance',
      security_group_name='dl-notebook-host-sg'
    )
    cdk.Tags.of(sg_dl_notebook_host).add('Name', 'dl-notebook-host-sg')

    #TODO: SHOULD restrict IP range allowed to ssh acces
    sg_dl_notebook_host.add_ingress_rule(peer=aws_ec2.Peer.ipv4("0.0.0.0/0"), connection=aws_ec2.Port.tcp(22), description='SSH access')
    sg_dl_notebook_host.add_ingress_rule(peer=aws_ec2.Peer.ipv4("0.0.0.0/0"), connection=aws_ec2.Port.tcp(8888), description='Jupyter Notebook access')

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
      key_name=EC2_KEY_PAIR_NAME
    )

    work_dirname = os.path.dirname(__file__)
    cdk_asset = aws_s3_assets.Asset(self, "Asset", path=os.path.join(work_dirname, "user-data/ec2user-jupyter-config.sh"))
    local_path = dl_nb_instance.user_data.add_s3_download_command(
      bucket=cdk_asset.bucket,
      bucket_key=cdk_asset.s3_object_key,
      local_file='/tmp/ec2user-jupyter-config.sh'
    )

    cdk_asset.grant_read(dl_nb_instance.role)

    commands = '''
set -x

exec > >(tee /var/log/bootstrap.log|logger -t user-data ) 2>&1
chmod +x {file_path}
sudo su - ec2-user bash -c '{file_path} $@' {AWS_Region}
/opt/aws/bin/cfn-signal -e $? --stack {cfn_stack} --resource {cfn_resource} --region {AWS_Region}
'''.format(AWS_Region=cdk.Aws.REGION, file_path=local_path,
  cfn_stack=self.stack_name, cfn_resource=self.get_logical_id(dl_nb_instance.instance))

    dl_nb_instance.user_data.add_commands(commands)

    cdk.CfnOutput(self, 'CDKAssetS3BucketName', value=cdk_asset.s3_bucket_name)
    cdk.CfnOutput(self, 'CDKAssetS3ObjectKey', value=cdk_asset.s3_object_key)
    cdk.CfnOutput(self, 'DLNotebookInstanceId', value=dl_nb_instance.instance_id)
    cdk.CfnOutput(self, 'DLNotebookInstancePublicDnsName', value=dl_nb_instance.instance_public_dns_name)
    cdk.CfnOutput(self, 'DLNotebookInstancePublicIP', value=dl_nb_instance.instance_public_ip)
    cdk.CfnOutput(self, 'JupyterURL', value=f'https://{dl_nb_instance.instance_public_dns_name}:8888/lab')


app = cdk.App()
DeepLearningAMIStack(app, "DeepLearningAMIStack",
  env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'),
    region=os.getenv('CDK_DEFAULT_REGION')))

app.synth()
