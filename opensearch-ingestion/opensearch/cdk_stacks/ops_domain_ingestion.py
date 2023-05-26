import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_logs,
  aws_osis
)
from constructs import Construct


class OpsDomainIngestionStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, pipeline_role_arn, opensearch_domain_endpoint, sg_opensearch_cluster, vpc, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    pipeline_name = self.node.try_get_context("osis_pipeline_name") or "ingestion-pipeline"

    pipeline_configuration_body = f'''version: "2"
log-pipeline:
  source:
    http:
      path: "/${{pipelineName}}/test_ingestion_path"
  processor:
    - date:
        from_time_received: true
        destination: "@timestamp"
  sink:
    - opensearch:
        hosts: [ "https://{opensearch_domain_endpoint}" ]
        index: "application_logs"
        aws:
          sts_role_arn: "{pipeline_role_arn}"
          region: "{cdk.Aws.REGION}"'''

    osis_pipeline_log_group = aws_logs.LogGroup(self, 'OSISPipelineLogGroup',
      log_group_name=f"/aws/vendedlogs/OpenSearchIngestion/{pipeline_name}/audit-logs",
      retention=aws_logs.RetentionDays.THREE_DAYS,
      # removal_policy=cdk.RemovalPolicy.DESTROY
      removal_policy=cdk.RemovalPolicy.RETAIN
    )

    cfn_pipeline = aws_osis.CfnPipeline(self, "CfnOSISPipeline",
      max_units=4,
      min_units=1,
      pipeline_configuration_body=pipeline_configuration_body,
      pipeline_name=pipeline_name,

      # the properties below are optional
      log_publishing_options=aws_osis.CfnPipeline.LogPublishingOptionsProperty(
        cloud_watch_log_destination=aws_osis.CfnPipeline.CloudWatchLogDestinationProperty(
          log_group=osis_pipeline_log_group.log_group_name,
        ),
        is_logging_enabled=True
      ),
      vpc_options=aws_osis.CfnPipeline.VpcOptionsProperty(
        security_group_ids=[sg_opensearch_cluster.security_group_id],
        subnet_ids=vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS).subnet_ids
      )
    )

    cdk.CfnOutput(self, f'{self.stack_name}-PipelineName', value=cfn_pipeline.pipeline_name)
