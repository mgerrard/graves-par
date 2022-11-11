This tool Graves-Parallel has been created using CoVeriTeam: https://gitlab.com/sosy-lab/software/coveriteam
It is essentially CoVeriTeam packaged with several other tools in the "cache/tools/" directory.
The file README.md contains more information about CoVeriTeam, including licencing information about CoVeriTeam.

Licenses and Copyrights:
The license and copyrights are separate for 1) CoVeriTeam, and 2) the packaged tools.
1) CoVeriTeam is licensed under the Apache 2.0 License, copyright Dirk Beyer.
   This directory contains some files (other than in the "cache/" directory)
   that are part of CoVeriTeam and are available under several other free licenses (cf. directory LICENSES).
2) Each packaged tool is packaged in its own directory under "cache/tools/".
   The license and copyright information for each of these tools is available in their respective directories.
   
   All but one of these tools are taken from the tool archives submitted to the sv-comp by the tool developers,
   hence these tools comply with the license requirements of sv-comp.
   
   The remaining tool cst_transform (https://github.com/cedricrupb/cst_transform) is
   packaged under "cache/tools/cst_transform-https-syncandshare.lrz.de-dl-fiPJhz6P526GDcYNyF4MpyD5" (TO CHANGE),
   and also complies with the sv-comp license requirements.

Dependencies:
  - clang-11
  - libclang-11-dev

Usage:

  ./graves.sh \<C_FILE\> \<SPEC\> {ILP32,LP64}
