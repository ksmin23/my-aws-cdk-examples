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

    sagemaker_endpoint_role = aws_iam.Role(self, 'SageMakerEndpointRole',
      role_name='AmazonSageMakerEndpointRole-{suffix}'.format(suffix=''.join(random.choices((string.digits), k=5))),
      assumed_by=aws_iam.ServicePrincipal('sagemaker.amazonaws.com'),
      path='/',
      managed_policies=[
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('IAMReadOnlyAccess'),
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonSageMakerReadOnly'),
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonS3ReadOnlyAccess'),
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('CloudWatchLogsFullAccess'),
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AWSAppRunnerServicePolicyForECRAccess'),
      ]
    )

    self.sagemaker_endpoint_role_arn = sagemaker_endpoint_role.role_arn

    cdk.CfnOutput(self, 'SageMakerExecutionRoleName', value=sagemaker_endpoint_role.role_name,
      export_name=f'{self.stack_name}-RoleName')
    cdk.CfnOutput(self, 'SageMakerExecutionRoleArn', value=self.sagemaker_endpoint_role_arn,
      export_name=f'{self.stack_name}-RoleArn')
