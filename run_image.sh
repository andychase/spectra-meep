set -e
set -x
# oracle
if grep -Fxq 'NAME="Oracle Linux Server"' /etc/os-release
then
dnf update -y
dnf config-manager --add-repo=https://download.docker.com/linux/centos/docker-ce.repo
dnf install docker-ce -y
systemctl start docker
systemctl enable docker

else

wget https://get.docker.com -O o.sh
bash o.sh
wget https://bootstrap.pypa.io/get-pip.py -O get-pip.py
python3 get-pip.py

fi

python3 -m pip install pip --upgrade
python3 -m pip install awscli
mkdir ~/.aws || true
cat << EOF > ~/.aws/credentials
[default]
aws_access_key_id = <Key here>
aws_secret_access_key = <Secret here>
EOF
python3 -m awscli ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 414380061457.dkr.ecr.us-east-1.amazonaws.com
docker pull 414380061457.dkr.ecr.us-east-1.amazonaws.com/spectra_meep
docker run -d 414380061457.dkr.ecr.us-east-1.amazonaws.com/spectra_meep bash -c "while true; do python ./src/aws.py; sleep 10; done"
