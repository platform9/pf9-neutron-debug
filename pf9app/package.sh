#!/bin/bash

set -e
set -u
set -x

echo "Running package.sh"

if [ $# -ne 5 ]; then
    echo "$0 requires 5 arguments:"
    echo "   $1 -> version string major.minor"
    echo "   $2 -> buildnumber"
    echo "   $3 -> source dir"
    echo "   $4 -> output dir"
    echo "   $5 -> deb or rpm"
    exit 1
fi


version=$1
buildnum=$2
srcdir=`cd $3; pwd`
outdir=`cd $4; pwd`
pkgtype=$5
thisdir=`cd $(dirname $0); pwd`
#dependencies="-d pf9-bbslave"
srcroot=$(readlink -f $thisdir/../)

name=pf9-neutron-debug
githash=`git rev-parse --short HEAD`
arch=x86_64
desc="Platform9 Neutron Debug service, built from pf9-neutron-debug@$githash"
package=$outdir/$name-$version-$buildnum.$arch.$pkgtype


[ -e $package ] && rm $package

fpm -t $pkgtype -s dir -n $name \
    --workdir $outdir/fpm-work \
    --description "$desc" \
    --license "Commercial" \
    --architecture $arch \
    --url "http://www.platform9.com" \
    --vendor "Platform9 Systems, Inc." \
    --version $version \
    --iteration $buildnum \
    --provides $name \
    --provides pf9app \
    --directories /opt/pf9/${name} \
    #${dependencies} \
    --exclude "**opt/pf9/python**" \
    --package $package \
    -C $srcdir .

case $pkgtype in
rpm)
    $srcroot/sign_packages.sh $package
    ;;
deb)
    $srcroot/sign_packages_deb.sh $package
    ;;
esac
