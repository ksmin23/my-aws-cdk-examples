# Amazon OpenSearch Ingestion CDK Python project!

This repository contains a set of example projects for [Amazon OpenSearch Ingestion](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/ingestion.html)

| Example | Architecture | Description |
|---------|-------------|------|
| [ingestion to opensearch domain](./opensearch) | ![osis-domain-pipeline](./opensearch/osis-domain-pipeline.svg) | data ingestion to an opensearch domain using OpenSearch Ingestion Pipelines |
| [opensearch-serverless colleciton](./opensearch-serverless) | ![osis-collection-pipeline](./opensearch-serverless/osis-collection-pipeline.svg) | data ingestion to an opensearch serverless collection using OpenSearch Ingestion Pipelines |

Enjoy!

## References

 * [Amazon OpenSearch Ingestion Developer Guide](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/ingestion.html)
   * [Tutorial: Ingesting data into a domain using Amazon OpenSearch Ingestion](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/osis-get-started.html)
   * [Tutorial: Ingesting data into a collection using Amazon OpenSearch Ingestion](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/osis-serverless-get-started.html)
 * [Data Prepper](https://opensearch.org/docs/latest/data-prepper/index/) - a server-side data collector capable of filtering, enriching, transforming, normalizing, and aggregating data for downstream analytics and visualization.