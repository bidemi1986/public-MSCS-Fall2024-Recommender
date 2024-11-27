# Create an S3 bucket (replace `movie-recommender-models` with your unique bucket name)
aws s3 mb s3://movie-recommender-models

# Upload your model files to the S3 bucket
aws s3 cp artifacts/movie_list.pkl s3://movie-recommender-models/
aws s3 cp artifacts/similarity.pkl s3://movie-recommender-models/



# Install AWS CLI
pip install awscli

# Configure AWS CLI
aws configure
# Provide your Access Key ID, Secret Access Key, Region, and output format.


pip install boto3
