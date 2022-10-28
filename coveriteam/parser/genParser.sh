#! /bin/bash
# This file is part of CoVeriTeam, a tool for on-demand composition of cooperative verification systems:
# https://gitlab.com/sosy-lab/software/coveriteam
#
# SPDX-FileCopyrightText: 2020 Dirk Beyer <https://www.sosy-lab.org>
#
# SPDX-License-Identifier: Apache-2.0

parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
cd $parent_path

java -cp ../../utils/antlr-4.8-complete.jar org.antlr.v4.Tool -Dlanguage=Python3 -visitor CoVeriLang.g4

# Insert copyright and license header
reuse addheader --template=header.jinja2 --license Apache-2.0 --copyright 'Dirk Beyer <https://www.sosy-lab.org>' ./CoVeriLang*.py