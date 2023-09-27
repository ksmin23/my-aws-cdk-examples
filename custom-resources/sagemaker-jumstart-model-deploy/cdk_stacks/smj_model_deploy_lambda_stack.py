from urllib.parse import urlparse

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_iam,
  aws_lambda
)
from constructs import Construct

class JumpStartModelDeployLambdaStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, lambda_layer, sagemaker_iam_role_arn, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    lambda_execution_role = aws_iam.Role(self, 'SMJumpStartModelDeployLambdaRole',
      role_name=f'{self.stack_name}-LambdaExecRole',
      assumed_by=aws_iam.ServicePrincipal('lambda.amazonaws.com'),
      managed_policies=[
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AWSLambdaBasicExecutionRole'),
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonSageMakerFullAccess')
      ]
    )

    SMJ_MODEL_INFO = self.node.try_get_context('sagemaker_jumpstart_model_info')
    model_id = SMJ_MODEL_INFO['model_id']
    endpoint_name = SMJ_MODEL_INFO['endpoint_name']

    #XXX: AWS Lambda - Defined runtime environment variables
    # https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html#configuration-envvars-runtime
    lambda_fn_env = {
      'MODEL_ID': model_id,
      'ENDPOINT_NAME': endpoint_name,
      'SAGEMAKER_IAM_ROLE_ARN': sagemaker_iam_role_arn
    }

    lambda_fn = aws_lambda.Function(self, "SMJumpStartModelDeployLambdaFn",
      runtime=aws_lambda.Runtime.PYTHON_3_10,
      function_name=f"{self.stack_name}-Function",
      handler="smj_model_deploy_lambda_fn.lambda_handler",
      description="SageMaker Jumpstart Model Deployment",
      code=aws_lambda.Code.from_asset('./src/main/python/CustomResourceProvider'),
      layers=[lambda_layer],
      environment=lambda_fn_env,
      timeout=cdk.Duration.minutes(15),
      memory_size=512,
      role=lambda_execution_role
    )

    self.lambda_function_arn = lambda_fn.function_arn

    cdk.CfnOutput(self, 'LambdaFnName', value=lambda_fn.function_name,
      export_name=f"{self.stack_name}-LambdaFnName")
