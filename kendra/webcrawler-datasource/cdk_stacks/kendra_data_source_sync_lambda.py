from urllib.parse import urlparse

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_iam,
  aws_lambda,
  aws_s3 as s3
)
from constructs import Construct

class KendraDataSourceSyncLambdaStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, kendra_index_id, kendra_data_source_id, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    kendra_data_source_sync_lambda_role_policy_doc = aws_iam.PolicyDocument()
    kendra_data_source_sync_lambda_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": [f"arn:aws:kendra:{cdk.Aws.REGION}:{cdk.Aws.ACCOUNT_ID}:index/{kendra_index_id}*"],
      "actions": [
        "kendra:*"
      ]
    }))

    kendra_data_source_sync_lambda_role = aws_iam.Role(self, 'KendraDataSourceSyncLambdaRole',
      role_name=f'{self.stack_name}-DocsKendraDataSourceRole',
      assumed_by=aws_iam.ServicePrincipal('lambda.amazonaws.com'),
      inline_policies={
        'KendraDataSourceSyncLambdaPolicy': kendra_data_source_sync_lambda_role_policy_doc
      },
      managed_policies=[
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AWSLambdaBasicExecutionRole')
      ]
    )

    LAMBDA_LAYER_LIB_S3_PATH = self.node.try_get_context('lambda_layer_lib_s3_path')
    parse_result = urlparse(LAMBDA_LAYER_LIB_S3_PATH)
    S3_BUCKET_NAME = parse_result.netloc
    lambda_layer_s3_bucket = s3.Bucket.from_bucket_name(self, "LambdaLayerS3Bucket", S3_BUCKET_NAME)
    lambda_layer_s3_object_key = parse_result.path.lstrip('/')

    py_cfnresponse_lib = aws_lambda.LayerVersion(self, "CfnResponseLib",
      layer_version_name="py-cfnresponse-lib",
      compatible_runtimes=[aws_lambda.Runtime.PYTHON_3_10],
      code=aws_lambda.Code.from_bucket(lambda_layer_s3_bucket, lambda_layer_s3_object_key),
      removal_policy=cdk.RemovalPolicy.DESTROY
    )

    #XXX: AWS Lambda - Defined runtime environment variables
    # https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html#configuration-envvars-runtime
    lambda_fn_env = {
      'INDEX_ID': kendra_index_id,
      'DS_ID': kendra_data_source_id
    }

    kendra_data_source_sync_lambda_fn = aws_lambda.Function(self, "KendraDataSourceSyncLambdaFn",
      runtime=aws_lambda.Runtime.PYTHON_3_10,
      function_name=f"{self.stack_name}-Function",
      handler="kendra_ds_sync_lambda_fn.lambda_handler",
      description="Kendra Data Source Sync Lambda Function",
      code=aws_lambda.Code.from_asset('./src/main/python/KendraDataSourceSync'),
      layers=[py_cfnresponse_lib],
      environment=lambda_fn_env,
      timeout=cdk.Duration.minutes(15),
      memory_size=1024,
      role=kendra_data_source_sync_lambda_role
    )

    self.kendra_ds_sync_lambda_arn = kendra_data_source_sync_lambda_fn.function_arn

    cdk.CfnOutput(self, 'KendraDSSyncLambdaFnName', value=kendra_data_source_sync_lambda_fn.function_name,
      export_name=f"{self.stack_name}-KendraDSSyncLambdaFnName")

