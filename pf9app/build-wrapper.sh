#!/bin/bash

set -e
set -u
set -x

echo "Running build-wrapper.sh"

thisdir=$(dirname $(readlink -f $0))
srcroot=$(cd $thisdir/..; pwd)
rpmbuild=$srcroot/build/wrapper
spec=$thisdir/wrapper.spec

# teamcity sets BUILD_NUMBER, if it's not set, use 0
buildnum=${BUILD_NUMBER:-0}
version=${PF9_VERSION:-3.1.0}
rpm_version=${version}-${buildnum}
githash=`git rev-parse --short HEAD`
arch=x86_64

for i in BUILD RPMS SOURCES SPECS SRPMS
do
    mkdir -p $rpmbuild/${i}
done

cp $spec $rpmbuild/SPECS/

# Copy packages
srcpkgbase=pf9-neutron-debug-$rpm_version
cp $srcroot/build/pf9app/neutron-debug/*.$arch.deb $rpmbuild/BUILD/
cp $srcroot/build/pf9app/neutron-debug/*.$arch.rpm $rpmbuild/BUILD/

# Copy role json
sed -e "s/__VERSION__/${rpm_version}/" $thisdir/neutron-debug-role.json > $rpmbuild/BUILD/pf9-neutron-debug-role.json

rpmbuild -bb \
         --define "_topdir $rpmbuild"  \
         --define "_srcpkgbase $srcpkgbase" \
         --define "_version $version"  \
         --define "_buildnum $buildnum" \
         --define "_githash $githash" \
         $spec

${srcroot}/sign_packages.sh ${rpmbuild}/RPMS/*/pf9-neutron-debug-app-wrapper*.rpm
