docker build -t my-lambda:latest .
docker run --rm -p 9000:8080 my-lambda:latest


create ECR 

aws ecr get-login-password --region us-east-1 \
  | docker login --username AWS --password-stdin 011528265658.dkr.ecr.us-east-1.amazonaws.com


REGION=us-east-1
ACCOUNT_ID=011528265658
REPO_NAME=utd-career-guiding-agent
TAG=langgraph-v1

ECR_URI="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO_NAME:$TAG"

# Build single-arch amd64, disable provenance/SBOM (prevents OCI index/attestations)
docker buildx build \
  --platform linux/amd64 \
  --provenance=false \
  --sbom=false \
  -t "$ECR_URI" \
  --push \
  .




# Bulding the Agent langgraph docker for lambda function 

docker build -t utd-langgraph-chat .

docker tag utd-langgraph-chat:latest <acct>.dkr.ecr.<region>.amazonaws.com/utd-langgraph-chat:latest

{
  "question": "I am a UTD student interested in AI engineering. Recommend relevant courses and 3 project ideas based on current job demand in Dallas."
}
