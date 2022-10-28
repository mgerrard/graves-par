# This file is part of CoVeriTeam, a tool for on-demand composition of cooperative verification systems:
# https://gitlab.com/sosy-lab/software/coveriteam
#
# SPDX-FileCopyrightText: 2020 Dirk Beyer <https://www.sosy-lab.org>
#
# SPDX-License-Identifier: Apache-2.0


To install or upgrade Python libraries, run the following command in the CoVeriTeam directory:

pip3 wheel --wheel-dir lib -r lib/requirements.txt

This upgrades all dependencies to the newest available version.

To add new dependencies, add them to requirements.txt
in the style of a requirements.txt file for pip
(https://pip.readthedocs.org/en/stable/user_guide/#requirements-files).

The license and copyright of each Python library must be declared
in a .license file next to it.
Typically, this information can be extracted from the metadata
in the library archive.
Afterwards, run reuse download --all and add any new files under LICENSES
such that all license texts are checked in.

Do not forget to check in all files under this directory.
We currently distribute these libraries in the repository
because downloading them requires "pip3", which many users do not have installed.

