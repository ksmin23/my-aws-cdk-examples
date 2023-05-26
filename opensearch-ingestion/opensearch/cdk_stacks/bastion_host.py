import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_iam
)
from constructs import Construct


class BastionHostEC2InstanceStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, opensearch_client_sg, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    ec2_instance_type = aws_ec2.InstanceType.of(aws_ec2.InstanceClass.BURSTABLE3, aws_ec2.InstanceSize.MEDIUM)

    sg_bastion_host = aws_ec2.SecurityGroup(self, "BastionHostSG",
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for an bastion host',
      security_group_name='bastion-host-sg'
    )
    cdk.Tags.of(sg_bastion_host).add('Name', 'bastion-host-sg')

    #TODO: SHOULD restrict IP range allowed to ssh acces
    sg_bastion_host.add_ingress_rule(peer=aws_ec2.Peer.ipv4("0.0.0.0/0"), connection=aws_ec2.Port.tcp(22), description='SSH access')

    ingestion_pipeline_policy_doc = aws_iam.PolicyDocument()

    ingestion_pipeline_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "sid": "PermitsWriteAccessToPipeline",
      "effect": aws_iam.Effect.ALLOW,
      "resources": [
        f"arn:aws:osis:{cdk.Aws.REGION}:{cdk.Aws.ACCOUNT_ID}:pipeline/*"
      ],
      "actions": [
        "osis:Ingest"
      ]
    }))

    ec2_instance_role = aws_iam.Role(self, 'EC2InstanceRole',
      role_name=f'EC2InstanceRole-{self.stack_name}',
      assumed_by=aws_iam.ServicePrincipal('ec2.amazonaws.com'),
      inline_policies={
        'PermitsWriteAccessToOSISPipeline': ingestion_pipeline_policy_doc
      },
      managed_policies=[
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonSSMManagedInstanceCore'),
        #XXX: EC2 instance should be able to access S3 for user data
        # aws_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonS3ReadOnlyAccess')
      ]
    )

    bastion_host = aws_ec2.Instance(self, "BastionHost",
      vpc=vpc,
      instance_type=ec2_instance_type,
      machine_image=aws_ec2.MachineImage.latest_amazon_linux2(),
      vpc_subnets=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PUBLIC),
      security_group=sg_bastion_host,
      role=ec2_instance_role
    )
    bastion_host.add_security_group(opensearch_client_sg)

    commands = '''
yum update -y
yum install -y jq

cd /home/ec2-user
su -c "pip3 install awscurl --user" -s /bin/sh ec2-user
su -c "pip3 install boto3 --user" -s /bin/sh ec2-user
'''

    bastion_host.user_data.add_commands(commands)

    cdk.CfnOutput(self, f'{self.stack_name}-EC2InstancePublicDNS',
      value=bastion_host.instance_public_dns_name,
      export_name=f'{self.stack_name}-EC2InstancePublicDNS')
    cdk.CfnOutput(self, f'{self.stack_name}-EC2InstanceId',
      value=bastion_host.instance_id,
      export_name=f'{self.stack_name}-EC2InstanceId')
    cdk.CfnOutput(self, f'{self.stack_name}-EC2InstanceAZ',
      value=bastion_host.instance_availability_zone,
      export_name=f'{self.stack_name}-EC2InstanceAZ')

