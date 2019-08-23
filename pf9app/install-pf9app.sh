#!/bin/bash

set -e
set -u
set -x

echo "Running install-pf9app: args $@"

if [ "$#" -ne 3 ]
then
    echo "$0 requires three arguments:"
    echo '   $1 -> root directory for the build'
    echo '   $2 -> python binary to use for the virtualenv'
    echo '   $3 -> system type: debian or redhat'
    exit 1
else
    buildroot=`cd $1; pwd`
    python=$2
    systemtype=$3
    mkdir -p $buildroot
fi

appname="pf9-designate"

# package source relative to this file:
srcroot="`cd $(dirname $0); pwd`"
parent_dir="`cd $(dirname $0)/..; pwd`"
config_dir="opt/pf9/etc/${appname}"
echo "SRCROOT = $srcroot"
echo "PARENTDIR = $parent_dir"

# virtualenv and setup
venv_relative=opt/pf9/${appname}
venv="${buildroot}/${venv_relative}"
virtualenv -p ${python} ${venv}
pushd ${parent_dir}
PIP_CACHE_DIR=~/.cache/pip-py27-netsvc ${venv}/bin/python ${venv}/bin/pip install opt/pf9/${appname}/requirements.txt
popd

# remove tests
#rm -rf ${buildroot}/opt/pf9/${appname}/lib/python2.7/site-packages/designate/tests

# remove venv/etc/designate directory
#rm -rf ${buildroot}/opt/pf9/${appname}/etc/designate

# copy hostagent config file
cp ${srcroot}/config ${buildroot}/opt/pf9/${appname}

# etc files
install -d -m 755 ${buildroot}/etc
#install -d -m 755 ${buildroot}/etc/cron.d
#install -d -m 755 ${buildroot}/etc/logrotate.d
install -d -m 755 ${buildroot}/${config_dir}
#cp -r ${srcroot}/etc/sudoers.d ${buildroot}/etc
cp -r ${parent_dir}/etc/neutron-debug.conf ${buildroot}/${config_dir}
#cp ${parent_dir}/etc/designate/pools* ${buildroot}/${config_dir}
#cp ${parent_dir}/etc/designate/rootwrap.conf ${buildroot}/${config_dir}/rootwrap.conf
#cp -r ${parent_dir}/etc/designate/rootwrap.d ${buildroot}/${config_dir}

# copy rootwrap-helper to preserve environment variables
#install -p -m 0755 ${srcroot}/designate-rootwrap-helper ${buildroot}/opt/pf9/${appname}/bin/

# copy designate-manage script to /usr/sbin
#install -d -m 0755 ${buildroot}/usr/sbin
#install -p -m 0755 ${srcroot}/designate-manage ${buildroot}/usr/sbin/

# copy logrotate and cron config
#install -p -m 0755 ${srcroot}/designate-cron-conf ${buildroot}/etc/cron.d/pf9-designate
#install -p -m 0644 ${srcroot}/designate-logrotate-conf ${buildroot}/etc/logrotate.d/pf9-designate

# init.d scripts - worker and mdns
mkdir -p ${buildroot}/etc/init.d
cp ${srcroot}/etc/init.d/initd.template.${systemtype} ${buildroot}/etc/init.d/pf9-neutron-debug
sed -i "s/suffix=.*/suffix=worker/" ${buildroot}/etc/init.d/pf9-neutron-debug
#cp ${srcroot}/etc/init.d/initd.template.${systemtype} ${buildroot}/etc/init.d/pf9-neutron-debug-mdns
#sed -i "s/suffix=.*/suffix=mdns/" ${buildroot}/etc/init.d/pf9-neutron-debug-mdns

# patch the #!python with the venv's python
sed -i "s/\#\!.*python/\#\!\/opt\/pf9\/${appname}\/bin\/python/" \
        ${venv}/bin/*
