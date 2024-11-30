#!/bin/bash

APPLICATION_NAME="movie-recommender"
VERSIONS=(
  "app-f860-241128_005605900906"
  "app-f860-241128_005340618484"
  "app-06a5-241128_004042071466"
  "app-06a5-241128_003005058698"
  "app-06a5-241128_002628283850"
)

for VERSION in "${VERSIONS[@]}"; do
    echo "Deleting version $VERSION..."
    aws elasticbeanstalk delete-application-version \
      --application-name "$APPLICATION_NAME" \
      --version-label "$VERSION" \
      --delete-source-bundle
done
echo "Deletion completed!"
