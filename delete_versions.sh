#!/bin/bash

APPLICATION_NAME="movie-recommender"
VERSIONS=(
  "app-bd2a-241129_181029505010"
  "app-bd2a-241129_180759828264"
)

for VERSION in "${VERSIONS[@]}"; do
    echo "Deleting version $VERSION..."
    aws elasticbeanstalk delete-application-version \
      --application-name "$APPLICATION_NAME" \
      --version-label "$VERSION" \
      --delete-source-bundle
done
echo "Deletion completed!"
