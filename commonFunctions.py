
import msg
import os

# no need for commands package sinse IFDH functionalities are required 
# to make it all work with dCache which is not mounted on a Jenkins build node
# --> import commands

# Note: ifdh module is a python API to IFDH toolkit that's "local FNAL development
#       in order to make python find this module one must first setup IFDH as follows:
#       source /cvmfs/fermilab.opensciencegrid.org/products/common/etc/setups.sh
#       setup ifdhc
#
import ifdh

IFDH=ifdh.ifdh()

# this is general enough to put in here 
nevents="100000"

def fillDAG_GHEP( meta, data_struct, jobsub, tag, xsec_a_path, out, main_tune, tunes ):

   if eventFilesExist( data_struct, out, tunes):
      msg.warning ( meta['Experiment'] + " test ghep files found in " + out + " ... " + msg.BOLD + "skipping " + meta['Emperiment'].lower() + ":fillDAG_GHEP\n", 1)
      return

   msg.info ("\tAdding " + meta['Experiment'] + " test (ghep) jobs\n")

   # in parallel mode
   jobsub.add ("<parallel>")

   # common configuration
   inputxsec = "gxspl-vA-" + tag + ".xml"
   if not (main_tune is None):
      inputxsec = main_tune + "-gxspl-vA-" + tag + ".xml"

   options = " -t " + meta['target'] + " --cross-sections input/" + inputxsec 
   if not (main_tune is None):
      options = options + " --tune " + main_tune

   for key in data_struct.iterkeys():
     opt = options + " -n " + nevents
     cmd = "gevgen " + opt + " -p " + data_struct[key]['projectile'] + " -e " + data_struct[key]['energy'] + \
           " -f " + data_struct[key]['flux'] + " -o gntp." + key + "-" + data_struct[key]['releaselabel'] + ".ghep.root"
     logfile = "gevgen_" + key + ".log"
     # NOTE: FIXME - CHECK WHAT IT DOES !!!
     jobsub.addJob ( xsec_a_path+"/"+inputxsec, out, logfile, cmd, None )
     # same for tunes if specified
     if not ( tunes is None):
        for tn in range(len(tunes)):
	   optTune = " -t " + meta['target'] + " --cross-sections input/" + tunes[tn] + "-gxspl-vA-" + tag + ".xml -n " + nevents
	   cmdTune = "gevgen " + optTune + " --tune " + tunes[tn] + " -p " + data_struct[key]['projectile'] + " -e " + data_struct[key]['energy'] + \
	             " -f " + data_struct[key]['flux'] + " -o " + tunes[tn] + "-gntp." + key + "-" + data_struct[key]['releaselabel'] + ".ghep.root"
	   jobsub.addJob( xsec_a_path+"/"+tunes[tn]+"/"+tunes[tn]+"-"+inputxsec, out+"/"+tunes[tn], tunes[tn]+"-"+logfile, cmdTune, None )

   # done
   jobsub.add ("</parallel>")
 
def createCmpConfigs( meta, data_struct, tag, date, reportdir, main_tune, tunes, regretags, regredir ):

   # not done, add jobs to dag
   msg.info ("\tCreate configuration XML for " + meta['Experiment'] + " test\n")  

   # NOTE: it's not very nice that "vA" and "/xsec/nuA/" are hardcoded here...
   #       should fine a way to make more configurable, such that this kind
   #       of info/specs stays on the app side only...
   #
   bname = os.path.basename( reportdir )
   regreOK = regreInputOK( bname, regretags, regredir, len(data_struct), "vA", "/xsec/nuA/" )

   for key in data_struct.iterkeys():
      gcfg = reportdir + "/cmp-" + data_struct[key]['releaselabel'] + "-" + tag + "_" + date + ".xml"
      gsim = "/gsimfile-" + data_struct[key]['releaselabel'] + "-" + tag + "_" + date + ".xml"
      gsimfile = reportdir + gsim
      try: os.remove(gcfg)
      except OSError: pass
      try: os.remove(gsimfile)
      except OSError: pass
      gxml = open( gcfg, 'w' )
      print >>gxml, '<?xml version="1.0" encoding="ISO-8859-1"?>'
      print >>gxml, '<config>'
      print >>gxml, '\t<experiment name="' + meta['Experiment'] + '">'
      print >>gxml, '\t\t<paths_relative_to_geniecmp_topdir> false </paths_relative_to_geniecmp_topdir>'

      print >>gxml, '\t\t\t<comparison>'

      for i in range( len( data_struct[key]['datafiles'] ) ):
         print >>gxml, '\t\t\t\t<spec>'
         print >>gxml, '\t\t\t\t\t<path2data> data/measurements/vA/' + meta['Experiment'].lower() + '/' + data_struct[key]['datafiles'][i] + ' </path2data>'
         print >>gxml, '\t\t\t\t\t<dataclass> ' + data_struct[key]['dataclass'] + ' </dataclass>'
         print >>gxml, '\t\t\t\t\t<predictionclass> ' + data_struct[key]['mcpredictions'][i] + ' </predictionclass>'
         print >>gxml, '\t\t\t\t</spec>'
      
      print >>gxml, '\t\t\t\t<genie> input' + gsim + ' </genie>'
      print >>gxml, '\t\t\t</comparison>'
      # now finish up and close global config
      print >>gxml, '\t</experiment>'
      print >>gxml, '</config>'
      gxml.close()
      
      xml = open( gsimfile, 'w' )
      print >>xml, '<?xml version="1.0" encoding="ISO-8859-1"?>'
      print >>xml, '<genie_simulation_outputs>'
      if ( main_tune is None):
         print >>xml, '\t<model name="' + tag + '-' + date + ':default:' + data_struct[key]['releaselabel'] + '">'
      else:
         print >>xml, '\t<model name="' + tag + '-' + date + ':' + main_tune + ':' + data_struct[key]['releaselabel'] + '">'
      print >>xml, '\t\t<evt_file format="ghep"> input/gntp.' + key + '-' + data_struct[key]['releaselabel'] + '.ghep.root </evt_file>'
      if ( main_tune is None):
         print >>xml, '\t\t<xsec_file> input/xsec-vA-' + tag + '.root </xsec_file>'
      else:
         print >>xml, '\t\t<xsec_file> input/' + main_tune + '-xsec-vA-' + tag + '.root </xsec_file>'
      print >>xml, '\t</model>'
      #tunes if specified
      if not (tunes is None):
         for tn in range(len(tunes)):
	    print >>xml, '\t<model name="' + tag + '-' + date + ':' + tunes[tn] + ':' + data_struct[key]['releaselabel'] + '">'
	    print >>xml, '\t\t<evt_file format="ghep"> input/' + tunes[tn] + '-gntp.' + key + "-" + data_struct[key]['releaselabel'] + '.ghep.root </evt_file>'
            print >>xml, '\t\t<xsec_file> input/' + tunes[tn] + '-xsec-vA-' + tag + '.root </xsec_file>'
	    print >>xml, '\t</model>'
      # regression if specified
      if not (regretags is None):
         if regreOK:
            # need to fetch date stamp for the regression from the leading path
            # assume that regredir is always /leading/path/to/TIMESTAMP/Index
            # NOTE: redirect output of split(...) to a separate array; 
            #       otherwise len(...) will be the length of regredir, not the length of array after splitting
            regredir_tmp = regredir.split("/")
            rdate = regredir_tmp[len(regredir_tmp)-2] # i.e. one before the last     
            for rt in range(len(regretags)):
	       rversion, rtune = regretags[rt].split("/")
	       # print >>xml, '\t<model name="' + regretags[rt] + ":default:" + data_struct[key]['releaselabel'] + '">'
	       print >>xml, '\t<model name="' + rversion + '-' + rdate + ':' + rtune + ':' +  data_struct[key]['releaselabel'] + '">'
	       print >>xml, '\t\t<evt_file format="ghep"> input/regre/' + rdate + "/" + regretags[rt] + '/gntp.' + key + '-' + data_struct[key]['releaselabel'] + '.ghep.root </evt_file>'
               print >>xml, '\t\t<xsec_file> input/regre/' + rdate + '/' + regretags[rt] + '/' + rtune + '-xsec-vA-' + rversion + '.root </xsec_file>'
	       print >>xml, '\t</model>'
         else:
            msg.info( "\t\tNO REGRESSION due to missing/incorrect input files \n" )     
	 
      print >>xml, '</genie_simulation_outputs>'
      xml.close()   

def fillDAG_cmp( meta, data_struct, jobsub, tag, date, xsec_a_path, eventdir, reportdir, main_tune, tunes, regretags, regredir ):

   # check if job is done already
   if resultsExist ( data_struct, tag, date, reportdir ):
      msg.warning ( meta['Experiment'] + " comparisons plots found in " + reportdir + " ... " + msg.BOLD + "skipping " + meta['Experiment'].lower() + ":fillDAG_cmp\n", 1)
      return

   # not done, add jobs to dag
   msg.info ("\tAdding " + meta['Experiment'] + " comparisons (plots) jobs\n")  
     
   # in serial mode
   jobsub.add ("<parallel>")

   inputs = reportdir + "/*.xml " + xsec_a_path + "/xsec-vA-" + tag + ".root " + eventdir + "/*.ghep.root "
   if not (main_tune is None):
      inputs = reportdir + "/*.xml " + xsec_a_path + "/" + main_tune + "-xsec-vA-" + tag + ".root " + eventdir + "/*.ghep.root "
   if not (tunes is None):
      for tn in range(len(tunes)):
	 inputs = " " + inputs + xsec_a_path + "/" + tunes[tn] + "/" + tunes[tn] + "-xsec-vA-" + tag + ".root " \
	           + eventdir + "/" + tunes[tn] + "/*.ghep.root "
   regre = None
   if not (regretags is None):
      # NOTE: it's not very nice that "vA" and "/xsec/nuA/" are hardcoded here...
      #       should fine a way to make more configurable, such that this kind
      #       of info/specs stays on the app side only...
      #       in principle, "/xsec/nuA/" can be decoded from xsec_a_path...
      #
      bname = os.path.basename( eventdir )
      regreOK = regreInputOK( bname, regretags, regredir, len(data_struct), "vA", "/xsec/nuA/" )
      if regreOK:
         regre = ""
         for rt in range(len(regretags)):
            rversion, rtune = regretags[rt].split("/")
	    regre = regre + regredir + "/" + regretags[rt] + "/xsec/nuA/" + rtune + "-xsec-vA-" + rversion + ".root " 
            regre = regre + regredir + "/" + regretags[rt] + "/events/" + bname + "/*.ghep.root "
      else:
         msg.info( "\t\tNO input for regression will be copied over \n" )
	 regre = None

   for key in data_struct.iterkeys():
      inFile = "cmp-" + data_struct[key]['releaselabel'] + "-" + tag + "_" + date + ".xml"
      outFile = "genie_" + tag + "_" + data_struct[key]['releaselabel']
      tablechi2 = "genie_" + tag + "_" + data_struct[key]['releaselabel'] + "-summary-chi2.txt"
      tableks = "genie_" + tag + "_" + data_struct[key]['releaselabel'] + "-summary-KS.txt"
      cmd = "gvld_general_comparison --no-root-output --global-config input/" + inFile + " -o " + outFile 
      cmd = cmd + " --summary-chi2-table " + tablechi2
      cmd = cmd + " --summary-KS-table " + tableks
      logfile = data_struct[key]['releaselabel'] + ".log"
      jobsub.addJob ( inputs, reportdir, logfile, cmd, regre )

   # done
   jobsub.add ("</parallel>")

def eventFilesExist( data_struct, path, tunes ):

   for key in data_struct.iterkeys():
      if "gntp." + key + "-" + data_struct[key]['releaselabel'] + ".ghep.root" not in os.listdir(path): return False
      if not (tunes is None):
         for tn in range(len(tunes)):
	    if tunes[tn] + "-gntp." + key + ".ghep.root" not in os.listdir(path+"/"+tunes[tn]): return False

   return True

def resultsExist( data_struct, tag, date, path ):

  # check if given path contains all plots  
   for key in data_struct.iterkeys():
      outFile = "genie_" + tag + "_" + data_struct[key]['releaselabel'] + ".pdf"
      if outFile not in os.listdir (path): return False
   
   return True

def regreInputOK( cmp_app, regretags, regredir, nreqfiles, xsec_id, xsec_subpath ):

  if not (regretags is None):

     # need to fetch date stamp for the regression from the leading path
     # assume that regredir is always /leading/path/to/TIMESTAMP/Index
     # NOTE: redirect output of split(...) to a separate array; 
     #       otherwise len(...) will be the length of regredir, not the length of array after splitting
     regredir_tmp = regredir.split("/")
     rdate = regredir_tmp[len(regredir_tmp)-2] # i.e. one before the last     

     regre_xsec_exists = True
     regre_events_exist = True
     for rt in range(len(regretags)):
        rversion, rtune = regretags[rt].split("/")
	if not xsec_id is None and not xsec_subpath is None:
	   #
	   # NOTE: this will NOT work for /pnfs on a Jenkins build node because dCache is NOT mounted there
	   #
	   # --> if rtune + "-xsec-" + xsec_id + "-" + rversion + ".root" not in os.listdir(regredir + "/" + regretags[rt] + xsec_subpath): 
	   #
	   # instead we have to use (pyton interface to) IFDH tools
	   #
	   xsec_found = IFDH.findMatchingFiles( regredir + "/" + regretags[rt] + xsec_subpath, rtune + "-xsec-" + xsec_id + "-" + rversion + ".root" )
	   if ( len(xsec_found) <= 0 ):
	       msg.info( "\t\tinput XSec for regression does NOT exits: " + regredir + "/" + regretags[rt] + xsec_subpath + rtune + "-xsec-" + vN + "-" + rversion + ".root " )
	       regre_xsec_exists = False
	#
	# NOTE: this will NOT work for /pnfs on a Jenkins build node because dCache is NOT mounted there
	#
	# --> regfiles = regredir + "/" + regretags[rt] + "/events/" + cmp_app + "/*.ghep.root"
	# --> retcode, nevfiles =  commands.getstatusoutput("ls -alF " + regfiles + " | wc -l")
	# --> if ( int(nevfiles) != nreqfiles ): 
	#
	# instead we have to use (pyton interface to) IFDH tools
	#
	evfiles_found = IFDH.findMatchingFiles( regredir + "/" + regretags[rt] + "/events/" + cmp_app + "/", "*.ghep.root" )	
	if ( len(evfiles_found) != nreqfiles ): 
	   msg.info( "\t\tTune " + rtune + " : incorrect number of event samples for regression: " + str(len(evfiles_found)) + "; it should be: " + str(nreqfiles) )
	   regre_events_exist = False

     return  ( regre_xsec_exists and  regre_events_exist )
   
  return False
