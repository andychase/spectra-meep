#!bash
docker buildx build \
  --platform arm64 \
  -t 414380061457.dkr.ecr.us-east-1.amazonaws.com/spectra_meep:latest \
  --push \
  .
