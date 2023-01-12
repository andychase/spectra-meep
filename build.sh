set -e
set -x
apt-get update &&  \
    apt-get install -y \
    build-essential \
    swapspace \
    csh gfortran libatlas-base-dev libxc-dev curl cmake
if [ "$(arch)" == "aarch64" ]; then
  mv install.arm64.info install.info
  make clean
  find . -name "*.o" -type f -delete
  csh ./tools/lapack/download-lapack.csh
  make -j4 lapack
  sed -i 's/uname -p/uname -m/g' ./ddi/compddi
  csh ./ddi/compddi
  cp ./ddi/ddikick.x .
  make libxc -j4
  grep -rl -- "-mcmodel=medium" . | xargs sed -i "s/-mcmodel=medium/-mcmodel=small/g"
  make modules
  ./compall
  make
fi
