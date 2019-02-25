#!/bin/bash

echo "@: $@"

while getopts p:v:o:i:l:c:d:r:R: OPT
do
  case ${OPT} in
    p) # path to genie top dir
      echo "opt p: OPTARG = $OPTARG"
      export GENIE=$OPTARG
      ;;
    v) # path to comparisons top dir
      echo "opt v: OPTARG = $OPTARG"
      export GENIE_COMPARISONS=$OPTARG
      ;;
    o) # output directory
      echo "opt o: OPTARG = $OPTARG"
      out=$OPTARG
      ;;
    i) # input files (fileA fileB fileC...)
      echo "opt i: OPTARG = $OPTARG"
      input=(`echo $OPTARG | sed 's/SPACE/ /g'`)
      ;;
    l) # logfile name
      echo "opt l: OPTARG = $OPTARG"
      log=$OPTARG
      ;;
    d) # print out to logfile
      echo "opt d: OPTARG = $OPTARG"
      debug=$OPTARG
      ;;
    c) # command to run
      echo "opt c: OPTARG = $OPTARG"
      cmd=`echo $OPTARG | sed 's/SPACE/ /g' | sed "s/SQUOTE/'/g"` 
      ;;
    r) # regression test
      echo "opt r: OPTARG = $OPTARG"
      regre=(`echo $OPTARG | sed 's/SPACE/ /g'`)
      ;;
    R) # Root version
      echo "opt R: OPTARG = $OPTARG"
      Root=$OPTARG
      ;;
  esac
done

### setup externals and paths ###

# export GUPSBASE=/cvmfs/fermilab.opensciencegrid.org/
# source $GUPSBASE/products/genie/externals/setup

# bootstrap setup off larsoft repo...
# ---> source /cvmfs/fermilab.opensciencegrid.org/products/genie/bootstrap_genie_ups.sh
source /cvmfs/fermilab.opensciencegrid.org/products/genie/bootstrap_genie_ups.sh


case ${Root} in
  5)
    setup root v5_34_36 -q nu:e9:prof
    setup lhapdf v5_9_1d -q e9:prof
    setup log4cpp v1_1_1d -q e9:prof
    break
    ;;
  6)
setup root v6_12_06a -q e17:prof
setup lhapdf v5_9_1k -q e17:prof
setup log4cpp v1_1_3a -q e17:prof
    break
    ;;
  *)
    echo "*** ATTENTION: Root version ${Root} unknown; ABORT !!!"
    exit 1
esac

export LD_LIBRARY_PATH=$GENIE/lib:$GENIE_COMPARISONS/lib:$LD_LIBRARY_PATH
export PATH=$GENIE/bin:$GENIE_COMPARISONS/bin:$PATH

echo "Command: "$cmd | tee $log
# echo "Input folder: " | tee -a $log
# ls -lh input | tee -a $log
echo "LD_LIBRARY_PATH = $LD_LIBRARY_PATH" | tee -a $log
echo "PATH = $PATH" | tee -a $log
echo "GENIE = $GENIE" | tee -a $log
echo "Contents of GENIE/bin: " | tee -a $log
echo `ls $GENIE/bin` | tee -a $log
#########################
echo ${LD_LIBRARY_PATH} | tr ":" "\n" | tee -a $log
echo ${PATH} | tr ":" "\n" | tee -a $log
pwd | tee -a $log
ls -lh | tee -a $log
which gmkspl | tee -a $log
##########################
echo "Running command" | tee -a $log

source /cvmfs/fermilab.opensciencegrid.org/products/common/etc/setups.sh
setup ifdhc

export IFDH_CP_MAXRETRIES=3

traperror () {
    local err=$1 # error status
    local line=$2 # LINENO
    local linecallfunc=$3
    local command="$4"
    local funcstack="$5"
    local errorfatal="${6:-0}"  ### by default errors are not fatal; i.e. use return instead of exit
    local CI_GRID_ERR_MSG=$(
    echo -e "### $0 MSG BEGIN"
    echo "ERROR: line $line - command '$command' exited with status: $err"
    if [ "$funcstack" != "::" ]; then
        echo -n "   ... Error at ${funcstack} "
        if [ "$linecallfunc" != "" ]; then
            echo -n "called at line $linecallfunc"
        fi
    else
        echo -n "   ... internal debug info from function ${FUNCNAME} (line $linecallfunc)"
    fi

    echo

    echo
    echo -e "### $0 MSG END")

    echo "${CI_GRID_ERR_MSG}"

    if [ "$errorfatal" -ne "0" ]; then
        echo "traperror exit: ${err}"
        export ci_traperror_exit_code=${err}
        echo "ci_traperror_exit_code: ${ci_traperror_exit_code}"
        exit ${err}
    else
        echo "traperror return: ${err}"
        export ci_traperror_exit_code=${err}
        echo "ci_traperror_exit_code: ${ci_traperror_exit_code}"
        return ${err}
    fi

}

# type traperror
# trap
trap 'traperror $? $LINENO $BASH_LINENO "$BASH_COMMAND" $(printf "::%s" ${FUNCNAME[@]}) $ERRORFATAL' ERR
# trap

ERRORFATAL=0 ### errors are not fatal; i.e. use return instead of exit

### load input (if defined) ###

#mkdir input
#for file in "${input[@]}"
#do
#  ifdh cp $file input
#done

# make a local copy od whatever /data from comparisons
cp -r $GENIE_COMPARISONS/data .

if [ "$input" != "none" ]; then

    echo "input is not none..." | tee -a $log

for token in "${input[@]}"
do

    idir=`dirname "$token"` 
    ipat=`basename "$token"`
# -->     idir=`dirname "$input"` 
# -->    ipat=`basename "$input"`
    echo "idir = $idir" | tee -a $log
    echo "ipat = $ipat" | tee -a $log
    # recall that `findMatchingFiles` recursively scans subdirs
    ifdh findMatchingFiles "$idir" "$ipat" | tee -a $log
    inputlist=`ifdh findMatchingFiles "$idir" "$ipat"`

    echo "making local input storage folder if not there yet.." | tee -a $log
    if [ ! -d "input" ]; then
       mkdir input
    fi

    echo "running ifdh fetch" | tee -a $log
    IFDH_DATA_DIR=./input ifdh fetchSharedFiles $inputlist

    if [ "$debug" == "true" ]
    then
        echo "Checking contents of local input folder: "
        ls -lh input
    fi
    echo "Checking contents of local input folder: " | tee -a $log
    ls -lh input | tee -a $log

done # end loop over tokens in input

fi  # check `input == none`

echo "regre = $regre"

if [ -n "$regre" -a "$regre" != "none" ]; then

    echo "regression test requested..." | tee -a $log

for rtoken in "${regre[@]}"
do

    rpat=`basename "$rtoken"`
    rdir=`dirname "$rtoken"`
    echo "rdir = $rdir" | tee -a $log
    echo "rpat = $rpat" | tee -a $log
    ifdh findMatchingFiles "$rdir" "$rpat" | tee -a $log
    regrelist=`ifdh findMatchingFiles "$rdir" "$rpat"`
   
    exp=`echo $rdir | awk -F '/' '{print $NF}'`
    rtune=`echo $rdir | awk -F '/' '{print $(NF-2)}'`
    rversion=`echo $rdir | awk -F '/' '{print $(NF-3)}'`
    rdate=`echo $rdir | awk -F '/' '{print $(NF-5)}'`
    
    echo "exp = $exp" | tee -a $log
    echo "rtune = $rtune" | tee -a $log
    echo "rdate = $rdate" | tee -a $log
    echo "rversion = $rversion" | tee -a $log
   
    echo "making local input/regression folder if not there yet.." | tee -a $log
    if [ ! -d "input/regre" ]; then
       mkdir input/regre
    fi
    if [ ! -d "input/regre/$rdate" ]; then
       mkdir input/regre/$rdate
    fi
    if [ ! -d "input/regre/$rdate/$rversion" ]; then
       mkdir input/regre/$rdate/$rversion
    fi
    if [ ! -d "input/regre/$rdate/$rversion/$rtune" ]; then
       mkdir input/regre/$rdate/$rversion/$rtune
    fi

    echo "running ifdh fetch for regression MC files" | tee -a $log
    IFDH_DATA_DIR=./input/regre/$rdate/$rversion/$rtune ifdh fetchSharedFiles $regrelist

    echo "Checking contents of local input/regression folder: " | tee -a $log
    ls -lh input/regre/$rdate/$rversion/$rtune | tee -a $log

done # end loop over rtokens in regre

fi # check `regre == "none" `

### run the command ###

if [ "$debug" == "true" ]
then
  echo "DEBUG MODE ON. ALL OUTPUT WILL BE COPIED TO LOG FILE"
  $cmd | tee -a $log
    # TODO: "grid debug" -> put output into grid log file?
    # $cmd
else
    # GENIE is pretty chatty, only save errors to log file
  $cmd 1>/dev/null 2> >( tee -a ${log} >&2 )
fi

### check for NaN's in the (output splines) XML files
### NOTE: this is essential for dag_1 and dag_3 
###       (generation of nu-nucleon and nu-nucleus/isotope splines, respectively)  
for xml in *gxs*.xml; do
   [[ ! -e ${xml} ]] && continue || :
   echo "Checking ${xml}"
   nans=`grep -i nan ${xml} || :`
   if [ ! -z "$nans" ]; then
      echo " ATTENTION: nan is detected in ${xml} output file generated by command ${cmd}; ABORT !!! " | tee bad_splines
      exit 81
   fi
done

### copy results to scratch

# first, remove size zero log files
logs=`ls *.log`
for logfile in $logs
do
    echo $logfile
    if [[ ! -s $logfile ]]; then
        echo "... is a zero size file, removing!"
        rm $logfile
    fi
done

# remove input-flux.root if any
rm -f input-flux.root

mkdir scratch
for f in $(find . -maxdepth 1 -type f -name \*.root -printf "%P\n" -o -name \*.xml -printf "%P\n" -o -name \*.log -printf "%P\n" -o -name \*.eps -printf "%P\n" -o -name \*.ps -printf "%P\n" -o -name \*.pdf -printf "%P\n" -o -name \*.txt -printf "%P\n" | sort )
do
  mv -v ${f} scratch
done

### mv *.root scratch
### mv *.xml scratch
### mv *.log scratch
### mv *.eps scratch
### mv *.ps scratch
### mv *.pdf scratch

if [ "$debug" == "true" ]
then
    echo "Checking output files..."
    ls scratch
fi

### copy everything from scratch to output 
# r. hatcher is dubious of `cp -r` in ifdhcp so we build a script.
# copy files one-by-one after making any necessary subdirectories
# use -x to enable echoing commands (+x to turn it back off)
cd scratch
# make a script to be sourced ...
rm -f copy_file.sh
touch copy_files.sh
# make any subdirectories (remove leading ./)
find . -type d -exec echo ifdh mkdir $out/{} \; | sed -e "s%\./%%g" >> copy_files.sh
# now any files (again removing leading ./)
find . -type f -exec echo ifdh cp {} $out/{} \; | sed -e "s%\./%%g" >> copy_files.sh
# now take `copy_files.sh` out of the file copy script
perl -ni -e 'print if !/copy_files/' copy_files.sh
echo "file copy script contents:" | tee -a $log
cat copy_files.sh | tee -a $log
set -x
source copy_files.sh
set +x
cd ..

# example (problems with " eaten by jobsub...)
# jobsub_submit -G genie -M --OS=SL6 --resource-provides=usage_model=DEDICATED,OPPORTUNISTIC file://runGENIE.sh -p /grid/fermiapp/genie/builds/genie_R-2_9_0_buildmaster_2015-10-27/ -o /pnfs/genie/scratch/users/goran/ -c "gmkspl -p 12 -t 1000010010 -n 500 -e 500 -o scratch/pgxspl-qel.xml --event-generator-list QE"
# temporary solution: use SPACE instead of spaces
# jobsub_submit -G genie -M --OS=SL6 --resource-provides=usage_model=DEDICATED,OPPORTUNISTIC file://runGENIE.sh -p /grid/fermiapp/genie/builds/genie_R-2_9_0_buildmaster_2015-10-27/ -o /pnfs/genie/scratch/users/goran/ -c "gmksplSPACE-pSPACE12SPACE-tSPACE1000010010SPACE-nSPACE500SPACE-eSPACE500SPACE-oSPACEscratch/pgxspl-qel.xmlSPACE--event-generator-listSPACEQE"

exit ${ci_traperror_exit_code}
