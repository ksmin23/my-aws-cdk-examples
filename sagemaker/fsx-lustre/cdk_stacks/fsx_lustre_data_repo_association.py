import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_fsx,
)
from constructs import Construct

class FSxLustreDataRepoAssociationStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, file_system_id, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    data_repository_path = self.node.try_get_context("data_repository_path")
    assert data_repository_path.startswith('s3://')

    file_system_path = self.node.try_get_context("file_system_path") or "/ns1"
    assert file_system_path.startswith('/')

    cfn_data_repository_association = aws_fsx.CfnDataRepositoryAssociation(self, "FSxLustreCfnDataRepositoryAssociation",
      data_repository_path=data_repository_path,
      file_system_id=file_system_id,
      file_system_path=file_system_path,
      batch_import_meta_data_on_create=True,
      imported_file_chunk_size=1024,
      s3=aws_fsx.CfnDataRepositoryAssociation.S3Property(
        auto_export_policy=aws_fsx.CfnDataRepositoryAssociation.AutoExportPolicyProperty(
          events=[
            "NEW",
            "CHANGED",
            "DELETED"
          ]
        ),
        auto_import_policy=aws_fsx.CfnDataRepositoryAssociation.AutoImportPolicyProperty(
          events=[
            "NEW",
            "CHANGED",
            "DELETED"
          ]
        )
      )
    )

    cfn_data_repository_association.apply_removal_policy(cdk.RemovalPolicy.DESTROY)

    cdk.CfnOutput(self, f'{self.stack_name}-FileSystemId',
      value=cfn_data_repository_association.file_system_id)
    cdk.CfnOutput(self, f'{self.stack_name}-FileSystemPath',
      value=cfn_data_repository_association.file_system_path)
    cdk.CfnOutput(self, f'{self.stack_name}-DataRepositoryPath',
      value=cfn_data_repository_association.data_repository_path)

