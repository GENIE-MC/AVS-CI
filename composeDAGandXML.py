#!/usr/bin/env python

from jobsub import Jobsub
# services
import parser, msg
import outputPaths
# xsec splines
import nun, nua
# "sanity check" (events scan)
import standard
# old-style validation
import hadronization
# new-style validation (sec, minerva, t2k, etc.)
import xsecval, minerva, t2k, miniboone
# general
import os, datetime

#
# Note: in the "guts" this machinery uses ifdh module 
#       which is a python API to IFDH, a "local" FNAL set of tools
#       in order to work, one must first set it up as follows:
#       source /cvmfs/fermilab.opensciencegrid.org/products/common/etc/setups.sh
#       setup ifdhc
#

# Example format:
# ./composeDAGandXML.py --genie_tag master  \ 
#                          --build_date YYYY-MM-DD  \
#                          --run_path /path/to/runGENIE.sh \ # e.g. /grid/fermiapp/genie/legacyValidation_update_1/runGENIE.sh
#                          --builds DUMMY \ 
#                          --output OUTPUT \ # e.g. /pnfs/genie/scratch/users/yarba_j/GENIE_LegacyValidation 
#  optional:               [ --main_tune the_tune ]
#  optional:               [ --add_tunes tune1,tune2,...]  # comma-separated !!!
#  optional:               [ --regre Revision/Tune,RegTag2,RegTag3,... --regre_dir /pnfs/genie/persistent/users/yarba_j/GENIE_LegacyValidation/Root<5/6>TimeStamp/Index ]
#                    e.g.    --regre R-2_12_10/Default --regre_dir /pnfs/genie/persistent/users/geniepro/GENIE_CI_Validation/Root5/2018-02-07/00 
#
# OLD FORMAT
#  optional:               [ --tunes tune1,tune2,...]  # comma-separated !!!
#  optional:               [ --regre R-2_12_6/2017-09-11,RegTag2,RegTag3,... --regre_dir /pnfs/genie/persistent/users/yarba_j/GENIE_LegacyValidation ]
#

def initMessage (args):
  print msg.BLUE
  print '*' * 80
  print '*', ' ' * 76, '*'
  print "*\tGENIE Legacy Validation based on src/scripts/production/batch", ' ' * 8, '*'
  print '*', ' ' * 76, '*'
  print '*' * 80
  print msg.GREEN
  print "Configuration:\n"
  print "\tGENIE version:\t", args.tag
  print "\tBuild on:\t", args.build_date
  print "\tLocated at:\t", args.builds
  print "\n\tResults folder:", args.output
  print msg.END

if __name__ == "__main__":
  
  
  # parse command line arguments
  args = parser.getArgs()
  print "CHECK DATE: ", args.build_date
  # if build date is not defined/specified, use today's date as default
  if args.build_date is None:
     print "DATE is None, reseting it to DEFAULT(today)"
     #
     # NOTE-1: os.system('date +%Y-%m-%d') will return an integer status !!!
     # NOTE-2: os.popen('date +%Y-%m-%d').read() will results in the "?" question mark at the end of the string
     # NOTE-3: the "%y-%m-%d" will result in the YY-MM-DD format
     #
     args.build_date = datetime.date.today().strftime("%Y-%m-%d") 
  
  
  if args.main_tune is None:
     args.main_tune = "Default"
  
  if args.root_version is None:
     args.root_version = "Root6"
  
  
  # print configuration summary
  initMessage (args)
  
  # preapre folder(s) structure for output
  # 12/12/2018 - remove build_date from the path; it'll be embeded by the CI machinery
  #              instead, use (main_)tune
#  args.paths = outputPaths.prepare ( args.output + "/" + args.tag + "/" + args.build_date )
  args.paths = outputPaths.prepare ( args.output + "/" + args.tag + "/" + args.main_tune )

  # initialize jobsub 
  #
  # NOTE: at this point, we are using it only to fill up DAGs;
  #       we are not submitting anything...
  #       ...maybe the DGA-filling part needs to make into a separate module ?
  #
  args.buildNameGE = "generator_" + args.tag + "_" + args.build_date
  args.buildNameCmp = "comparisons_" + args.cmptag + "_" + args.build_date

  # tune(s) (optional)
  if not (args.add_tunes is None):
     args.add_tunes = args.add_tunes.split(",")
     # weed out additional tune thaat's the same as main_tune (if any)
     add_tunes_tmp = []
     for tn in range(len(args.add_tunes)):
        if ( args.add_tunes[tn].find(args.main_tune) == -1 ):
	   add_tunes_tmp.append( args.add_tunes[tn] )
     if not add_tunes_tmp:
        print msg.RED
	print "\tNo additional tune(s) that are different from main_tune " + args.main_tune + "; set additional tunes to None"
	print mas.END
	args.add_tunes = None
     else:
        args.add_tunes = add_tunes_tmp
  
  # regresion tests (optional)
  if not (args.regretags is None):
     args.regretags = args.regretags.split(",")
     regretags_tmp = []
     # here we also have to select only those that match the main_tune
     for rt in range(len(args.regretags)):
	if ( args.regretags[rt].find("/"+args.main_tune) != -1 ):
	   regretags_tmp.append(args.regretags[rt])  # to remove, use pop[rt]  	
     if not regretags_tmp:
        print msg.RED
        print "\tNo tags in the regression list match main_tune " + args.main_tune + "; set regression to None"
        print msg.END
	args.regretags = None
     else:
        args.regretags = regretags_tmp
     #
     # also need to check/assert that args.regredir is not None !!! otherwise throw !!!
     # assert ( not (args.regredir is None) ), "Path to regression dir is required for regression tests"
     if args.regredir is None: raise AssertionError

  jobsub = Jobsub (args)

  # fill dag files with jobs
  msg.info ("Adding jobs to dag file: " + jobsub.dagFile + "\n")
  
  # nucleon cross sections
  nun.fillDAG ( jobsub, args.tag, args.paths, args.main_tune, args.add_tunes )
  
  # nucleus cross sections
  nua.fillDAG ( jobsub, args.tag, args.paths, args.main_tune, args.add_tunes )
  
  # standard mc sanity check (events scan)
  standard.fillDAG( jobsub, args.tag, args.paths, args.main_tune ) # NO ADDITIONAL TUNES assumed !!!
  
  # xsec validation
  xsecval.fillDAG( jobsub, args.tag, args.build_date, args.paths, args.main_tune, args.add_tunes, args.regretags, args.regredir ) 
  
  # hadronization test
  hadronization.fillDAG ( jobsub, args.tag, args.build_date, args.paths, args.main_tune, args.add_tunes, args.regretags, args.regredir )
  
  # MINERvA test
  minerva.fillDAG( jobsub, args.tag, args.build_date, args.paths, args.main_tune, args.add_tunes, args.regretags, args.regredir )
  
  # T2K
  # NOTE (JVY): NO regression test so far since we don't have anything for T2k from GENIE v2_x_y
  # NOTE (JV): starting Feb.2019, add regression test since we now have some event files for T2K for master and/or R-3_00_xx series
  t2k.fillDAG( jobsub, args.tag, args.build_date, args.paths, args.main_tune, args.add_tunes, args.regretags, args.regredir )
  
  # MiniBooNE
  # NOTE (JVY): NO regression test so far since we don't have anything for MiniBooNE from GENIE v2_x_y
  # NOTE (JV): starting Feb.2019, add regression test since we now have some event files for MiniBooNE for master and/or R-3_00_xx series
  miniboone.fillDAG( jobsub, args.tag, args.build_date, args.paths, args.main_tune, args.add_tunes, args.regretags, args.regredir )
