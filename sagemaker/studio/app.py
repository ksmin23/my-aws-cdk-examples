#!/usr/bin/env python3
import os
import random
import string

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_iam,
  aws_s3 as s3,
  aws_sagemaker
)
from constructs import Construct

random.seed(47)

class SageMakerStudioStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    #XXX: For creating this CDK Stack in the existing VPC,
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

    #XXX: To use more than 2 AZs, be sure to specify the account and region on your stack.
    #XXX: https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_ec2/Vpc.html
    # vpc = aws_ec2.Vpc(self, 'SageMakerStudioVPC',
    #   max_azs=2,
    #   gateway_endpoints={
    #     "S3": aws_ec2.GatewayVpcEndpointOptions(
    #       service=aws_ec2.GatewayVpcEndpointAwsService.S3
    #     )
    #   }
    # )

    sg_sm_instance = aws_ec2.SecurityGroup(self, "SageMakerStudioSG",
      vpc=vpc,
      allow_all_outbound=True,
      description='Security group with no ingress rule',
      security_group_name='sagemaker-studio-sg'
    )
    sg_sm_instance.add_ingress_rule(peer=sg_sm_instance, connection=aws_ec2.Port.all_traffic(), description='sagemaker studio security group')
    cdk.Tags.of(sg_sm_instance).add('Name', 'sagemaker-studio-sg')

    sagemaker_execution_policy_doc = aws_iam.PolicyDocument()
    sagemaker_execution_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": ["arn:aws:s3:::*"],
      "actions": ["s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"]
    }))

    sagemaker_emr_execution_policy_doc = aws_iam.PolicyDocument()
    sagemaker_emr_execution_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": ["*"],
      "actions": ["iam:PassRole"],
      "conditions": {
        "StringEquals": {
          "iam:PassedToService": "sagemaker.amazonaws.com"
        }
      },
      "sid": "AllowPassRoleSageMaker"
    }))

    sagemaker_emr_execution_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": ["*"],
      "actions": ["elasticmapreduce:ListInstances",
        "elasticmapreduce:DescribeCluster",
        "elasticmapreduce:DescribeSecurityConfiguration",
        "iam:CreateServiceLinkedRole",
        "iam:GetRole"]
    }))

    sagemaker_emr_execution_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": ["arn:aws:elasticmapreduce:*:*:cluster/*"],
      "actions": ["elasticmapreduce:DescribeCluster",
        "elasticmapreduce:ListInstanceGroups"]
    }))

    sagemaker_emr_execution_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": ["*"],
      "actions": ["elasticmapreduce:ListClusters"]
    }))

    sagemaker_emr_execution_role = aws_iam.Role(self, 'SageMakerExecutionRole',
      role_name='AmazonSageMakerStudioExecutionRole-{suffix}'.format(suffix=''.join(random.choices((string.digits), k=5))),
      assumed_by=aws_iam.ServicePrincipal('sagemaker.amazonaws.com'),
      path='/',
      inline_policies={
        'sagemaker-execution-policy': sagemaker_execution_policy_doc,
        #XXX: add additional IAM Policy to use EMR in SageMaker Studio
        # https://aws.amazon.com/blogs/machine-learning/amazon-sagemaker-studio-notebooks-backed-by-spark-in-amazon-emr/
        'sagemaker-emr': sagemaker_emr_execution_policy_doc
      },
      managed_policies=[
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonSageMakerFullAccess'),
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonSageMakerCanvasFullAccess')
      ]
    )

    sm_studio_user_settings = aws_sagemaker.CfnDomain.UserSettingsProperty(
      execution_role=sagemaker_emr_execution_role.role_arn,
      security_groups=[sg_sm_instance.security_group_id]
    )

    sagemaker_studio_domain = aws_sagemaker.CfnDomain(self, 'SageMakerStudioDomain',
      auth_mode='IAM', # [SSO | IAM]
      default_user_settings=sm_studio_user_settings,
      domain_name='sm-studio-workshop',
      subnet_ids=vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS).subnet_ids,
      vpc_id=vpc.vpc_id,
      app_network_access_type='VpcOnly' # [PublicInternetOnly | VpcOnly]
    )

    #XXX: https://docs.aws.amazon.com/sagemaker/latest/dg/studio-jl.html#studio-jl-set
    sagmaker_jupyerlab_arn = self.node.try_get_context('sagmaker_jupyterlab_arn')

    default_user_settings = aws_sagemaker.CfnUserProfile.UserSettingsProperty(
      jupyter_server_app_settings=aws_sagemaker.CfnUserProfile.JupyterServerAppSettingsProperty(
        default_resource_spec=aws_sagemaker.CfnUserProfile.ResourceSpecProperty(
          #XXX: JupyterServer apps only support the system value.
          instance_type="system",
          sage_maker_image_arn=sagmaker_jupyerlab_arn
        )
      ),
      security_groups=[sg_sm_instance.security_group_id]
    )

    sagemaker_user_profile = aws_sagemaker.CfnUserProfile(self, 'SageMakerStudioUserProfile',
      domain_id=sagemaker_studio_domain.attr_domain_id,
      user_profile_name='default-user',
      user_settings=default_user_settings
    )

    cdk.CfnOutput(self, f'{self.stack_name}-DomainId', value=sagemaker_user_profile.domain_id)
    cdk.CfnOutput(self, f'{self.stack_name}-UserProfileName', value=sagemaker_user_profile.user_profile_name)


app = cdk.App()
SageMakerStudioStack(app, "SageMakerStudioStack", env=cdk.Environment(
  account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION')))

app.synth()
