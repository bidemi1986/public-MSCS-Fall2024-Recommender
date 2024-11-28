#!/bin/bash

# Initialize Elastic Beanstalk
eb init movie-recommender --platform python-3.8 --region us-east-1

# Create environment if it doesn't exist
if ! eb status movie-recommender-prod &>/dev/null; then
    eb create movie-recommender-prod \
        --elb-type application \
        --service-role aws-elasticbeanstalk-service-role \
        --instance-profile aws-elasticbeanstalk-ec2-role

    # Wait for environment to be ready
    echo "Waiting for environment to be ready..."
    sleep 60

    # Configure auto scaling trigger
    aws elasticbeanstalk update-environment \
        --environment-name movie-recommender-prod \
        --option-settings '[
            {
                "Namespace": "aws:autoscaling:trigger",
                "OptionName": "MeasureName",
                "Value": "CPUUtilization"
            },
            {
                "Namespace": "aws:autoscaling:trigger",
                "OptionName": "Statistic",
                "Value": "Average"
            },
            {
                "Namespace": "aws:autoscaling:trigger",
                "OptionName": "Unit",
                "Value": "Percent"
            },
            {
                "Namespace": "aws:autoscaling:trigger",
                "OptionName": "Period",
                "Value": "5"
            },
            {
                "Namespace": "aws:autoscaling:trigger",
                "OptionName": "BreachDuration",
                "Value": "5"
            },
            {
                "Namespace": "aws:autoscaling:trigger",
                "OptionName": "UpperThreshold",
                "Value": "70"
            },
            {
                "Namespace": "aws:autoscaling:trigger",
                "OptionName": "LowerThreshold",
                "Value": "30"
            }
        ]'
fi

# Deploy application
eb deploy movie-recommender-prod

# Create CloudWatch dashboard
aws cloudwatch put-dashboard \
    --dashboard-name "MovieRecommender" \
    --dashboard-body "$(cat dashboard.json)"