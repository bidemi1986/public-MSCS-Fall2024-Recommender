#!/bin/bash

# Initialize Elastic Beanstalk
eb init movie-recommender --platform python-3.8 --region us-east-1

# Create environment if it doesn't exist
if ! eb status movie-recommender-prod &>/dev/null; then
    eb create movie-recommender-prod \
        --elb-type application

    # Wait for environment to be ready
    echo "Waiting for environment to be ready..."
    sleep 60
fi

# Deploy application
eb deploy movie-recommender-prod

# Create CloudWatch dashboard
aws cloudwatch put-dashboard \
    --dashboard-name "MovieRecommender" \
    --dashboard-body "$(cat dashboard.json)"