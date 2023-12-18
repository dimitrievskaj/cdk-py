from aws_cdk import Stack, Tags
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_elasticloadbalancingv2 as elbv2
from aws_cdk import aws_ecr as ecr
from aws_cdk import aws_secretsmanager as secretsmanager
from aws_cdk import aws_ssm as ssm
from constructs import Construct

from py_cdk_stacks.config import CurrentConfig


class ComputeStack(Stack):
    def __init__(
        self,
        scope: Construct,
        id: str,
        vpc: ec2.Vpc,
        app_ecr: ecr.IRepository,
        config,
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)

        def resource_name(name: str):
            return f"{CurrentConfig.PREFIX}-{name}"

        # Assuming these secrets are stored in AWS Secrets Manager GCP Connection
        db_credentials_secret = secretsmanager.Secret.from_secret_name_v2(
            self,
            "DBCredentialsSecret",
            "gcpConnection",
        )

        # Fetch the secret from AWS Secrets Manager for SSO integration
        sso_secret = secretsmanager.Secret.from_secret_name_v2(
            self,
            "SSOSecret",
            "ssoIntegration",
        )

        # Fetch the secret from AWS Secrets Manager for Google Maps Api Key
        google_maps_api_secret = secretsmanager.Secret.from_secret_name_v2(
            self,
            "GoogleMapsAPISecret",
            "gMapsApiKey",
        )
        # Create a security group for Fargate
        fargate_sg = ec2.SecurityGroup(
            self,
            "FargateServiceSG",
            vpc=vpc,
            description="Security group for Fargate Service",
            allow_all_outbound=True,
        )

        # Create inbound rule to enable access to fargate from gcp database
        gcp_db_ip = "192.168.0.14"
        gcp_db_port = 5432
        fargate_sg.add_egress_rule(
            ec2.Peer.ipv4(gcp_db_ip + "/32"),
            ec2.Port.tcp(gcp_db_port),
            "Allow outbound to GCP DB",
        )
        cluster = ecs.Cluster(
            self,
            resource_name("cluster"),
            vpc=vpc,
            cluster_name=resource_name("cluster-api"),
            container_insights=True,
        )

        task_definition = ecs.FargateTaskDefinition(
            self,
            resource_name("TaskDefinition"),
            memory_limit_mib=2048,
            cpu=1024,
        )

        container = task_definition.add_container(
            resource_name("container"),
            image=ecs.ContainerImage.from_ecr_repository(app_ecr),
            port_mappings=[ecs.PortMapping(container_port=80)],
            logging=ecs.LogDrivers.aws_logs(stream_prefix="app-api"),
            environment={
                "ENV": "DEV",
                "AWS_REGION": "us-east-1",
                # Additional environment variables as needed
            },
            secrets={
                "DB_USER": ecs.Secret.from_secrets_manager(
                    db_credentials_secret, "username"
                ),
                "DB_PASSWORD": ecs.Secret.from_secrets_manager(
                    db_credentials_secret, "password"
                ),
                "DB_HOST": ecs.Secret.from_secrets_manager(
                    db_credentials_secret, "host"
                ),
                "DB_PORT": ecs.Secret.from_secrets_manager(
                    db_credentials_secret, "port"
                ),
                "DB_NAME": ecs.Secret.from_secrets_manager(
                    db_credentials_secret, "dbname"
                ),
                "GOOGLE_MAPS_API_KEY": ecs.Secret.from_secrets_manager(
                    google_maps_api_secret, "googlemapsapikey"
                ),
                "SSO_CLIENT_ID": ecs.Secret.from_secrets_manager(
                    sso_secret, "ssoclientid"
                ),
                "SSO_CLIENT_SECRET": ecs.Secret.from_secrets_manager(
                    sso_secret, "ssoclientsecret"
                ),
            },
        )

        load_balancer = elbv2.ApplicationLoadBalancer(
            self, resource_name("loadbalancer"), vpc=vpc, internet_facing=True
        )
        target_group = elbv2.ApplicationTargetGroup(
            self,
            resource_name("TargetGroup"),
            vpc=vpc,
            port=80,
            target_type=elbv2.TargetType.IP,
            health_check=elbv2.HealthCheck(path="/v1/healthcheck"),
        )

        listener = load_balancer.add_listener(
            "Listener", port=80, default_target_groups=[target_group]
        )

        service = ecs.FargateService(
            self,
            resource_name("FargateService"),
            cluster=cluster,
            task_definition=task_definition,
            desired_count=2,
            assign_public_ip=True,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            service_name="app-api",
            security_groups=[fargate_sg],
        )

        listener.add_targets(
            resource_name("ECS-Service"),
            port=80,
            targets=[
                service.load_balancer_target(
                    container_name=resource_name("container"), container_port=80
                )
            ],
        )

        Tags.of(self).add("Project", "Demo")
        Tags.of(self).add("Team", "DevOps")
