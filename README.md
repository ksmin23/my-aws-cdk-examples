# AWS CDK Python Examples

![Stats](https://img.shields.io/badge/118-CDK_Projects-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)


This repository contains a set of [AWS Cloud Development Kit](https://docs.aws.amazon.com/cdk/api/latest/) Python examples with architecture diagrams for frequently used AWS services.

| Example | Description | Tags |
|---------|-------------|------|
| [api-gateway/cognito-api-lambda](./api-gateway/cognito-api-lambda/) | ![amazon-cognito-api-lambda](./api-gateway/cognito-api-lambda/amazon-cognito-api-lambda.svg) | api-gateway, cognito, lambda |
| [api-gateway/dynamodb](./api-gateway/dynamodb/) | ![apigw-dynamodb-arch](./api-gateway/dynamodb/apigw-dynamodb-arch.svg) | api-gateway, dynamodb |
| [api-gateway/dynamodb-cognito](./api-gateway/dynamodb-cognito/) | ![apigw-cognito-dynamodb-arch](./api-gateway/dynamodb-cognito/apigw-cognito-dynamodb-arch.svg) | api-gateway, cognito, dynamodb |
| [api-gateway/http-dynamodb-crud-api](./api-gateway/http-dynamodb-crud-api/) | ![http-dynamodb-crud-api](./api-gateway/http-dynamodb-crud-api/dynamodb_crud_http_api.svg) | api-gateway(HTTP API), dynamodb, lambda |
| [api-gateway/kds-proxy](./api-gateway/kds-proxy/) | ![apigw-kds-proxy-arch](./api-gateway/kds-proxy/apigw-kds-proxy-arch.svg) | api-gateway, kinesis data streams |
| [api-gateway/kds-proxy-cognito](./api-gateway/kds-proxy-cognito/) | ![apigw-kds-proxy-cognito-arch](./api-gateway/kds-proxy-cognito/apigw-kds-proxy-cognito-arch.svg) | api-gateway, cognito, kinesis data streams |
| [api-gateway/logging-api-calls-to-firehose](./api-gateway/logging-api-calls-to-firehose/) | ![logging-api-calls-to-firehose](./api-gateway/logging-api-calls-to-firehose/logging-api-calls-to-firehose.svg) | api-gateway, kinesis data firehose |
| [api-gateway/logging-api-calls-to-cloudwatch-logs](./api-gateway/logging-api-calls-to-cloudwatch-logs/) | ![logging-api-calls-to-cloudwatch-logs](./api-gateway/logging-api-calls-to-cloudwatch-logs/logging-api-calls-to-cloudwatch-logs.svg) | api-gateway, cloudwatch logs subscription filters with kinesis data firehose |
| [athena](./athena/) | ![athena-arch](./athena/aws-athena-arch.svg) | athena (named query, work group), s3 |
| [batch/batch-with-ec2](./batch/batch-with-ec2/) | Launch AWS Batch | aws batch |
| [bedrock/opensearch-serverless](./bedrock/cfn/opensearch-serverless/) | Launch Knowledge Bases for Amazon Bedrock using Amazon OpenSearch Serverless as a vector store| amazon bedrock, knowledge bases, opensearch serverless |
| [bedrock/generative-ai-cdk-constructs](./bedrock/generative-ai-cdk-constructs) | Launch Knowledge Bases for Amazon Bedrock | amazon bedrock, knowledge bases |
| [cloud9](./cloud9/) | ![cloud9](./cloud9/aws-cloud9.svg) | cloud9 |
| [cloudfront/static-site](./cloudfront/static-site/) | ![cloudfront-s3-static-site-arch](./cloudfront/static-site/cloudfront-s3-static-site-arch.svg) | cloudfront |
| [custom-resources/sagemaker-jumstart-model-deploy](./custom-resources/sagemaker-jumstart-model-deploy/) | Deploy SageMaker JumpStart Model with CDK Custom Resources | sagemaker jumpstart, cdk custom-resources |
| [dms/aurora_mysql-to-kinesis](./dms/aurora_mysql-to-kinesis/) | ![dms-mysql-to-kinesis-arch](./dms/aurora_mysql-to-kinesis/dms-mysql-to-kinesis-arch.svg) | dms, mysql, kinesis |
| [dms/aurora_mysql-to-s3](./dms/aurora_mysql-to-s3/) | ![dms-mysql-to-s3-arch](./dms/aurora_mysql-to-s3/dms-mysql-to-s3-arch.svg) | dms, mysql, s3 |
| [dms-serverless/aurora_mysql-to-kinesis](./dms-serverless/aurora_mysql-to-kinesis/) | ![dms_serverless-mysql-to-kinesis-arch](./dms-serverless/aurora_mysql-to-kinesis/dms_serverless-mysql-to-kinesis-arch.svg) | dms serverless, mysql, kinesis |
| [dms-serverless/aurora_mysql-to-s3](./dms-serverless/aurora_mysql-to-s3/) | ![dms_serverless-mysql-to-s3-arch](./dms-serverless/aurora_mysql-to-s3/dms_serverless-mysql-to-s3-arch.svg) | dms serverless, mysql, s3 |
| [documentdb](./documentdb/) | ![documentdb-sagemaker-arch](./documentdb/documentdb-sagemaker-arch.svg) | documentdb(docdb), secerts manager, sagemaker|
| [documentdb-elastic-clusters](./documentdb-elastic-clusters/) | ![docdb-elastic-arch](./documentdb-elastic-clusters/docdb-elastic-arch.svg) | documentdb elastic clusters(docdb-elastic), secerts manager|
| [dynamodb](./dynamodb/) | ![dynamodb-arch](./dynamodb/dynamodb-arch.svg) | dynamodb |
| [ec2/vpc](./ec2/vpc/) | ![aws-vpc](./ec2/vpc/aws-vpc.svg) | vpc |
| [ec2/import-existing-vpc](./ec2/import-existing-vpc/) | ![aws-existing-vpc](./ec2/import-existing-vpc/aws-existing-vpc.svg) | vpc |
| [ec2/jenkins-on-ec2](./ec2/jenkins-on-ec2/) | ![jenkins-on-ec2](./ec2/jenkins-on-ec2/jenkins-on-ec2.svg) | jenkins, ec2 |
| [ec2/jupyter-on-dlami](./ec2/jupyter-on-dlami/) | Launch Jupyter Server on Amazon Deep Learning AMI | jupyter, ec2, DLAMI |
| [ec2/dlami-wth-aws-neuron](./ec2/dlami-wth-aws-neuron/) | Launch Jupyter Server on Amazon Deep Learning AMI with AWS Neuron | jupyter, ec2, DLAMI, AWS Neuron |
| [ec2/stable-diffusion-webui-on-dlami](./ec2/stable-diffusion-webui-on-dlami/) | ![Stable_Diffusion_WebUI_Screenshot](./ec2/stable-diffusion-webui-on-dlami/SD-WebUI-Screenshot.png) | Stable Diffusion WebUI, ec2, DLAMI |
| [ecr](./ecr/) | upload Docker image into Amazon ECR Repository | ecr |
| [ecs-patterns/alb-fargate-service](./ecs-patterns/alb-fargate-service/) | ![ecs-alb-fargate-service-arch](./ecs-patterns/alb-fargate-service/ecs-alb-fargate-service-arch.svg) | ecs patterns, Application Loadbalancer Fargate Service |
| [ecs-patterns/nlb-fargate-service](./ecs-patterns/nlb-fargate-service/) | ![ecs-nlb-fargate-service-arch](./ecs-patterns/nlb-fargate-service/ecs-nlb-fargate-service-arch.svg)  | ecs patterns, Network Loadbalancer Fargate Service |
| [elasticache/redis](./elasticache/redis/) | ![elasticache-redis-arch](./elasticache/redis/elasticache-for-redis-arch.svg) | redis |
| [elasticache/redis-primary-replica](./elasticache/redis-primary-replica/) | ![elasticache-redis-primary-replica-arch](./elasticache/redis-primary-replica/elasticache-for-redis-primary-replica-arch.svg) | redis primary-replica cluster |
| [elasticache/redis-cluster](./elasticache/redis-cluster/) | ![elasticache-redis-cluster-arch](./elasticache/redis-cluster/elasticache-for-redis-cluster-arch.svg) | redis-cluster |
| [elasticache-serverless/serverless-redis-cluster](./elasticache-serverless/serverless-redis-cluster/) | ![elasticache-serverless-for-redis-cluster-arch](./elasticache-serverless/serverless-redis-cluster/elasticache-serverless-for-redis-cluster-arch.svg) | ElastiCache Serverless for Redis |
| [elasticsearch](./elasticsearch/) | ![amazon-es-arch](./elasticsearch/amazon-es-arch.svg) | elasticsearch |
| [opensearch/cfn-domain](./opensearch-service/cfn-domain) | ![amazon-opensearch-arch](./opensearch-service/cfn-domain/amazon-opensearch-arch.svg) | opensearch created with cdk.aws_opensearch.CfnDomain construct |
| [opensearch/domain](./opensearch-service/domain) | ![amazon-opensearch-arch](./opensearch-service/domain/amazon-opensearch-arch.svg) | opensearch created with cdk.aws_opensearch.Domain construct |
| [opensearch-serverless/search](./opensearch-serverless/search) | ![opensearch-serverless-search-type](./opensearch-serverless/search/opensearch-serverless-search-type.svg) | opensearch serverless for search usecases |
| [opensearch-serverless/time-series](./opensearch-serverless/time-series) | ![opensearch-serverless-timeseries-arch](./opensearch-serverless/time-series/opensearch-serverless-timeseries-arch.svg) | opensearch serverless for time series analysis |
| [opensearch-serverless/vpc-endpoint](./opensearch-serverless/vpc-endpoint) | ![opensearch-serverless-vpc-endpoint-arch](./opensearch-serverless/vpc-endpoint/opensearch-serverless-vpc-endpoint-arch.svg) | opensearch serverless in VPC |
| [opensearch-serverless/kinesis-firehose](./opensearch-serverless/kinesis-firehose) | ![opensearch-serverless-firehose-arch](./opensearch-serverless/kinesis-firehose/opensearch-serverless-firehose-arch.svg) | data ingestion to opensearch serverless using kinesis firehose |
| [opensearch-ingestion/opensearch](./opensearch-ingestion/opensearch) | ![osis-domain-pipeline](./opensearch-ingestion/opensearch/osis-domain-pipeline.svg) | data ingestion to opensearch domain using OpenSearch Ingestion Pipelines |
| [opensearch-ingestion/opensearch-serverless](./opensearch-ingestion/opensearch-serverless) | ![osis-collection-pipeline](./opensearch-ingestion/opensearch-serverless/osis-collection-pipeline.svg) | data ingestion to opensearch serverless using OpenSearch Ingestion Pipelines |
| [emr](./emr/) | ![amazon-emr-on_demand](./emr/amazon-emr-on_demand.svg) | emr, Hive, Spark, JupyterHub, Hudi, Iceberg  |
| [emr-serverless](./emr-serverless/) | ![amazon-emr-serverless](./emr-serverless/amazon-emr-serverless.svg) | emr serverless |
| [emr-studio](./emr-studio/) | Launch an Amazon EMR Studio | emr studio |
| [glue/cdc-parquet-to-apache-iceberg](./glue/cdc-parquet-to-apache-iceberg/) | ![glue-job-cdc-parquet-to-iceberg-arch](./glue/cdc-parquet-to-apache-iceberg/glue-job-cdc-parquet-to-iceberg-arch.svg) | aws glue, Apache Iceberg, Parquet |
| [glue/cdc-streams-to-apache-iceberg](./glue/cdc-streams-to-apache-iceberg/) | ![glue-streaming-cdc-to-iceberg-table](./glue/cdc-streams-to-apache-iceberg/glue-streaming-cdc-to-iceberg-table.svg) | aws glue streaming, Apache Iceberg |
| [glue/streaming-etl/sink-to-s3](./glue/streaming-etl/sink-to-s3/) | ![glue-streaming-ingestion-from-kinesis-to-s3-arch](./glue/streaming-etl/sink-to-s3/glue-streaming-to-s3.svg) | aws glue streaming, kinesis data streams, s3, parquet |
| [glue/streaming-etl/sink-to-deltalake](./glue/streaming-etl/sink-to-deltalake/) | ![glue-streaming-ingestion-from-kinesis-to-deltalake-arch](./glue/streaming-etl/sink-to-deltalake/glue-streaming-data-to-deltalake-table.svg) | aws glue streaming, kinesis data streams, s3, Delta Lake |
| [glue/streaming-etl/sink-to-hudi](./glue/streaming-etl/sink-to-hudi/) | ![glue-streaming-ingestion-from-kinesis-to-hudi-arch](./glue/streaming-etl/sink-to-hudi/glue-streaming-data-to-hudi-table.svg) | aws glue streaming, kinesis data streams, s3, Apache Hudi |
| [glue/streaming-etl/sink-to-iceberg](./glue/streaming-etl/sink-to-iceberg/) | ![glue-streaming-ingestion-from-kinesis-to-iceberg-arch](./glue/streaming-etl/sink-to-iceberg/glue-streaming-data-to-iceberg-table.svg) | aws glue streaming, kinesis data streams, s3, Apache Iceberg |
| [glue/streaming-etl/kafka-to-iceberg](./glue/streaming-etl/kafka-to-iceberg/) | ![glue-streaming-ingestion-from-msk-to-iceberg-arch](./glue/streaming-etl/kafka-to-iceberg/glue-streaming-data-from-kafka-to-iceberg-table.svg) | aws glue streaming, Managed Service for Apache Kafka (MSK), s3, Apache Iceberg |
| [glue/streaming-etl/msk-serverless-to-iceberg](./glue/streaming-etl/msk-serverless-to-iceberg/) | ![glue-streaming-ingestion-from-msk-serverless-to-iceberg-arch](./glue/streaming-etl/msk-serverless-to-iceberg/glue-streaming-data-from-msk-serverless-to-iceberg-table.svg) | aws glue streaming, MSK Serverless, s3, Apache Iceberg |
| [kendra/webcrawler-datasource](./kendra/webcrawler-datasource/) | ![firehose_data_transform](./kendra/webcrawler-datasource/amazon_kendra_arch.svg) | kendra, lambda |
| [keyspaces-cassandra](./keyspaces-cassandra/) | ![amazon_keyspaces-arch](./keyspaces-cassandra/amazon_keyspaces-arch.svg)| amazon keyspaces, cassandra |
| [kinesis-data-firehose/data-transform](./kinesis-data-firehose/data-transform/) | ![firehose_data_transform](./kinesis-data-firehose/data-transform/firehose_data_transform.svg) | kinesis firehose, lambda, s3, schema-validation |
| [kinesis-data-firehose/dynamic-partitioning/inline](./kinesis-data-firehose/dynamic-partitioning/inline/) | ![firehose_dynamic_partition_with_inline](./kinesis-data-firehose/dynamic-partitioning/inline/firehose_dynamic_partition_with_inline.svg) | kinesis firehose, s3, dynamic-partitioning, jq |
| [kinesis-data-firehose/dynamic-partitioning/lambda](./kinesis-data-firehose/dynamic-partitioning/lambda/) | ![firehose_dynamic_partition_with_lambda](./kinesis-data-firehose/dynamic-partitioning/lambda/firehose_dynamic_partition_with_lambda.svg) | kinesis firehose, s3, dynamic-partitioning, lambda |
| [kinesis-data-firehose/ekk-stack](./kinesis-data-firehose/ekk-stack/) | ![amazon-ekk-stack-arch](./kinesis-data-firehose/ekk-stack/amazon-ekk-stack-arch.svg) | kinesis firehose, s3, Elasticsearch, bastion host |
| [kinesis-data-firehose/opskk-stack](./kinesis-data-firehose/opskk-stack/) | ![amazon-opskk-stack-arch](./kinesis-data-firehose/opskk-stack/amazon-opskk-stack-arch.svg) | kinesis firehose, s3, OpenSearch, bastion host |
| [kinesis-data-firehose/msk-firehose-s3-stack](./kinesis-data-firehose/msk-firehose-s3-stack/) | ![msk-firehose-s3-arch](./kinesis-data-firehose/msk-firehose-s3-stack/msk-firehose-s3-arch.svg) | msk, kinesis firehose, s3, bastion host |
| [kinesis-data-firehose/msk-serverless-firehose-s3-stack](./kinesis-data-firehose/msk-serverless-firehose-s3-stack/) | ![msk-serverless-firehose-s3-arch](./kinesis-data-firehose/msk-serverless-firehose-s3-stack/msk-serverless-firehose-s3-arch.svg) | msk serverless, kinesis firehose, s3, bastion host |
| [kinesis-data-streams/to-kinesis-data-firehose](./kinesis-data-streams/to-kinesis-data-firehose/) | ![amazon-ekk-stack-arch](./kinesis-data-streams/to-kinesis-data-firehose/kinesis_streams_to_firehose_to_s3.svg) | kinesis data streams, kinesis firehose, s3 |
| [kinesis-data-analytics-for-flink/msk-replication](./kinesis-data-analytics/kda-flink/msk-replication/) | ![kda-flink-msk-replication](./kinesis-data-analytics/kda-flink/msk-replication/kda-flink-msk-replication.svg) | kinesis data analytics for flink, msk |
| [lakeformation](./lakeformation/) | Granting AWS Lake Formation permissions on Data Catalog Resources | glue data catalog, lakeformation |
| [lambda/alb-lambda](./lambda/alb-lambda/) | ![aws-alb-lambda](./lambda/alb-lambda/aws-alb-lambda-arch.svg) | lambda, application load balancer |
| [lambda/alb-path-routing-lambda](./lambda/alb-path-routing-lambda/) | ![alb-path-routing-lambda](./lambda/alb-path-routing-lambda/aws-alb-path-routing-lambda-arch.svg) | lambda, application load balancer |
| [lambda/async-invoke](./lambda/async-invoke/) | ![aws-lambda-async-invocation](./lambda/async-invoke/aws-lambda-async-invocation.svg) | lambda, sns, event-bridge |
| [lambda/lambda-custom-container](./lambda/lambda-custom-container/) | ![aws-lambda-custom-container](./lambda/lambda-custom-container/aws-lambda-custom-container.svg) | lambda, ecr, custom container |
| [memorydb-for-redis](./memorydb/redis-cluster) | ![memorydb-for-redis](./memorydb/redis-cluster/amazon-memorydb.svg) | memorydb |
| [memorydb-for-redis for vector search](./memorydb/vector-search) | ![memorydb-for-redis-for-vectorsearch](./memorydb/vector-search/amazon-memorydb.svg) | memorydb for vector search |
| [msk](./msk/) | ![msk-arch](./msk/msk-arch.svg) | msk(kafka) |
| [msk_aplha](./msk_alpha/) | ![msk-arch](./msk_alpha/msk-arch.svg) | msk(kafka) |
| [msk-serverless](./msk-serverless/) | ![msk-serverless-arch](./msk-serverless/msk-serverless-arch.svg) | msk serverless(kafka) |
| [mwaa(airflow)](./mwaa/) | ![mwaa-arch](./mwaa/mwaa-arch.svg) | mwaa(airflow) |
| [neptune](./neptune/) | ![neptune-arch](./neptune/neptune-arch.svg) | sagemaker, neptune |
| [rds/aurora_mysql](./rds/aurora_mysql/) | ![aurora_mysql](./rds/aurora_mysql/aurora_mysql-arch.svg) | aurora mysql, secrets manager |
| [rds/aurora_postgresql](./rds/aurora_postgresql/) | ![aurora_postgresql](./rds/aurora_postgresql/aurora_postgresql-arch.svg) | aurora postgresql, secrets manager |
| [rds/mariadb](./rds/mariadb/) | ![mariadb-arch](./rds/mariadb/mariadb-arch.svg) | mariadb, secrets manager |
| [rds/rds_proxy-aurora_mysql](./rds/rds_proxy-aurora_mysql/) | ![rds_proxy-aurora_mysql](./rds/rds_proxy-aurora_mysql/rds_proxy-aurora_mysql-arch.svg) | rds-proxy, aurora mysql, secrets manager |
| [rds/nginx-rds_proxy-aurora_mysql](./rds/nginx-rds_proxy-aurora_mysql/) | ![nginx-rds_proxy-aurora_mysql](./rds/nginx-rds_proxy-aurora_mysql/nginx-rds-proxy-aurora_mysql-arch.svg) | NGINX, aurora mysql, secrets manager |
| [rds/sagemaker-aurora_mysql](./rds/sagemaker-aurora_mysql/) | ![sagemaker-aurora_mysql](./rds/sagemaker-aurora_mysql/mysql-sagemaker-arch.svg) | aurora mysql, secrets manager, sagemaker notebook |
| [rds/sagemaker-aurora_postgresql](./rds/sagemaker-aurora_postgresql/) | ![sagemaker-aurora_postgresql](./rds/sagemaker-aurora_postgresql/postgresql-sagemaker-arch.svg) | aurora postgresql, secrets manager, sagemaker notebook |
| [rds/sagemaker-studio-aurora_postgresql](./rds/sagemaker-studio-aurora_postgresql/) | ![sagemaker-studio-aurora_postgresql](./rds/sagemaker-studio-aurora_postgresql/postgresql-sagemaker-in-vpc-arch.svg) | aurora postgresql, secrets manager, sagemaker studio in vpc |
| [aurora_serverless_v1/aurora_mysql-serverless_v1](./rds/aurora_serverless_v1/aurora_mysql-serverless_v1) | ![aurora_mysql_serverless_v1](./rds/aurora_serverless_v1/aurora_mysql-serverless_v1/aurora_mysql-serverless_v1-cluster-arch.svg) | aurora mysql serverless v1 cluster, secrets manager |
| [aurora_serverless_v2/aurora_mysql-serverless_v2-replica](./rds/aurora_serverless_v2/aurora_mysql-serverless_v2-replica) | ![aurora_serverless_v2_replica](./rds/aurora_serverless_v2/aurora_mysql-serverless_v2-replica/aurora_mysql-with-serverless_v2-replica-arch.svg) | aurora mysql serverless v2, aurora mysql, secrets manager |
| [aurora_serverless_v2/aurora_postgresql-serverless_v2](./rds/aurora_serverless_v2/aurora_postgresql-serverless_v2) | ![aurora_postgresql_serverless_v2](./rds/aurora_serverless_v2/aurora_postgresql-serverless_v2/aurora_postgresql-serverless_v2-cluster-arch.svg) | aurora postgresql serverless v2 cluster, secrets manager |
| [redshift/cfn](./redshift/cfn) | ![redshift-cfn-arch](./redshift/cfn/redshift-cfn-arch.svg) | redshift |
| [redshift/alpha](./redshift/redshift_alpha/) | ![redshift-cfn-arch](./redshift/redshift_alpha/redshift-alpha-arch.svg) | redshift |
| [redshift-serverless](./redshift-serverless/) | ![redshift-serverless-arch](./redshift-serverless/redshift-serverless-arch.svg) | redshift-serverless |
| [redshift-streaming-ingestion/from-kinesis](./redshift-streaming-ingestion/from-kinesis/) | ![redshift_streaming_from_kds](./redshift-streaming-ingestion/from-kinesis/redshift_streaming_from_kds.svg) | redshift streaming ingestion from kinesis |
| [redshift-streaming-ingestion/from-msk](./redshift-streaming-ingestion/from-msk/) | ![redshift_streaming_from_msk](./redshift-streaming-ingestion/from-msk/redshift_streaming_from_msk.svg) | redshift streaming ingestion from msk |
| [redshift-streaming-ingestion/from-msk-serverless](./redshift-streaming-ingestion/from-msk-serverless/) | ![redshift_streaming_from_msk_serverless](./redshift-streaming-ingestion/from-msk-serverless/redshift_streaming_from_msk_serverless.svg) | redshift streaming ingestion from msk serverless |
| [sagemaker/notebook](./sagemaker/notebook/) | Launch an Amazon SageMaker Notebook Instance | sagemaker notebook instance |
| [sagemaker/studio](./sagemaker/studio/) | ![studio-vpc-internet](./sagemaker/studio/studio-vpc-internet.png) | sagemaker studio |
| [sagemaker/studio-in-vpc](./sagemaker/studio-in-vpc/) | ![studio-vpc-private](./sagemaker/studio-in-vpc/studio-vpc-private.png) | sagemaker studio in a Private VPC |
| [sagemaker/fsx-lustre](./sagemaker/fsx-lustre/) | Training Jobs with FileSystemInput using Amazon FSx for Lustre | sagemaker studio, FSx for Lustre (FSxLustre) |
| [sagemaker/sagemaker-glue](./sagemaker/sagemaker-glue/) | ![studio-glue-arch](./sagemaker/sagemaker-glue/sagemaker-glue-arch.svg)  | sagemaker studio, aws glue |
| [sagemaker/mlflow-ec2-sagemaker](./sagemaker/mlflow-ec2-sagemaker/) | ![mlflow-sagemaker-arch](./sagemaker/mlflow-ec2-sagemaker/mlflow-sagemaker-arch.svg) | MLflow, sagemaker studio |
| [sagemaker/mlflow-ecs-sagemaker](./sagemaker/mlflow-ecs-sagemaker/) | ![mlflow-ecs-sagemaker-arch](./sagemaker/mlflow-ecs-sagemaker/mlflow-ecs-sagemaker-arch.svg) | MLflow, ecs, fargate, sagemaker studio |
| [sagemaker-async-inference/jumpstart](./sagemaker/model-inference-endpoints/sagemaker-async-inference/jumpstart) | Asynchronous Inference using SageMaker JumpStart | sagemaker async endpoint, jumpstart |
| [sagemaker-async-inference/hugging-face](./sagemaker/model-inference-endpoints/sagemaker-async-inference/hugging-face) | Asynchronous Inference using Hugging Face DLC | sagemaker async endpoint, hugging face |
| [sagemaker-async-inference/pytorch](./sagemaker/model-inference-endpoints/sagemaker-async-inference/pytorch) | Asynchronous Inference using PyTorch DLC | sagemaker async endpoint, pytorch |
| [sagemaker-realtime-inference/jumpstart](./sagemaker/model-inference-endpoints/sagemaker-realtime-inference/jumpstart) | Real-time Inference using SageMaker JumpStart | sagemaker real-time endpoint, jumpstart |
| [sagemaker-realtime-inference/hugging-face](./sagemaker/model-inference-endpoints/sagemaker-realtime-inference/hugging-face) | Real-time Inference using Hugging Face DLC | sagemaker real-time endpoint, hugging face |
| [sagemaker-realtime-inference/pytorch](./sagemaker/model-inference-endpoints/sagemaker-realtime-inference/pytorch) | Real-time Inference using PyTorch DLC | sagemaker real-time endpoint, pytorch |
| [sagemaker-inference-component](./sagemaker/inference-component) | ![](./sagemaker/inference-component/sagemaker-inference-component.gif) | sagemaker real-time endpoint, inference component, multiple FMs on the same instance |

Enjoy!


## Useful commands

 * `npm install -g aws-cdk`          Install the AWS CDK Toolkit (the `cdk` command).
 * `npm install -g aws-cdk@latest`   Install the latest AWS CDK Toolkit (the `cdk`command).
 * `cdk init app --language python`  Create a new, empty CDK Python project.
 * `cdk bootstrap --profile <AWS Profile>` Deploys the CDK Toolkit staging stack; see [Bootstrapping](https://docs.aws.amazon.com/cdk/v2/guide/bootstrapping.html)


## How to fetch specific source directories

This repository is huge, containing a vast number of files, making it a `monorepo`.
Consequently, if you wish to fetch specific source directories instead of downloading the entire repository,
we recommend using the `git sparse-checkout` command.

For example, let's say you want to clone the `cognito-api-lambda` project in `api-gateway` directory.

In that case, open your terminal and run the following command.

   ```
   git clone https://github.com/ksmin23/my-aws-cdk-examples.git
   cd my-aws-cdk-examples
   git sparse-checkout init --cone
   git sparse-checkout set api-gateway/cognito-api-lambda
   ```

:information_source: For more information about `git sparse-checkout`, see [this article](https://github.blog/2020-01-17-bring-your-monorepo-down-to-size-with-sparse-checkout/).


## References

 * [Working with the AWS CDK](https://docs.aws.amazon.com/cdk/latest/guide/work-with.html)
 * [Your first AWS CDK app](https://docs.aws.amazon.com/cdk/latest/guide/hello_world.html)
 * [AWS CDK v2 Reference Documentation](https://docs.aws.amazon.com/cdk/api/v2/)
 * [AWS CDK Toolkit (cdk command)](https://docs.aws.amazon.com/cdk/v2/guide/cli.html)
 * [AWS CDK Workshop](https://cdkworkshop.com/)
 * [Construct Hub: Open-source CDK libraries](https://constructs.dev/)
 * [aws-samples/aws-cdk-examples](https://github.com/aws-samples/aws-cdk-examples)
 * [CDK Resources](https://cdk.dev/resources) - A collection of tools to help during the development of CDK applications.
 * [Awesome CDK](https://github.com/kalaiser/awesome-cdk) - Curated list of awesome AWS Cloud Development Kit (AWS CDK) open-source projects, guides, blogs and other resources.
 * [AWS CloudFormation quotas](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cloudformation-limits.html) - Check out **AWS CloudFormation quotas** when you encounter limitation errors when authoring templates and creating stacks.

