provider "aws" {
  version = "~> 2.0"
  region  = "eu-central-1"
  # Auth credentials are fetched from environment
}

resource "aws_elastic_beanstalk_environment" "staging_env" {
  # (resource arguments)
  name                = "Sempoblockchain-env"
  application         = "SempoBlockchain"
  tier                = "WebServer"
  solution_stack_name = "64bit Amazon Linux 2018.03 v2.20.0 running Multi-container Docker 18.09.9-ce (Generic)"

  setting {
    name      = "AppSource"
    namespace = "aws:cloudformation:template:parameter"
    resource  = ""
    value     = "https://s3-eu-central-1.amazonaws.com/elasticbeanstalk-samples-eu-central-1/ecs-sample.zip"
  }
  setting {
    name      = "Application Healthcheck URL"
    namespace = "aws:elasticbeanstalk:application"
    resource  = ""
    value     = ""
  }
  setting {
    name      = "AssociatePublicIpAddress"
    namespace = "aws:ec2:vpc"
    resource  = ""
    value     = ""
  }
  setting {
    name      = "Automatically Terminate Unhealthy Instances"
    namespace = "aws:elasticbeanstalk:monitoring"
    resource  = ""
    value     = "true"
  }
  setting {
    name      = "Availability Zones"
    namespace = "aws:autoscaling:asg"
    resource  = ""
    value     = "Any"
  }
  setting {
    name      = "BatchSize"
    namespace = "aws:elasticbeanstalk:command"
    resource  = ""
    value     = "100"
  }
  setting {
    name      = "BatchSizeType"
    namespace = "aws:elasticbeanstalk:command"
    resource  = ""
    value     = "Percentage"
  }
  setting {
    name      = "BlockDeviceMappings"
    namespace = "aws:autoscaling:launchconfiguration"
    resource  = ""
    value     = "/dev/xvdcz=:12:true:gp2"
  }
  setting {
    name      = "BreachDuration"
    namespace = "aws:autoscaling:trigger"
    resource  = ""
    value     = "5"
  }
  setting {
    name      = "ConfigDocument"
    namespace = "aws:elasticbeanstalk:healthreporting:system"
    resource  = ""
    value     = "{\"Version\":1,\"CloudWatchMetrics\":{\"Instance\":{\"RootFilesystemUtil\":null,\"CPUIrq\":null,\"LoadAverage5min\":null,\"ApplicationRequests5xx\":null,\"ApplicationRequests4xx\":null,\"CPUUser\":null,\"LoadAverage1min\":null,\"ApplicationLatencyP50\":null,\"CPUIdle\":null,\"InstanceHealth\":null,\"ApplicationLatencyP95\":null,\"ApplicationLatencyP85\":null,\"ApplicationLatencyP90\":null,\"CPUSystem\":null,\"ApplicationLatencyP75\":null,\"CPUSoftirq\":null,\"ApplicationLatencyP10\":null,\"ApplicationLatencyP99\":null,\"ApplicationRequestsTotal\":null,\"ApplicationLatencyP99.9\":null,\"ApplicationRequests3xx\":null,\"ApplicationRequests2xx\":null,\"CPUIowait\":null,\"CPUNice\":null},\"Environment\":{\"InstancesSevere\":null,\"InstancesDegraded\":null,\"ApplicationRequests5xx\":null,\"ApplicationRequests4xx\":null,\"ApplicationLatencyP50\":null,\"ApplicationLatencyP95\":null,\"ApplicationLatencyP85\":null,\"InstancesUnknown\":null,\"ApplicationLatencyP90\":null,\"InstancesInfo\":null,\"InstancesPending\":null,\"ApplicationLatencyP75\":null,\"ApplicationLatencyP10\":null,\"ApplicationLatencyP99\":null,\"ApplicationRequestsTotal\":null,\"InstancesNoData\":null,\"ApplicationLatencyP99.9\":null,\"ApplicationRequests3xx\":null,\"ApplicationRequests2xx\":null,\"InstancesOk\":null,\"InstancesWarning\":null}},\"Rules\":{\"Environment\":{\"ELB\":{\"ELBRequests4xx\":{\"Enabled\":true}},\"Application\":{\"ApplicationRequests4xx\":{\"Enabled\":true}}}}}"
  }
  setting {
    name      = "ConnectionDrainingEnabled"
    namespace = "aws:elb:policies"
    resource  = ""
    value     = "true"
  }
  setting {
    name      = "ConnectionDrainingTimeout"
    namespace = "aws:elb:policies"
    resource  = ""
    value     = "20"
  }
  setting {
    name      = "ConnectionSettingIdleTimeout"
    namespace = "aws:elb:policies"
    resource  = ""
    value     = "60"
  }
  setting {
    name      = "Cooldown"
    namespace = "aws:autoscaling:asg"
    resource  = ""
    value     = "360"
  }
  setting {
    name      = "CrossZone"
    namespace = "aws:elb:loadbalancer"
    resource  = ""
    value     = "true"
  }
  setting {
    name      = "Custom Availability Zones"
    namespace = "aws:autoscaling:asg"
    resource  = ""
    value     = ""
  }
  setting {
    name      = "DEPLOYMENT_NAME"
    namespace = "aws:elasticbeanstalk:application:environment"
    resource  = ""
    value     = "staging"
  }
  setting {
    name      = "DefaultSSHPort"
    namespace = "aws:elasticbeanstalk:control"
    resource  = ""
    value     = "22"
  }
  setting {
    name      = "DeleteOnTerminate"
    namespace = "aws:elasticbeanstalk:cloudwatch:logs"
    resource  = ""
    value     = "false"
  }
  setting {
    name      = "DeleteOnTerminate"
    namespace = "aws:elasticbeanstalk:cloudwatch:logs:health"
    resource  = ""
    value     = "false"
  }
  setting {
    name      = "DeploymentPolicy"
    namespace = "aws:elasticbeanstalk:command"
    resource  = ""
    value     = "AllAtOnce"
  }
  setting {
    name      = "EC2KeyName"
    namespace = "aws:autoscaling:launchconfiguration"
    resource  = ""
    value     = "blockchain-deploy"
  }
  setting {
    name      = "ELBScheme"
    namespace = "aws:ec2:vpc"
    resource  = ""
    value     = "public"
  }
  setting {
    name      = "ELBSubnets"
    namespace = "aws:ec2:vpc"
    resource  = ""
    value     = ""
  }
  setting {
    name      = "EnableSpot"
    namespace = "aws:ec2:instances"
    resource  = ""
    value     = "false"
  }
  setting {
    name      = "EnvironmentType"
    namespace = "aws:elasticbeanstalk:environment"
    resource  = ""
    value     = "LoadBalanced"
  }
  setting {
    name      = "EnvironmentVariables"
    namespace = "aws:cloudformation:template:parameter"
    resource  = ""
    value     = "SECRETS_BUCKET=sarafu-secretsDEPLOYMENT_NAME=staging"
  }
  setting {
    name      = "EvaluationPeriods"
    namespace = "aws:autoscaling:trigger"
    resource  = ""
    value     = "1"
  }
  setting {
    name      = "ExternalExtensionsS3Bucket"
    namespace = "aws:elasticbeanstalk:environment"
    resource  = ""
    value     = ""
  }
  setting {
    name      = "ExternalExtensionsS3Key"
    namespace = "aws:elasticbeanstalk:environment"
    resource  = ""
    value     = ""
  }
  setting {
    name      = "HealthCheckSuccessThreshold"
    namespace = "aws:elasticbeanstalk:healthreporting:system"
    resource  = ""
    value     = "Ok"
  }
  setting {
    name      = "HealthStreamingEnabled"
    namespace = "aws:elasticbeanstalk:cloudwatch:logs:health"
    resource  = ""
    value     = "false"
  }
  setting {
    name      = "HealthyThreshold"
    namespace = "aws:elb:healthcheck"
    resource  = ""
    value     = "3"
  }
  setting {
    name      = "HooksPkgUrl"
    namespace = "aws:cloudformation:template:parameter"
    resource  = ""
    value     = "https://s3.dualstack.eu-central-1.amazonaws.com/elasticbeanstalk-env-resources-eu-central-1/stalks/eb_docker_ecs_4.2.1.201590.0_1585088844/lib/hooks.tar.gz"
  }
  setting {
    name      = "IamInstanceProfile"
    namespace = "aws:autoscaling:launchconfiguration"
    resource  = ""
    value     = "aws-elasticbeanstalk-ec2-role"
  }
  setting {
    name      = "IgnoreHealthCheck"
    namespace = "aws:elasticbeanstalk:command"
    resource  = ""
    value     = "false"
  }
  setting {
    name      = "ImageId"
    namespace = "aws:autoscaling:launchconfiguration"
    resource  = ""
    value     = "ami-053d2b67def7d823f"
  }
  setting {
    name      = "InstancePort"
    namespace = "aws:cloudformation:template:parameter"
    resource  = ""
    value     = "80"
  }
  setting {
    name      = "InstancePort"
    namespace = "aws:elb:listener:80"
    resource  = ""
    value     = "80"
  }
  setting {
    name      = "InstanceProtocol"
    namespace = "aws:elb:listener:80"
    resource  = ""
    value     = "HTTP"
  }
  setting {
    name      = "InstanceRefreshEnabled"
    namespace = "aws:elasticbeanstalk:managedactions:platformupdate"
    resource  = ""
    value     = "false"
  }
  setting {
    name      = "InstanceType"
    namespace = "aws:autoscaling:launchconfiguration"
    resource  = ""
    value     = "t2.medium"
  }
  setting {
    name      = "InstanceTypeFamily"
    namespace = "aws:cloudformation:template:parameter"
    resource  = ""
    value     = "t2"
  }
  setting {
    name      = "InstanceTypes"
    namespace = "aws:ec2:instances"
    resource  = ""
    value     = "t2.medium"
  }
  setting {
    name      = "Interval"
    namespace = "aws:elb:healthcheck"
    resource  = ""
    value     = "10"
  }
  setting {
    name      = "LaunchTimeout"
    namespace = "aws:elasticbeanstalk:control"
    resource  = ""
    value     = "0"
  }
  setting {
    name      = "LaunchType"
    namespace = "aws:elasticbeanstalk:control"
    resource  = ""
    value     = "Migration"
  }
  setting {
    name      = "ListenerEnabled"
    namespace = "aws:elb:listener:80"
    resource  = ""
    value     = "true"
  }
  setting {
    name      = "ListenerProtocol"
    namespace = "aws:elb:listener:80"
    resource  = ""
    value     = "HTTP"
  }
  setting {
    name      = "LoadBalancerHTTPPort"
    namespace = "aws:elb:loadbalancer"
    resource  = ""
    value     = "80"
  }
  setting {
    name      = "LoadBalancerHTTPSPort"
    namespace = "aws:elb:loadbalancer"
    resource  = ""
    value     = "OFF"
  }
  setting {
    name      = "LoadBalancerPortProtocol"
    namespace = "aws:elb:loadbalancer"
    resource  = ""
    value     = "HTTP"
  }
  setting {
    name      = "LoadBalancerSSLPortProtocol"
    namespace = "aws:elb:loadbalancer"
    resource  = ""
    value     = "HTTPS"
  }
  setting {
    name      = "LoadBalancerType"
    namespace = "aws:elasticbeanstalk:environment"
    resource  = ""
    value     = "classic"
  }
  setting {
    name      = "LogPublicationControl"
    namespace = "aws:elasticbeanstalk:hostmanager"
    resource  = ""
    value     = "false"
  }
  setting {
    name      = "LowerBreachScaleIncrement"
    namespace = "aws:autoscaling:trigger"
    resource  = ""
    value     = "-1"
  }
  setting {
    name      = "LowerThreshold"
    namespace = "aws:autoscaling:trigger"
    resource  = ""
    value     = "2000000"
  }
  setting {
    name      = "ManagedActionsEnabled"
    namespace = "aws:elasticbeanstalk:managedactions"
    resource  = ""
    value     = "false"
  }
  setting {
    name      = "MaxBatchSize"
    namespace = "aws:autoscaling:updatepolicy:rollingupdate"
    resource  = ""
    value     = "1"
  }
  setting {
    name      = "MaxSize"
    namespace = "aws:autoscaling:asg"
    resource  = ""
    value     = "4"
  }
  setting {
    name      = "MeasureName"
    namespace = "aws:autoscaling:trigger"
    resource  = ""
    value     = "NetworkOut"
  }
  setting {
    name      = "MinInstancesInService"
    namespace = "aws:autoscaling:updatepolicy:rollingupdate"
    resource  = ""
    value     = "1"
  }
  setting {
    name      = "MinSize"
    namespace = "aws:autoscaling:asg"
    resource  = ""
    value     = "1"
  }
  setting {
    name      = "MonitoringInterval"
    namespace = "aws:autoscaling:launchconfiguration"
    resource  = ""
    value     = "5 minute"
  }
  setting {
    name      = "Notification Endpoint"
    namespace = "aws:elasticbeanstalk:sns:topics"
    resource  = ""
    value     = ""
  }
  setting {
    name      = "Notification Protocol"
    namespace = "aws:elasticbeanstalk:sns:topics"
    resource  = ""
    value     = "email"
  }
  setting {
    name      = "Notification Topic ARN"
    namespace = "aws:elasticbeanstalk:sns:topics"
    resource  = ""
    value     = ""
  }
  setting {
    name      = "Notification Topic Name"
    namespace = "aws:elasticbeanstalk:sns:topics"
    resource  = ""
    value     = ""
  }
  setting {
    name      = "PauseTime"
    namespace = "aws:autoscaling:updatepolicy:rollingupdate"
    resource  = ""
    value     = ""
  }
  setting {
    name      = "Period"
    namespace = "aws:autoscaling:trigger"
    resource  = ""
    value     = "5"
  }
  setting {
    name      = "PreferredStartTime"
    namespace = "aws:elasticbeanstalk:managedactions"
    resource  = ""
    value     = ""
  }
  setting {
    name      = "RetentionInDays"
    namespace = "aws:elasticbeanstalk:cloudwatch:logs"
    resource  = ""
    value     = "7"
  }
  setting {
    name      = "RetentionInDays"
    namespace = "aws:elasticbeanstalk:cloudwatch:logs:health"
    resource  = ""
    value     = "7"
  }
  setting {
    name      = "RollbackLaunchOnFailure"
    namespace = "aws:elasticbeanstalk:control"
    resource  = ""
    value     = "false"
  }
  setting {
    name      = "RollingUpdateEnabled"
    namespace = "aws:autoscaling:updatepolicy:rollingupdate"
    resource  = ""
    value     = "true"
  }
  setting {
    name      = "RollingUpdateType"
    namespace = "aws:autoscaling:updatepolicy:rollingupdate"
    resource  = ""
    value     = "Health"
  }
  # setting {
  #   name      = "RootVolumeIOPS"
  #   namespace = "aws:autoscaling:launchconfiguration"
  #   resource  = ""
  #   value     = ""
  # }
  # setting {
  #   name      = "RootVolumeSize"
  #   namespace = "aws:autoscaling:launchconfiguration"
  #   resource  = ""
  #   value     = ""
  # }
  # setting {
  #   name      = "RootVolumeType"
  #   namespace = "aws:autoscaling:launchconfiguration"
  #   resource  = ""
  #   value     = ""
  # }
  setting {
    name      = "SECRETS_BUCKET"
    namespace = "aws:elasticbeanstalk:application:environment"
    resource  = ""
    value     = "sarafu-secrets"
  }
  setting {
    name      = "SSHSourceRestriction"
    namespace = "aws:autoscaling:launchconfiguration"
    resource  = ""
    value     = "tcp,22,22,0.0.0.0/0"
  }
  setting {
    name      = "SSLCertificateId"
    namespace = "aws:elb:listener:80"
    resource  = ""
    value     = ""
  }
  setting {
    name      = "SSLCertificateId"
    namespace = "aws:elb:loadbalancer"
    resource  = ""
    value     = ""
  }
  setting {
    name      = "SecurityGroups"
    namespace = "aws:autoscaling:launchconfiguration"
    resource  = ""
    value     = ""
  }
  setting {
    name      = "SecurityGroups"
    namespace = "aws:elb:loadbalancer"
    resource  = ""
    value     = ""
  }
  setting {
    name      = "ServiceRole"
    namespace = "aws:elasticbeanstalk:environment"
    resource  = ""
    value     = "arn:aws:iam::847108109661:role/aws-elasticbeanstalk-service-role"
  }
  setting {
    name      = "SpotFleetOnDemandAboveBasePercentage"
    namespace = "aws:ec2:instances"
    resource  = ""
    value     = "70"
  }
  setting {
    name      = "SpotFleetOnDemandBase"
    namespace = "aws:ec2:instances"
    resource  = ""
    value     = "0"
  }
  setting {
    name      = "SpotMaxPrice"
    namespace = "aws:ec2:instances"
    resource  = ""
    value     = ""
  }
  setting {
    name      = "Statistic"
    namespace = "aws:autoscaling:trigger"
    resource  = ""
    value     = "Average"
  }
  setting {
    name      = "StreamLogs"
    namespace = "aws:elasticbeanstalk:cloudwatch:logs"
    resource  = ""
    value     = "false"
  }
  setting {
    name      = "Subnets"
    namespace = "aws:ec2:vpc"
    resource  = ""
    value     = ""
  }
  setting {
    name      = "SystemType"
    namespace = "aws:elasticbeanstalk:healthreporting:system"
    resource  = ""
    value     = "basic"
  }
  setting {
    name      = "Target"
    namespace = "aws:elb:healthcheck"
    resource  = ""
    value     = "TCP:80"
  }
  setting {
    name      = "Timeout"
    namespace = "aws:autoscaling:updatepolicy:rollingupdate"
    resource  = ""
    value     = "PT30M"
  }
  setting {
    name      = "Timeout"
    namespace = "aws:elasticbeanstalk:command"
    resource  = ""
    value     = "600"
  }
  setting {
    name      = "Timeout"
    namespace = "aws:elb:healthcheck"
    resource  = ""
    value     = "5"
  }
  setting {
    name      = "UnhealthyThreshold"
    namespace = "aws:elb:healthcheck"
    resource  = ""
    value     = "5"
  }
  setting {
    name      = "Unit"
    namespace = "aws:autoscaling:trigger"
    resource  = ""
    value     = "Bytes"
  }
  setting {
    name      = "UpdateLevel"
    namespace = "aws:elasticbeanstalk:managedactions:platformupdate"
    resource  = ""
    value     = ""
  }
  setting {
    name      = "UpperBreachScaleIncrement"
    namespace = "aws:autoscaling:trigger"
    resource  = ""
    value     = "1"
  }
  setting {
    name      = "UpperThreshold"
    namespace = "aws:autoscaling:trigger"
    resource  = ""
    value     = "6000000"
  }
  setting {
    name      = "VPCId"
    namespace = "aws:ec2:vpc"
    resource  = ""
    value     = ""
  }
}


