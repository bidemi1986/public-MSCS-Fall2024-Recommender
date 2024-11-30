#!/bin/bash

APPLICATION_NAME="movie-recommender"

# Get the list of environment names
ENVIRONMENTS=$(aws elasticbeanstalk describe-environments \
  --application-name $APPLICATION_NAME \
  --query "Environments[].EnvironmentName" \
  --output text)

for ENV in $ENVIRONMENTS; do
    echo "Terminating environment $ENV..."
    aws elasticbeanstalk terminate-environment --environment-name $ENV
done

echo "All environments have been terminated."
