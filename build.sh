apt-get update &&  \
    apt-get install -y \
    build-essential \
    swapspace \
    csh gfortran libatlas-base-dev libxc-dev curl cmake
[ $(arch) == "aarch64" ] && mv install.arm64.info install.info
csh ./tools/lapack/download-lapack.csh 
make -j4 lapack
sed -i 's/uname -p/uname -m/g' ./ddi/compddi
csh ../ddi/compddi
cp ./ddi/ddikick.x .
make libxc -j4
make modules
make

