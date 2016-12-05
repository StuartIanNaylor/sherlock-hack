#bin/bash
########################################################
#
#  Makefile to install and run Sherlock_Hack.
#
########################################################

#First of all this isn't my code and being a noob all credit to the source.
#https://github.com/vmlaker/sherlock
#Who based it on the great work at http://bitbucket.org/cleemesser/numpy-sharedmem
#
#Which to be honest read what they say as all I have done is make it specific to face detection
#and removed some of the redundent code of previous examples.

echo 'Refresh repo & update system'
apt-get -y update

echo 'install compile tools'
apt-get -y install build-essential cmake cmake-curses-gui pkg-config git
apt-get -y install python-dev
pip install virtualenv 

echo 'install opencv'
pip install coils==1.0.9
pip install Cython==0.24
pip install mpipe==1.0.8
pip install numpy==1.11.0

apt-get -y install opencv-data libopencv-dev python-opencv



echo 'get nump-shared python module'
mkdir -p temp && \
cd temp && \
hg clone http://bitbucket.org/cleemesser/numpy-sharedmem && \
cd numpy-sharedmem && \
python setup.py install && \
cd ../.. && \
rm -rf temp

echo 'Hopefully now run the examples from the command line'

python ./src/object3.py


