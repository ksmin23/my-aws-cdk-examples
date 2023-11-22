#!/usr/bin/env python3

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_emr
)
from constructs import Construct

class EmrStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    EMR_CLUSTER_NAME = cdk.CfnParameter(self, 'EMRClusterName',
      type='String',
      description='Amazon EMR Cluster name',
      default='my-emr-cluster'
    )

    emr_instances = aws_emr.CfnCluster.JobFlowInstancesConfigProperty(
      core_instance_group=aws_emr.CfnCluster.InstanceGroupConfigProperty(
        instance_count=2,
        instance_type="m5.xlarge",
        market="ON_DEMAND"
      ),
      ec2_subnet_id=vpc.public_subnets[0].subnet_id,
      keep_job_flow_alive_when_no_steps=True, # After last step completes: Cluster waits
      master_instance_group=aws_emr.CfnCluster.InstanceGroupConfigProperty(
        instance_count=1,
        instance_type="m5.xlarge",
        market="ON_DEMAND"
      ),
      termination_protected=True
    )

    emr_copy_jar_step_config = aws_emr.CfnCluster.StepConfigProperty(
      hadoop_jar_step=aws_emr.CfnCluster.HadoopJarStepConfigProperty(
        jar="command-runner.jar",

        # the properties below are optional
        args=[
          "bash",
          "-c",
          "; ".join([
            "hdfs dfs -mkdir -p /apps/hudi/lib",
            "hdfs dfs -copyFromLocal /usr/lib/hudi/hudi-spark-bundle.jar /apps/hudi/lib/hudi-spark-bundle.jar",
            "hdfs dfs -copyFromLocal /usr/lib/spark/external/lib/spark-avro.jar /apps/hudi/lib/spark-avro.jar",
            "hdfs dfs -mkdir -p /apps/iceberg/lib",
            "hdfs dfs -copyFromLocal /usr/share/aws/iceberg/lib/iceberg-spark3-runtime.jar /apps/iceberg/lib/iceberg-spark3-runtime.jar"
          ])
        ]
      ),
      name="CopyJarsToHDFS",
      action_on_failure="CONTINUE"
    )

    emr_cfn_cluster = aws_emr.CfnCluster(self, "MyEMRCluster",
      instances=emr_instances,
      # In order to use the default role for `job_flow_role`, you must have already created it using the CLI or console
      job_flow_role="EMR_EC2_DefaultRole",
      name=EMR_CLUSTER_NAME.value_as_string,
      # service_role="EMR_DefaultRole_V2",
      service_role="EMR_DefaultRole",
      applications=[
        aws_emr.CfnCluster.ApplicationProperty(name="Hadoop"),
        aws_emr.CfnCluster.ApplicationProperty(name="Hive"),
        aws_emr.CfnCluster.ApplicationProperty(name="JupyterHub"),
        aws_emr.CfnCluster.ApplicationProperty(name="Livy"),
        aws_emr.CfnCluster.ApplicationProperty(name="Spark"),
        aws_emr.CfnCluster.ApplicationProperty(name="JupyterEnterpriseGateway")
      ],
      bootstrap_actions=None,
      configurations=[
        aws_emr.CfnCluster.ConfigurationProperty(
          classification="hive-site",
          configuration_properties={
            "hive.metastore.client.factory.class": "com.amazonaws.glue.catalog.metastore.AWSGlueDataCatalogHiveClientFactory"
        }),
        aws_emr.CfnCluster.ConfigurationProperty(
          classification="spark-hive-site",
          configuration_properties={
            "hive.metastore.client.factory.class": "com.amazonaws.glue.catalog.metastore.AWSGlueDataCatalogHiveClientFactory"
        })
      ],
      ebs_root_volume_size=10,
      log_uri="s3n://aws-logs-{account}-{region}/elasticmapreduce/".format(account=cdk.Aws.ACCOUNT_ID, region=cdk.Aws.REGION),
      release_label="emr-6.7.0",
      steps=[
        emr_copy_jar_step_config
      ],
      scale_down_behavior="TERMINATE_AT_TASK_COMPLETION",
      # tags=[cdk.CfnTag(
      #   key="for-use-with-amazon-emr-managed-policies",
      #   value="true"
      # )],
      visible_to_all_users=True
    )

    cdk.CfnOutput(self, 'ClusterName', value=emr_cfn_cluster.name,
      export_name=f'{self.stack_name}-ClusterName')
    cdk.CfnOutput(self, 'EMRReleaseLabel', value=emr_cfn_cluster.release_label,
      export_name=f'{self.stack_name}-ReleaseLabel')
    cdk.CfnOutput(self, 'EMRMasterPublicDNS', value=emr_cfn_cluster.attr_master_public_dns,
      export_name=f'{self.stack_name}-MasterPublicDNS')
