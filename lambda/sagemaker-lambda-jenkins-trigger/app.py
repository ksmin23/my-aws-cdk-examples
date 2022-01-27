#!/usr/bin/env python3
import os
import json

from aws_cdk import (
  core as cdk,
  aws_events,
  aws_events_targets,
  aws_iam,
  aws_lambda,
  aws_secretsmanager
)


class SageMakerLambdaJenkinsTriggerStack(cdk.Stack):

  def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    JENKINS_USER = cdk.CfnParameter(self, 'JenkinsUser',
      type='String',
      description='Jenkins user name'
    )

    JENKINS_API_TOKEN = cdk.CfnParameter(self, 'JenkinsAPIToken',
      type='String',
      description='Jenkins user api token',
      no_echo=True
    )

    JENKINS_URL = cdk.CfnParameter(self, 'JenkinsUrl',
      type='String',
      description='Jenkins url'
    )

    secret_value = aws_secretsmanager.SecretStringValueBeta1.from_token(
      json.dumps({JENKINS_USER.value_as_string: JENKINS_API_TOKEN.value_as_string}))

    jenkins_api_user_token_secret = aws_secretsmanager.Secret(self, "JenkinsAPIUserTokenSecret",
      secret_string_beta1=secret_value,
      description="Secret to store jenkins username and personal access token"
    )

    jenkins_trigger_lambda_fn = aws_lambda.Function(self, "LambdaJenkinsTrigger",
      runtime=aws_lambda.Runtime.PYTHON_3_8,
      function_name="SageMakerJenkins-LambdaJenkinsTrigger",
      handler="lambda_jenkins_trigger.lambda_handler",
      description="Lambda function invoked by SageMaker Model Package State change",
      code=aws_lambda.Code.from_asset(os.path.join(os.path.dirname(__file__), 'src/main/python')),
      environment={
        "JenkinsAPIUserTokenSecret": jenkins_api_user_token_secret.secret_name,
        "JenkinsUrl": JENKINS_URL.value_as_string,
      },
      timeout=cdk.Duration.minutes(5)
    )

    jenkins_trigger_lambda_fn.add_to_role_policy(aws_iam.PolicyStatement(
      effect=aws_iam.Effect.ALLOW,
      resources=["arn:aws:secretsmanager:*:*:*"],
      actions=["secretsmanager:GetSecretValue"]))

    jenkins_trigger_lambda_fn.add_to_role_policy(aws_iam.PolicyStatement(
      effect=aws_iam.Effect.ALLOW,
      resources=["arn:aws:logs:*:*:*"],
      actions=["logs:*"]))

    event_rule = aws_events.Rule(self, "JenkinsTriggerRule",
      rule_name="SageMakerJenkinsTriggerRule",
      event_pattern={
        "account": [self.account],
        "source": ["aws.sagemaker"],
        "detail_type": ["SageMaker Model Package State Change"],
        "detail": {
           "ModelApprovalStatus": [
             "Approved",
             "Rejected"
           ]
        }
      },
      description='''Rule to trigger a deployment when SageMaker Model registry is updated with a new model package.
For example, a new model package is registered with Registry'''
    )
    event_rule.add_target(aws_events_targets.LambdaFunction(jenkins_trigger_lambda_fn))
    event_rule.apply_removal_policy(cdk.RemovalPolicy.DESTROY)

    cdk.CfnOutput(self, 'JenkinsAPIUserTokenSecretName',
      value=jenkins_api_user_token_secret.secret_name, export_name='JenkinsAPIUserTokenSecret')
    cdk.CfnOutput(self, 'JenkinsTriggerLambdaFunctionName',
      value=jenkins_trigger_lambda_fn.function_name, export_name='LambdaJenkinsTrigger')


app = cdk.App()
SageMakerLambdaJenkinsTriggerStack(app, "SageMakerLambdaJenkinsTriggerStack",
  env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'),
    region=os.getenv('CDK_DEFAULT_REGION')))

app.synth()
