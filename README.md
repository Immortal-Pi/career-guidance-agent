docker build -t my-lambda:latest .
docker run --rm -p 9000:8080 my-lambda:latest


create ECR 

REGION=us-east-1
ACCOUNT_ID=011528265658
REPO_NAME=utd-career-guiding-agent
TAG=lambda-v1

ECR_URI="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO_NAME:$TAG"

# Build single-arch amd64, disable provenance/SBOM (prevents OCI index/attestations)
docker buildx build \
  --platform linux/amd64 \
  --provenance=false \
  --sbom=false \
  -t "$ECR_URI" \
  --push \
  .
