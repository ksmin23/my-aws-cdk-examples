#!/usr/bin/env python3
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

random.seed(43)

class SageMakerStudioStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    sagemaker_execution_policy_doc = aws_iam.PolicyDocument()
    sagemaker_execution_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": ["arn:aws:s3:::*"],
      "actions": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ]
    }))

    #XXX: Permissions for AWS Glue Interactive Sessions in SageMaker Studio
    # For more information, see https://docs.aws.amazon.com/sagemaker/latest/dg/getting-started-glue-sm.html#glue-sm-iam
    sagemaker_custom_access_policy_doc = aws_iam.PolicyDocument()
    sagemaker_custom_access_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": ["*"],
      "actions": [
		    "iam:GetRole",
        "iam:PassRole",
        "sts:GetCallerIdentity"
      ]
    }))

    sagemaker_docker_build_policy_doc = aws_iam.PolicyDocument()
    sagemaker_docker_build_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": ["*"],
      "actions": ["ecr:GetAuthorizationToken"]
    }))

    sagemaker_docker_build_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": ["*"],
      "actions": [
        "ecr:BatchGetImage",
        "ecr:BatchCheckLayerAvailability",
        "ecr:CompleteLayerUpload",
        "ecr:DescribeImages",
        "ecr:DescribeRepositories",
        "ecr:GetDownloadUrlForLayer",
        "ecr:InitiateLayerUpload",
        "ecr:ListImages",
        "ecr:PutImage",
        "ecr:UploadLayerPart",
        "ecr:CreateRepository",
        "ecr:GetAuthorizationToken",
        "ec2:DescribeAvailabilityZones"
      ]
    }))

    sagemaker_docker_build_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": ["arn:aws:codebuild:*:*:project/sagemaker-studio*"],
      "actions": [
        "codebuild:DeleteProject",
        "codebuild:CreateProject",
        "codebuild:BatchGetBuilds",
        "codebuild:StartBuild"
      ]
    }))

    sagemaker_docker_build_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": ["arn:aws:logs:*:*:log-group:/aws/codebuild/sagemaker-studio*"],
      "actions": ["logs:CreateLogStream"],
    }))

    sagemaker_docker_build_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": ["arn:aws:logs:*:*:log-group:/aws/codebuild/sagemaker-studio*:log-stream:*"],
      "actions": [
        "logs:GetLogEvents",
        "logs:PutLogEvents"
      ]
    }))

    sagemaker_docker_build_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": ["*"],
      "actions": ["logs:CreateLogGroup"]
    }))

    sagemaker_docker_build_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": ["arn:aws:s3:::sagemaker-*/*"],
      "actions": [
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:PutObject"
      ]
    }))

    sagemaker_docker_build_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": ["arn:aws:s3:::sagemaker*"],
      "actions": ["s3:CreateBucket"],
    }))

    sagemaker_docker_build_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": ["*"],
      "actions": [
        "iam:GetRole",
        "iam:ListRoles"
      ]
    }))

    sagemaker_docker_build_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": ["arn:aws:iam::*:role/*"],
      "conditions": {
        "StringLikeIfExists": {
          "iam:PassedToService": [
            "codebuild.amazonaws.com"
          ]
        }
      },
      "actions": ["iam:PassRole"]
    }))

    sagemaker_execution_role = aws_iam.Role(self, 'SageMakerExecutionRole',
      role_name='AmazonSageMakerExecutionRole-{suffix}'.format(suffix=''.join(random.choices((string.digits), k=5))),
      assumed_by=aws_iam.ServicePrincipal('sagemaker.amazonaws.com'),
      path='/',
      inline_policies={
        'sagemaker-execution-policy': sagemaker_execution_policy_doc,
        'sagemaker-custom-access-policy': sagemaker_custom_access_policy_doc,
        'sagemaker-docker-build-policy': sagemaker_docker_build_policy_doc,
      },
      managed_policies=[
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonSageMakerFullAccess'),
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonSageMakerCanvasFullAccess'),
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('AWSCloudFormationReadOnlyAccess'),
        #XXX: Permissions for AWS Glue Interactive Sessions in SageMaker Studio
        # For more information, see https://docs.aws.amazon.com/sagemaker/latest/dg/getting-started-glue-sm.html#glue-sm-iam
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AwsGlueSessionUserRestrictedServiceRole')
      ]
    )

    #XXX: To use the sm-docker CLI, the Amazon SageMaker execution role used by the Studio notebook
    # environment should have a trust policy with CodeBuild
    sagemaker_execution_role.assume_role_policy.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "principals": [aws_iam.ServicePrincipal('codebuild.amazonaws.com')],
      "actions": ["sts:AssumeRole"]
    }))

    #XXX: Permissions for AWS Glue Interactive Sessions in SageMaker Studio
    # For more information, see https://docs.aws.amazon.com/sagemaker/latest/dg/getting-started-glue-sm.html#glue-sm-iam
    sagemaker_execution_role.assume_role_policy.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "principals": [aws_iam.ServicePrincipal('glue.amazonaws.com')],
      "actions": ["sts:AssumeRole"]
    }))

    sm_studio_user_settings = aws_sagemaker.CfnDomain.UserSettingsProperty(
      execution_role=sagemaker_execution_role.role_arn
    )

    sagemaker_studio_domain = aws_sagemaker.CfnDomain(self, 'SageMakerStudioDomain',
      auth_mode='IAM', # [SSO | IAM]
      default_user_settings=sm_studio_user_settings,
      domain_name='studio-glue-interactive-sessions',
      subnet_ids=vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS).subnet_ids,
      vpc_id=vpc.vpc_id,
      app_network_access_type='PublicInternetOnly' # [PublicInternetOnly | VpcOnly]
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
      )
    )

    sagemaker_user_profile = aws_sagemaker.CfnUserProfile(self, 'SageMakerStudioUserProfile',
      domain_id=sagemaker_studio_domain.attr_domain_id,
      user_profile_name='default-user',
      user_settings=default_user_settings
    )

    cdk.CfnOutput(self, 'DomainUrl', value=sagemaker_studio_domain.attr_url,
                  export_name=f'{self.stack_name}-DomainUrl')
    cdk.CfnOutput(self, 'DomainId', value=sagemaker_user_profile.domain_id,
                  export_name=f'{self.stack_name}-DomainId')
    cdk.CfnOutput(self, 'UserProfileName', value=sagemaker_user_profile.user_profile_name,
                  export_name=f'{self.stack_name}-UserProfileName')

