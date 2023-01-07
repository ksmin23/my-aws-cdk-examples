import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_fsx,
)
from constructs import Construct

class FSxLustreStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    lustre_maintenance_time = aws_fsx.LustreMaintenanceTime(
      day=aws_fsx.Weekday.SUNDAY,
      hour=19,
      minute=0
    )

    lustre_configuration = {
      "deployment_type": aws_fsx.LustreDeploymentType.PERSISTENT_2,
      "per_unit_storage_throughput": 125,
      "weekly_maintenance_start_time": lustre_maintenance_time
    }

    vpc_subnet = vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS).subnets[0]

    lustre_file_system = aws_fsx.LustreFileSystem(self, "FsxLustreFileSystem",
      lustre_configuration=lustre_configuration,
      storage_capacity_gib=1200,
      vpc=vpc,
      vpc_subnet=vpc_subnet,
      removal_policy=cdk.RemovalPolicy.DESTROY
    )

    self.file_system_id = lustre_file_system.file_system_id

    cdk.CfnOutput(self, f'{self.stack_name}-FileSystemId', value=lustre_file_system.file_system_id)
    cdk.CfnOutput(self, f'{self.stack_name}-MountName', value=lustre_file_system.mount_name)
    cdk.CfnOutput(self, f'{self.stack_name}-LustreSubnetId', value=vpc_subnet.subnet_id)

