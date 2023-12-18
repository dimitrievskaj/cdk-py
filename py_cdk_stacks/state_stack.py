from aws_cdk import Stack, RemovalPolicy, Tags
from constructs import Construct
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecr as ecr

from py_cdk_stacks.config import CurrentConfig


class StateStack(Stack):
    def __init__(self, scope: Construct, id: str, config, **kwargs):
        super().__init__(scope, id, **kwargs)

        def resource_name(name: str) -> str:
            return f"{CurrentConfig.PREFIX}-{name}"

        self.vpc = ec2.Vpc(
            self,
            resource_name("vpc"),
            vpc_name=resource_name("vpc"),
            max_azs=2,
            cidr="10.0.0.0/16",
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public", subnet_type=ec2.SubnetType.PUBLIC, cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="Isolated",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24,
                ),
            ],
        )

        self.app_ecr = ecr.Repository(
            self,
            "AppRepo",
            repository_name=resource_name("app-api"),
            removal_policy=RemovalPolicy.RETAIN,
        )

        Tags.of(self).add("Project", "Demo")
        Tags.of(self).add("Team", "DevOps")
