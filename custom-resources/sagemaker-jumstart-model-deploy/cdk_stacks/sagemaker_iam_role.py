#!/usr/bin/env python3
import random
import string

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_iam
)
from constructs import Construct

random.seed(47)


class SageMakerIAMRoleStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
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
      role_name='AmazonSageMakerStudioExecutionRole-{suffix}'.format(suffix=''.join(random.choices((string.digits), k=5))),
      assumed_by=aws_iam.ServicePrincipal('sagemaker.amazonaws.com'),
      path='/',
      inline_policies={
        'sagemaker-execution-policy': sagemaker_execution_policy_doc,
        'sagemaker-docker-build-policy': sagemaker_docker_build_policy_doc,
      },
      managed_policies=[
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonSageMakerReadOnly'),
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('AWSCloudFormationReadOnlyAccess'),
      ]
    )

    #XXX: To use the sm-docker CLI, the Amazon SageMaker execution role used by the Studio notebook
    # environment should have a trust policy with CodeBuild
    sagemaker_execution_role.assume_role_policy.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "principals": [aws_iam.ServicePrincipal('codebuild.amazonaws.com')],
      "actions": ["sts:AssumeRole"]
    }))

    self.sagemaker_execution_role_arn = sagemaker_execution_role.role_arn

    cdk.CfnOutput(self, 'SageMakerExecutionRoleName', value=sagemaker_execution_role.role_name,
      export_name=f'{self.stack_name}-RoleName')
    cdk.CfnOutput(self, 'SageMakerExecutionRoleArn', value=self.sagemaker_execution_role_arn,
      export_name=f'{self.stack_name}-RoleArn')
