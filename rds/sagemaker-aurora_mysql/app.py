#!/usr/bin/env python3
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_iam,
  aws_logs,
  aws_rds,
  aws_sagemaker
)
from constructs import Construct


class SagemakerAuroraMysqlStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    #XXX: For creating this CDK Stack in the existing VPC,
    # remove comments from the below codes and
    # comments out vpc = aws_ec2.Vpc(..) codes,
    # then pass -c vpc_name=your-existing-vpc to cdk command
    # for example,
    # cdk -c vpc_name=your-existing-vpc syth
    #
    # vpc_name = self.node.try_get_context("vpc_name") or "default"
    # vpc = aws_ec2.Vpc.from_lookup(self, "SagemakerAuroraMySQLVPC",
    #   is_default=True,
    #   vpc_name=vpc_name)

    #XXX: To use more than 2 AZs, be sure to specify the account and region on your stack.
    #XXX: https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_ec2/Vpc.html
    vpc = aws_ec2.Vpc(self, "SagemakerAuroraMySQLVPC",
      max_azs=2,
      gateway_endpoints={
        "S3": aws_ec2.GatewayVpcEndpointOptions(
          service=aws_ec2.GatewayVpcEndpointAwsService.S3
        )
      }
    )

    sg_use_mysql = aws_ec2.SecurityGroup(self, 'MySQLClientSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for mysql client',
      security_group_name='use-mysql-sg'
    )
    cdk.Tags.of(sg_use_mysql).add('Name', 'mysql-client-sg')

    sg_mysql_server = aws_ec2.SecurityGroup(self, 'MySQLServerSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for mysql',
      security_group_name='mysql-server-sg'
    )
    sg_mysql_server.add_ingress_rule(peer=sg_use_mysql, connection=aws_ec2.Port.tcp(3306),
      description='use-mysql-sg')
    sg_mysql_server.add_ingress_rule(peer=sg_mysql_server, connection=aws_ec2.Port.all_tcp(),
      description='mysql-server-sg')
    cdk.Tags.of(sg_mysql_server).add('Name', 'mysql-server-sg')

    rds_subnet_group = aws_rds.SubnetGroup(self, 'RdsSubnetGroup',
      description='subnet group for mysql',
      subnet_group_name='aurora-mysql',
      vpc_subnets=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS),
      vpc=vpc
    )

    rds_engine = aws_rds.DatabaseClusterEngine.aurora_mysql(version=aws_rds.AuroraMysqlEngineVersion.VER_2_08_1)

    rds_cluster_param_group = aws_rds.ParameterGroup(self, 'AuroraMySQLClusterParamGroup',
      engine=rds_engine,
      description='Custom cluster parameter group for aurora-mysql5.7',
      parameters={
        'innodb_flush_log_at_trx_commit': '2',
        'slow_query_log': '1',
        'tx_isolation': 'READ-COMMITTED',
        'wait_timeout': '300',
        'character-set-client-handshake': '0',
        'character_set_server': 'utf8mb4',
        'collation_server': 'utf8mb4_unicode_ci',
        'init_connect': 'SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci'
      }
    )

    rds_db_param_group = aws_rds.ParameterGroup(self, 'AuroraMySQLDBParamGroup',
      engine=rds_engine,
      description='Custom parameter group for aurora-mysql5.7',
      parameters={
        'slow_query_log': '1',
        'tx_isolation': 'READ-COMMITTED',
        'wait_timeout': '300',
        'init_connect': 'SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci'
      }
    )

    db_cluster_name = self.node.try_get_context('db_cluster_name')
    rds_credentials = aws_rds.Credentials.from_generated_secret("admin")
    db_cluster = aws_rds.DatabaseCluster(self, 'Database',
      engine=rds_engine,
      credentials=rds_credentials,
      writer=aws_rds.ClusterInstance.provisioned("writer",
        instance_type=aws_ec2.InstanceType.of(aws_ec2.InstanceClass.BURSTABLE3, aws_ec2.InstanceSize.MEDIUM),
        parameter_group=rds_db_param_group,
        auto_minor_version_upgrade=False,
      ),
      readers=[
        aws_rds.ClusterInstance.provisioned("reader",
          instance_type=aws_ec2.InstanceType.of(aws_ec2.InstanceClass.BURSTABLE3, aws_ec2.InstanceSize.MEDIUM),
          parameter_group=rds_db_param_group,
          auto_minor_version_upgrade=False
        )
      ],
      parameter_group=rds_cluster_param_group,
      cloudwatch_logs_retention=aws_logs.RetentionDays.THREE_DAYS,
      cluster_identifier=db_cluster_name,
      subnet_group=rds_subnet_group,
      backup=aws_rds.BackupProps(
        retention=cdk.Duration.days(3),
        preferred_window="03:00-04:00"
      ),
      security_groups=[sg_mysql_server],
      vpc=vpc,
      vpc_subnets=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS)
    )

    sagemaker_notebook_role_policy_doc = aws_iam.PolicyDocument()
    sagemaker_notebook_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": [db_cluster.secret.secret_full_arn],
      "actions": ["secretsmanager:GetSecretValue"]
    }))

    sagemaker_notebook_role = aws_iam.Role(self, 'SageMakerNotebookRoleForRDS',
      role_name='AWSSageMakerNotebookRoleForRDS',
      assumed_by=aws_iam.ServicePrincipal('sagemaker.amazonaws.com'),
      inline_policies={
        'AuroraMySQLSecretPolicy': sagemaker_notebook_role_policy_doc
      }
    )

    cf_readonly_access_policy = aws_iam.ManagedPolicy.from_aws_managed_policy_name('AWSCloudFormationReadOnlyAccess')
    sagemaker_notebook_role.add_managed_policy(cf_readonly_access_policy) 

    #XXX: skip downloading rds-combined-ca-bundle.pem if not use SSL with a MySQL DB instance
    # https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_MySQL.html#MySQL.Concepts.SSLSupport
    rds_wb_lifecycle_content = '''#!/bin/bash
sudo -u ec2-user -i <<'EOF'
echo "export AWS_REGION={AWS_Region}" >> ~/.bashrc
source /home/ec2-user/anaconda3/bin/activate python3
pip install --upgrade ipython-sql
pip install --upgrade PyMySQL 
pip install --upgrade pretty_errors
source /home/ec2-user/anaconda3/bin/deactivate
cd /home/ec2-user/SageMaker
wget -N https://s3.amazonaws.com/rds-downloads/rds-combined-ca-bundle.pem
wget -N https://raw.githubusercontent.com/ksmin23/my-aws-cdk-examples/main/rds/sagemaker-aurora_mysql/ipython-sql.ipynb
EOF
'''.format(AWS_Region=cdk.Aws.REGION)

    rds_wb_lifecycle_config_prop = aws_sagemaker.CfnNotebookInstanceLifecycleConfig.NotebookInstanceLifecycleHookProperty(
      content=cdk.Fn.base64(rds_wb_lifecycle_content)
    )

    rds_wb_lifecycle_config = aws_sagemaker.CfnNotebookInstanceLifecycleConfig(self, 'MySQLWorkbenchLifeCycleConfig',
      notebook_instance_lifecycle_config_name='MySQLWorkbenchLifeCycleConfig',
      on_start=[rds_wb_lifecycle_config_prop]
    )

    rds_workbench = aws_sagemaker.CfnNotebookInstance(self, 'AuroraMySQLWorkbench',
      instance_type='ml.t3.xlarge',
      role_arn=sagemaker_notebook_role.role_arn,
      lifecycle_config_name=rds_wb_lifecycle_config.notebook_instance_lifecycle_config_name,
      notebook_instance_name='AuroraMySQLWorkbench',
      root_access='Disabled',
      security_group_ids=[sg_use_mysql.security_group_id],
      subnet_id=vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS).subnet_ids[0]
    )

    cdk.CfnOutput(self, 'StackName', value=self.stack_name, export_name='StackName')
    cdk.CfnOutput(self, 'VpcId', value=vpc.vpc_id, export_name='VpcId')

    cdk.CfnOutput(self, 'DBClusterName', value=db_cluster.cluster_identifier, export_name='DBClusterName')
    cdk.CfnOutput(self, 'DBCluster', value=db_cluster.cluster_endpoint.socket_address, export_name='DBCluster')
    #XXX: https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_secretsmanager/README.html
    # secret_arn="arn:aws:secretsmanager:<region>:<account-id-number>:secret:<secret-name>-<random-6-characters>",
    cdk.CfnOutput(self, 'DBSecret', value=db_cluster.secret.secret_name, export_name='DBSecret')

    cdk.CfnOutput(self, 'SageMakerRole', value=sagemaker_notebook_role.role_name, export_name='SageMakerRole')
    cdk.CfnOutput(self, 'SageMakerNotebookInstance', value=rds_workbench.notebook_instance_name, export_name='SageMakerNotebookInstance')
    cdk.CfnOutput(self, 'SageMakerNotebookInstanceLifecycleConfig', value=rds_workbench.lifecycle_config_name, export_name='SageMakerNotebookInstanceLifecycleConfig')


app = cdk.App()
SagemakerAuroraMysqlStack(app, "sagemaker-aurora-mysql", env=cdk.Environment(
  account=os.environ["CDK_DEFAULT_ACCOUNT"],
  region=os.environ["CDK_DEFAULT_REGION"]))

app.synth()
