#!/usr/bin/env python3
import os

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_lambda,
  aws_s3 as s3
)
from constructs import Construct


class LambdaLayersStack(Stack):

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

    # vpc = aws_ec2.Vpc(self, 'LambdaLayersVPC',
    #   max_azs=3,
    #   gateway_endpoints={
    #     "S3": aws_ec2.GatewayVpcEndpointOptions(
    #       service=aws_ec2.GatewayVpcEndpointAwsService.S3
    #     )
    #   }
    # )

    S3_BUCKET_LAMBDA_LAYER_LIB = self.node.try_get_context('s3_bucket_lambda_layer_lib')
    s3_lib_bucket = s3.Bucket.from_bucket_name(self, construct_id, S3_BUCKET_LAMBDA_LAYER_LIB)
    pytz_lib_layer = aws_lambda.LayerVersion(self, "PyTZLib",
      layer_version_name="pytz-lib",
      compatible_runtimes=[aws_lambda.Runtime.PYTHON_3_7],
      code=aws_lambda.Code.from_bucket(s3_lib_bucket, "var/pytz-lib.zip")
    )

    es_lib_layer = aws_lambda.LayerVersion(self, "ESLib",
      layer_version_name="es-lib",
      compatible_runtimes=[aws_lambda.Runtime.PYTHON_3_7],
      code=aws_lambda.Code.from_bucket(s3_lib_bucket, "var/es-lib.zip")
    )

    lambda_fn = aws_lambda.Function(self, "LambdaLayerTest",
      runtime=aws_lambda.Runtime.PYTHON_3_7,
      function_name="LambdaLayerTest",
      handler="lambda_layer_test.lambda_handler",
      description="Lambda Layer Test",
      code=aws_lambda.Code.from_asset("./src/main/python"),
      timeout=cdk.Duration.minutes(5),
      layers=[es_lib_layer, pytz_lib_layer],
      vpc=vpc
    )


app = cdk.App()
LambdaLayersStack(app, "LambdaLayersStack",  env=cdk.Environment(
  account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION')))

app.synth()
