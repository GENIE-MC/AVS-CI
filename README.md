# AVS-CI
Automated Validation Suite - Continuous Integration

   General Information

GENIE validation and MC-to-data comparisons chain that runs weekly at Fermilab,
using Fermigrid resources, based on the CI (cont.itegration) machinery (genie_ci):
https://cdcvs.fnal.gov/redmine/projects/genie_ci/wiki


The following steps are currently included in the chain:

* generation of (anti)neutrino-nucleon splines (per nu-flavor, per nucleon, then merged)
* generation of (anti)neutrino-nucleui splines (per nucleus, then merged)
* "sanity checks" (checks for conservations, etc.)
** generation of event GENIE samples
** run gevscan utility to detect non-conservations
* XSec benchmark
** generation of GENIE event samples
** run gvld_general_comparion application with various configurations to benchmark vs data
* Hadronization benchmark
** generation of GENIE event samples
** run gvld_hadronization application to benchmark vs various bubble chamber data
* MINERvA benchmark
** generattion of GENIE event samples
** run gvld_general_comparison to benchmark GENIE preditions vs MINERvA data
* T2K benchmark
** generattion of GENIE event samples
** run gvld_general_comparison to benchmark GENIE preditions vs selected T2K data
* MiniBooNE benchmark
** generattion of GENIE event samples
** run gvld_general_comparison to benchmark GENIE preditions vs selected MiniBooNE data

Results in a form of logfiles ("sanity check") or plot books are posted to the CI dashboard;
please see monitoring instructions:
https://cdcvs.fnal.gov/redmine/projects/genie_ci/wiki/How_to_monitor_the_status_of_your_build


   Additional Information

Initial version was based on code by Tomasz Golan.

* https://github.com/TomaszGolan/legacyValidation
* https://github.com/TomaszGolan/genieScripts


