#docker buildx build --platform=linux/arm64 -t 414380061457.dkr.ecr.us-east-1.amazonaws.com/spectra_meep:arm --push .
docker buildx build --platform=linux/amd64 -t 414380061457.dkr.ecr.us-east-1.amazonaws.com/spectra_meep:amd --push .
docker manifest rm 414380061457.dkr.ecr.us-east-1.amazonaws.com/spectra_meep:latest
docker manifest create \
  414380061457.dkr.ecr.us-east-1.amazonaws.com/spectra_meep:latest \
  414380061457.dkr.ecr.us-east-1.amazonaws.com/spectra_meep:arm \
  414380061457.dkr.ecr.us-east-1.amazonaws.com/spectra_meep:amd
docker manifest push 414380061457.dkr.ecr.us-east-1.amazonaws.com/spectra_meep:latest
