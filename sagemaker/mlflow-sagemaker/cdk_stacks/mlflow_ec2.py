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


class MLflowOnEC2InstanceStack(Stack):

  def __init__(self, scope: Construct, construct_id: str,
    vpc, artifact_bucket, sg_rds_client,
    database_enpoint, database_secret, database_name,
    **kwargs) -> None:

    super().__init__(scope, construct_id, **kwargs)

    EC2_INSTANCE_TYPE = self.node.try_get_context('instance_type') or 't3.medium'

    ami_name = self.node.try_get_context('ami_name')

    sg_mlflow_ec2_instance = aws_ec2.SecurityGroup(self, "MLflowEC2InstanceSG",
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for MLflow server on EC2 Instance',
      security_group_name='mlflow-server-sg'
    )
    cdk.Tags.of(sg_mlflow_ec2_instance).add('Name', 'mlflow-server-sg')

    #TODO: SHOULD restrict IP range allowed to ssh acces
    sg_mlflow_ec2_instance.add_ingress_rule(peer=aws_ec2.Peer.ipv4("0.0.0.0/0"),
      connection=aws_ec2.Port.tcp(22), description='SSH access')
    sg_mlflow_ec2_instance.add_ingress_rule(peer=aws_ec2.Peer.ipv4(vpc.vpc_cidr_block),
      connection=aws_ec2.Port.tcp(5000), description='Access to MLflow Server')
    sg_mlflow_ec2_instance.add_ingress_rule(peer=aws_ec2.Peer.ipv4("0.0.0.0/0"),
      connection=aws_ec2.Port.tcp(5000), description='Access to MLflow Server')
    # sg_dlami_instance.add_ingress_rule(peer=aws_ec2.Peer.ipv4("0.0.0.0/0"),
    #   connection=aws_ec2.Port.tcp(8888), description='Jupyter Notebook access')

    #XXX: https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_ec2/InstanceClass.html
    #XXX: https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_ec2/InstanceSize.html#aws_cdk.aws_ec2.InstanceSize
    # ec2_instance_type = aws_ec2.InstanceType.of(aws_ec2.InstanceClass.BURSTABLE3, aws_ec2.InstanceSize.MEDIUM)
    ec2_instance_type = aws_ec2.InstanceType(EC2_INSTANCE_TYPE)

    #XXX: Release Notes for DLAMI
    # https://docs.aws.amazon.com/dlami/latest/devguide/appendix-ami-release-notes.html
    ec2_machine_image = aws_ec2.MachineImage.lookup(
      name=ami_name,
      owners=["amazon"]
    )

    secretsmanager_readonly_policy_doc = aws_iam.PolicyDocument()
    secretsmanager_readonly_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": [database_secret.secret_arn],
      "actions": ["secretsmanager:GetSecretValue"]
    }))

    mlflow_ec2_instance_role = aws_iam.Role(self, 'MLflowEC2InstanceRole',
      role_name=f'{self.stack_name}-EC2InstanceRole',
      assumed_by=aws_iam.ServicePrincipal('ec2.amazonaws.com'),
      inline_policies={
        'secretsmanager-readonly': secretsmanager_readonly_policy_doc,
      },
      managed_policies=[
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonSSMManagedInstanceCore'),
        #XXX: EC2 instance should be able to access S3 for user data
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonS3FullAccess')
      ]
    )

    mlflow_ec2_instance = aws_ec2.Instance(self, "MLflowEC2Instance",
      vpc=vpc,
      role=mlflow_ec2_instance_role,
      instance_type=ec2_instance_type,
      machine_image=ec2_machine_image,
      vpc_subnets=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PUBLIC),
      security_group=sg_mlflow_ec2_instance
    )
    mlflow_ec2_instance.add_security_group(sg_rds_client)

    user_data_asset = aws_s3_assets.Asset(self, 'MLflowEC2UserData',
      path=os.path.join(os.path.dirname(__file__), '../user-data/'))
    user_data_asset.grant_read(mlflow_ec2_instance.role)



    commands = '''
apt update && apt upgrade -y
apt install software-properties-common -y
apt-get install -y -q mysql-client
apt-get install -y -q jq
apt install -y -q unzip

add-apt-repository -y ppa:deadsnakes/ppa
apt install -y -q python3.10
apt install -y -q python3.10-distutils
update-alternatives --install /usr/local/bin/python3 python3 /usr/bin/python3.10 10
su -c "curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10" -s /bin/sh ubuntu
su -c "python3.10 -m pip install --upgrade pip" -s /bin/sh ubuntu
apt install -y -q python3.10-venv
apt install -y -q supervisor

su -c "python3.10 -m pip install -U boto3" -s /bin/sh ubuntu
su -c "python3.10 -m pip install -U mlflow==2.6.0 PyMySQL==1.1.0 urllib3==1.26.18" -s /bin/sh ubuntu

cd /home/ubuntu
curl -s "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
rm -f awscliv2.zip
'''

    commands += f'''
cd /home/ubuntu

cat <<EOF >env_vars.sh
export BUCKET=s3://{artifact_bucket.bucket_name}
export DB_EDNPOINT={database_enpoint}
export DATABASE={database_name}
export USERNAME=$(aws secretsmanager get-secret-value --secret-id {database_secret.secret_name} | jq -r '.SecretString | fromjson.username')
export PASSWORD=$(aws secretsmanager get-secret-value --secret-id {database_secret.secret_name} | jq -r '.SecretString | fromjson.password')
EOF

chown ubuntu:ubuntu env_vars.sh
'''
    mlflow_ec2_instance.user_data.add_commands(commands)

    USER_DATA_LOCAL_PATH = mlflow_ec2_instance.user_data.add_s3_download_command(
      bucket=user_data_asset.bucket,
      bucket_key=user_data_asset.s3_object_key,
      local_file='/tmp/user_data.zip'
    )

    commands =f'''
cd /home/ubuntu/
mkdir -p /home/ubuntu/opt
unzip {USER_DATA_LOCAL_PATH} -d /home/ubuntu/opt/
chown -R ubuntu:root /home/ubuntu/opt
chmod +x /home/ubuntu/opt/mlflow_server.sh
cp -fp /home/ubuntu/opt/mlflow_supervisord.conf /etc/supervisor/conf.d/
service supervisor restart
'''
    mlflow_ec2_instance.user_data.add_commands(commands)


    cdk.CfnOutput(self, 'EC2InstancePublicDNS',
      value=mlflow_ec2_instance.instance_public_dns_name,
      export_name=f'{self.stack_name}-EC2InstancePublicDNS')
    cdk.CfnOutput(self, 'EC2InstanceId',
      value=mlflow_ec2_instance.instance_id,
      export_name=f'{self.stack_name}-EC2InstanceId')
    cdk.CfnOutput(self, 'EC2InstanceAZ',
      value=mlflow_ec2_instance.instance_availability_zone,
      export_name=f'{self.stack_name}-EC2InstanceAZ')
    cdk.CfnOutput(self, 'EC2UserDataS3Path',
      value=user_data_asset.s3_object_url,
      export_name=f'{self.stack_name}-EC2UserDataS3Path')
