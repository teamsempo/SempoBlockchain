provider "aws" {
  region = "us-east-1"
}

resource "aws_elb" "staging_lb" {
  availability_zones = [
    "us-east-1a",
    "us-east-1b",
    "us-east-1c",
  ]

  listener {
    instance_port      = 80
    instance_protocol  = "http"
    lb_port            = 80
    lb_protocol        = "http"
    ssl_certificate_id = ""
  }

  connection_draining         = true
  connection_draining_timeout = 20
}

resource "aws_ecr_repository" "SempoRepository" {
  name                 = "ecrrepo"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_elastic_beanstalk_application" "SempoBlockchain" {
  name = "SempoBlockchain"
}


resource "aws_elastic_beanstalk_environment" "staging_env" {
  name                = "Sempoblockchain-env2"
  application         = "SempoBlockchain"
  solution_stack_name = "64bit Amazon Linux 2018.03 v2.20.4 running Multi-container Docker 19.03.6-ce (Generic)"
  wait_for_ready_timeout = "30m"
  cname_prefix           = "sempo-staging2"
  depends_on = [aws_elastic_beanstalk_application.SempoBlockchain]

  setting {
      namespace = "aws:autoscaling:launchconfiguration"
      name = "IamInstanceProfile"
      value = "aws-elasticbeanstalk-ec2-role"
  }
  setting {
    namespace = "aws:autoscaling:launchconfiguration"
    name = "InstanceType"
    value = "t2.micro"
  }
}