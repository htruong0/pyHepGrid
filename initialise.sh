#!/bin/bash

export LFC_HOST=lfc.grid.sara.nl
export LCG_CATALOG_TYPE=lfc
export LFC_HOME=/grid/pheno/morgan
export LCG_GFAL_INFOSYS=lcgbdii.gridpp.rl.ac.uk:2170

NNLOJETDIR=/mt/home/morgan/NNLOJET
LHAPDFDIR=/mt/home/morgan/NNLOJET/driver/LHAPDF
RUNCARDS=/mt/home/morgan/NNLOJET/driver/grid # changeme
GCCDIR=/mt/home/morgan/gcc-5.2.0/


LFN=lfn:/grid/pheno/morgan/
SRM=srm://se01.dur.scotgrid.ac.uk/dpm/dur.scotgrid.ac.uk/home/pheno/morgan_dir

all=$1

cp $NNLOJETDIR/driver/NNLOJET .
cp -r $RUNCARDS .

if [ $all == 'all' ] ; then
    echo "Initialising full local directory"
    cp -r $LHAPDFDIR .
    cp -r $GCCDIR ./gcc
    tar -czf local.tar.gz LHAPDF gcc
    #LFN
    lcg-del -a lfn:input/local.tar.gz
    lcg-cr --vo pheno -l lfn:input/local.tar.gz  file:$PWD/local.tar.gz
    #SRM
    #lcg-del $SRM/input/local.tar.gz
    #lcg-cp $PWD/local.tar.gz $SRM/input/local.tar.gz
    #GRID_FILE=$(lcg-rf $SRM/input/local.tar.gz -l $LFN/input/local.tar.gz)
fi

echo "Initialising NNLOJET"
lcg-del -a lfn:input/NNLOJET.tar.gz
tar -czf NNLOJET.tar.gz NNLOJET *.RRa *.RRb *.vRa *.vRb *.vBa *.vBb grid
lcg-cr --vo pheno -l lfn:input/NNLOJET.tar.gz  file:$PWD/NNLOJET.tar.gz

