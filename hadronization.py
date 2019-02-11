# fill dag with hadronization test jobs

import msg
import outputPaths
import os
import commonFunctions

nuPDG = {
  '1000' :  '14',
  '1100' :  '14',
  '1200' : '-14',
  '1300' : '-14'}
  
targetPDG = { 
  '1000' : '1000000010',
  '1100' : '1000010010',
  '1200' : '1000000010',
  '1300' : '1000010010'}

mcseed = "210921029"
nEvents = "100000"
energy = "0.5,80.0"  
generatorList = "HadronizationTest"
flux = "1/x"

def fillDAG ( jobsub, tag, date, paths, main_tune, tunes, regretags, regredir ):
  outputPaths.expand( paths['hadron'], tunes )
  fillDAG_GHEP (jobsub, tag, paths['xsec_N'], paths['hadron'], main_tune, tunes)
  # ---> No need ---> fillDAG_GST (jobsub, paths['hadron'], tunes)
  createFileList ( tag, date, paths['xsec_N'], paths['hadron'], paths['hadrep'], main_tune, tunes, regretags, regredir )
  fillDAG_data ( jobsub, tag, date, paths['xsec_N'], paths['hadron'], paths['hadrep'], main_tune, tunes, regretags, regredir )

def fillDAG_GHEP (jobsub, tag, xsec_n_path, out, main_tune, tunes):
  # check if job is done already
  if isDoneGHEP (out, tunes):
    msg.warning ("hadornization test ghep files found in " + out + " ... " + msg.BOLD + "skipping hadronization:fillDAG_GHEP\n", 1)
    return
  #not done, add jobs to dag
  msg.info ("\tAdding hadronization test (ghep) jobs\n")

  # in parallel mode
  jobsub.add ("<parallel>")

  # common configuration
  inputFile = "gxspl-vN-" + tag + ".xml"
  if not (main_tune is None):
     inputFile = main_tune + "-gxspl-vN-" + tag + ".xml"

  options   = " -n " + nEvents + " -e " + energy + " -f " + flux + " --seed " + mcseed + \
              " --cross-sections input/" + inputFile + " --event-generator-list " + generatorList
  if not (main_tune is None):
     options = options + " --tune " + main_tune

  # loop over keys and generate gevgen command
  for key in nuPDG.iterkeys():
    cmd = "gevgen " + options + " -p " + nuPDG[key] + " -t " + targetPDG[key] + " -r " + key
    logFile = "gevgen_" + key + ".log"
    jobsub.addJob (xsec_n_path + "/" + inputFile, out, logFile, cmd, None)
    # same for tunes if specified
    if not (tunes is None):
       for tn in range(len(tunes)):
	  optTune = " -n " + nEvents + " -e " + energy + " -f " + flux + " --seed " + mcseed + \
              " --cross-sections input/" + tunes[tn] + "-" + inputFile + " --event-generator-list " + generatorList
	  cmdTune = "gevgen " + optTune + " --tune " + tunes[tn] + " -p " + nuPDG[key] + " -t " + targetPDG[key] + " -r " + key + \
	             " -o " + tunes[tn] + "-gntp." + key + ".ghep.root"
	  jobsub.addJob( xsec_n_path+"/"+tunes[tn]+"/"+tunes[tn]+"-"+inputFile, out+"/"+tunes[tn], tunes[tn]+"-"+logFile, cmdTune, None )

  # done
  jobsub.add ("</parallel>")

def fillDAG_GST (jobsub, out, tunes):
  # check if job is done already
  if isDoneGST (out, tunes):
    msg.warning ("hadronization test gst files found in " + out + " ... " + msg.BOLD + "skipping hadronization:fillDAG_GST\n", 1)
    return
  # not done, add jobs to dag
  msg.info ("\tAdding hadronization test (gst) jobs\n")

  # in parallel mode
  jobsub.add ("<parallel>")
  # loop over keys and generate gntpc command
  for key in nuPDG.iterkeys():
    inputFile = "gntp." + key + ".ghep.root"
    logFile = "gntpc" + key + ".log"
    cmd = "gntpc -f gst -i input/" + inputFile
    jobsub.addJob (out + "/" + inputFile, out, logFile, cmd, None)
    # same for tunes if specified
    if not (tunes is None):
       for tn in range(len(tunes)):
          cmdTune = "gntpc -f gst -i input/" + tunes[tn] + "-" + inputFile
	  jobsub.addJob( out+"/"+tunes[tn]+"/"+tunes[tn]+"-"+inputFile, out+"/"+tunes[tn], tunes[tn]+"-"+logFile, cmdTune, None )

  # done
  jobsub.add ("</parallel>")

def fillDAG_data (jobsub, tag, date, xsec_n_path, outEvents, outRep, main_tune, tunes, regretags, regredir):
  # check if job is done already
  if isDoneData (tag, date, outRep):
    msg.warning ("hadronization test plots found in " + outRep + " ... " + msg.BOLD + "skipping hadronization:fillDAG_data\n", 1)
    return
  # not done, add jobs to dag
  msg.info ("\tAdding hadronization test (plots) jobs\n")    

  # in serial mode
  jobsub.add ("<serial>")
  inFile  = "file_list-" + tag + "-" + date + ".xml"
  cmd = "gvld_hadronization -g input/" + inFile 
  # add the command to dag
  inputs = outRep + "/" + inFile + " " + xsec_n_path + "/xsec-vN-" + tag + ".root " + outEvents + "/*.ghep.root"
  if not (main_tune is None):
     inputs = outRep + "/" + inFile + " " + xsec_n_path + "/" + main_tune + "-xsec-vN-" + tag + ".root " + outEvents + "/*.ghep.root"
  if not (tunes is None):
     for tn in range(len(tunes)):
        inputs = inputs + " " + xsec_n_path + "/" + tunes[tn] + "/" + tunes[tn] + "-xsec-vN-" + tag + ".root " + \
	         outEvents + "/" + tunes[tn] + "/*.ghep.root"
  logFile = "gvld_hadronz_test.log"
  regre = None
  if not (regretags is None):
     # check if input for regression is OK
     regreOK = commonFunctions.regreInputOK( "hadronization", regretags, regredir, len(nuPDG), "vN", "/xsec/nuN/" )
     if regreOK:
        # NOTE: no need to fetch rdate here; it'll just be part of regre_dir "leading" path
        regre = ""
        for rt in range(len(regretags)):
           rversion, rtune = regretags[rt].split("/")
	   regre = regre + regredir + "/" + regretags[rt] + "/xsec/nuN/"+ rtune + "-xsec-vN-" + rversion + ".root " 
	   regre = regre + regredir + "/" + regretags[rt] + "/events/hadronization/*.ghep.root "
     else:
        msg.info( "\t\tNO input for regression will be copied over \n" )
	regre = None

  jobsub.addJob ( inputs, outRep, logFile, cmd, regre )

  # done
  jobsub.add ("</serial>")
  
def isDoneGHEP (path, tunes):
  # check if given path contains all ghep files
  for key in nuPDG.iterkeys():
    if "gntp." + key + ".ghep.root" not in os.listdir (path): return False
    if not (tunes is None):
       for tn in range(len(tunes)):
          if tunes[tn] + "-gntp." + key + ".ghep.root" not in os.listdir (path+"/"+tunes[tn]): return False

  return True
  
def isDoneGST (path, tunes):
  # check if given path contains all gst files
  for key in nuPDG.iterkeys():
    if "gntp." + key + ".gst.root" not in os.listdir (path): return False
    if not (tunes is None):
       for tn in range(len(tunes)):
          if tunes[tn] + "-gntp." + key + ".gst.root" not in os.listdir (path+"/"+tunes[tn]): return False
    
  return True
  
def isDoneData (tag, date, path):
  # check if given path contains the plots
  if "genie_" + tag + "-hadronization_test.ps" not in os.listdir (path): return False
  return True
  
def createFileList ( tag, date, xsec_n_path, outEvent, outRep, main_tune, tunes, regretags, regredir ):

  msg.info ("\tCreate configuration XML for hadronization test \n")

  # create xml file with the file list in the format as src/scripts/production/misc/make_genie_sim_file_list.pl
  xmlFile = outRep + "/file_list-" + tag + "-" + date + ".xml"
  try: os.remove (xmlFile)
  except OSError: pass
  xml = open (xmlFile, 'w');
  print >>xml, '<?xml version="1.0" encoding="ISO-8859-1"?>'
  print >>xml, '<genie_simulation_outputs>'
  if (main_tune is None): 
     print >>xml, '\t<model name="default-' + tag + '-' + date + '">'
  else:
     print >>xml, '\t<model name="' + main_tune + '-' + tag + '-' + date + '">'
  for key in nuPDG.iterkeys():
    print >>xml, '\t\t<evt_file format="ghep"> input/gntp.' + key + '.ghep.root </evt_file>'
  if (main_tune is None):
     print >>xml, '\t\t<xsec_file> input/xsec-vN-' + tag + '.root </xsec_file>'
  else:
     print >>xml, '\t\t<xsec_file> input/' + main_tune + '-xsec-vN-' + tag + '.root </xsec_file>'
  print >>xml, '\t</model>'
  # same for tunes if specified
  if not (tunes is None):
     for tn in range(len(tunes)):
	print >>xml, '\t<model name="' + tunes[tn] + '-' + tag + '-' + date + '">'
	for key in nuPDG.iterkeys():
           print >>xml, '\t\t<evt_file format="ghep"> input/' + tunes[tn] + '-gntp.' + key + '.ghep.root </evt_file>'	
        print >>xml, '\t\t<xsec_file> input/' + tunes[tn] + '-xsec-vN-' + tag + '.root </xsec_file>'
	print  >>xml, '\t</model>'
  # regression if specified
  if not (regretags is None):
     # check if input for regression is OK
     regreOK = commonFunctions.regreInputOK( "hadronization", regretags, regredir, len(nuPDG), "vN", "/xsec/nuN/" )
     if regreOK:
        # need to fetch date stamp for the regression from the leading path
        # assume that regredir is always /leading/path/to/TIMESTAMP/Index
        # NOTE: redirect output of split(...) to a separate array; 
        #       otherwise len(...) will be the length of regredir, not the length of array after splitting
        regredir_tmp = regredir.split("/")
        rdate = regredir_tmp[len(regredir_tmp)-2] # i.e. one before the last     
        for rt in range(len(regretags)):
	   rversion, rtune = regretags[rt].split("/")
	   # print >>xml, '\t<model name="' + regretags[rt] + '">'
	   print >>xml, '\t<model name="' + rtune + '-' + rversion + '-' + rdate +  '">'     
	   for key in nuPDG.iterkeys():
              print >>xml, '\t\t<evt_file format="ghep"> input/regre/' + rdate + '/' + regretags[rt] + '/gntp.' + key + '.ghep.root </evt_file>'
           print  >>xml, '\t\t<xsec_file> input/regre/' + rdate + '/' + regretags[rt] + '/' + rtune + '-xsec-vN-' + rversion + '.root </xsec_file>'
	   print  >>xml, '\t</model>'
     else:
        msg.info( "\t\tNO REGRESSION due to missing/incorrect input files \n" )
  
  print >>xml, '</genie_simulation_outputs>'
  xml.close()

