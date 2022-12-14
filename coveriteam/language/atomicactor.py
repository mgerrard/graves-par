# This file is part of CoVeriTeam, a tool for on-demand composition of cooperative verification systems:
# https://gitlab.com/sosy-lab/software/coveriteam
#
# SPDX-FileCopyrightText: 2020 Dirk Beyer <https://www.sosy-lab.org>
#
# SPDX-License-Identifier: Apache-2.0
import signal

from benchexec import tooladapter
from benchexec.model import cmdline_for_run, load_tool_info
from benchexec.runexecutor import RunExecutor
import benchexec.containerexecutor as containerexecutor
from benchexec.test_benchmark_definition import DummyConfig
from coveriteam.language.actor import Actor
from coveriteam.language.actorconfig import ActorConfig
from coveriteam.util import (
    TOOL_OUTPUT_FILE,
    str_dict,
    get_additional_paths_for_container_config,
    get_TOOL_INFO_DOWNLOAD_PATH,
)
import argparse
from pathlib import Path
import os
import uuid
from xml.etree import ElementTree
from coveriteam.language import CoVeriLangException
from benchexec.container import DIR_HIDDEN, DIR_OVERLAY, DIR_READ_ONLY, DIR_FULL_ACCESS
from string import Template
from coveriteam.language.artifact import AtomicActorDefinition
import logging


def get_task_metadata(program_path):
    """
    This function returns the task options to be passed to the tool info module
    to create a command.
    At the moment we only have two kinds of programs: C and Java.
    """
    d = {}
    if isinstance(program_path, str) and Path(program_path).suffix in [".i", ".c"]:
        if not Actor.data_model:
            raise CoVeriLangException(
                "Data model missing. Please provide a data model."
            )
        # TODO Actor is not a nice place to store data model. Think about it.
        d = {"data_model": Actor.data_model, "language": "C"}
    else:
        if Actor.data_model:
            raise CoVeriLangException("Data model is not allowed in Java verification.")
        d = {"language": "Java"}
    return d


class AtomicActor(Actor):
    run_executor: RunExecutor
    force_stop: bool

    def __init__(self, path, version=None):
        self.force_stop = False

        if isinstance(path, AtomicActorDefinition):
            path = path.path
        self.__config = ActorConfig(path, version)

    def name(self):
        return self.__config.actor_name

    def log_dir(self):
        # actor execution id is for the complete execution of an actor -- atomic or composite
        # atomic execution id is for this specific atomic actor.
        return (
            Actor.get_top_actor_execution_dir()
            / self.name()
            / self._atomic_execution_id
        )

    def log_file(self):
        return self.log_dir() / TOOL_OUTPUT_FILE

    def _get_relative_path_to_tool(self, path):
        return os.path.relpath(path, self.__config.tool_dir) if path else ""

    def print_version(self):
        cwd = os.getcwd()
        os.chdir(self.__config.tool_dir)
        self.__set_directory_modes({})

        tool_name = self.__config.tool_name or self.name()
        tool_info, self._tool = load_tool_info(
            tool_name, self.__create_config_for_container_execution()
        )
        tool_locator = tooladapter.CURRENT_BASETOOL.ToolLocator(
            use_path=True, use_current=True
        )
        version = self._tool.version(self._tool.executable(tool_locator))
        print(self._tool.name() + " " + version)
        os.chdir(cwd)

    def act(self, **kwargs):
        # Generate atomic execution id and then call the act method of the super class.
        self._atomic_execution_id = str(uuid.uuid4())
        self.__set_directory_modes(kwargs)
        res = super().act(**kwargs)
        self.gen_xml_elem(kwargs, res)

        return res

    def _act(self, **kwargs):
        # Cancel execution immediately, because stop is called before
        if self.force_stop:
            return  # noqa R502

        args = self._prepare_args(**kwargs)
        d = self._get_arg_substitutions(**kwargs)
        options = [Template(o).safe_substitute(**d) for o in self.__config.options]
        self._run_tool(*args, options)
        try:
            res = self._extract_result()
            self._tool.close()
            return res
        except UnboundLocalError:
            msg = "The execution of the actor {} did not produce the expected result".format(
                self.name()
            )
            msg += "More information can be found in the logfile produced by the tool: {}".format(
                self.log_file()
            )
            raise CoVeriLangException(msg)

    def _run_tool(self, program_path, property_path, additional_options=[], options=[]):
        # Change directory to tool's directory
        cwd = os.getcwd()
        os.chdir(self.__config.tool_dir)

        if program_path:
            identifier = None
            task_options = get_task_metadata(program_path)
            if isinstance(program_path, str):
                program_path = [self._get_relative_path_to_tool(program_path)]
            elif isinstance(program_path, list):
                program_path = [
                    self._get_relative_path_to_tool(p) for p in program_path
                ]
        else:
            identifier = "no-program-file"
            task_options = {}

        property_path = self._get_relative_path_to_tool(property_path)

        tool_name = self.__config.tool_name or self.name()

        tool_info, self._tool = load_tool_info(
            tool_name, self.__create_config_for_container_execution()
        )
        lims_for_exec = {
            "softtimelimit": self.__config.reslim.get("timelimit"),
            "memlimit": self.__config.reslim.get("memlimit"),
        }
        resource_limits = tooladapter.CURRENT_BASETOOL.ResourceLimits(
            self.__config.reslim.get("timelimit"),
            self.__config.reslim.get("timelimit"),
            None,
            self.__config.reslim.get("memlimit"),
            self.__config.reslim.get("cpuCores"),
        )
        tool_locator = tooladapter.CURRENT_BASETOOL.ToolLocator(
            use_path=True, use_current=True
        )
        tool_executable = self._tool.executable(tool_locator)
        # TODO This is bad. It has to change. cmd should not be a part of the actor.
        # But we need it to extract result since PR 592 in benchexec.
        self._cmd = cmdline_for_run(
            self._tool,
            tool_executable,
            options + additional_options,
            program_path,
            identifier,
            property_path,
            task_options,
            resource_limits,
        )

        # Test for stopping the execution of this atomic actor
        self.run_executor = RunExecutor(dir_modes=self._dir_modes)

        def handler(signum, frame):
            logging.debug("caught stop signal")
            self.stop()

        try:
            signal.signal(signal.SIGTERM, handler)
        except ValueError:
            logging.debug("Signal handler in main thread not possible")

        self.measurements = self.run_executor.execute_run(
            self._cmd,
            str(self.log_file().resolve()),
            output_dir=str(self.log_dir().resolve()),
            result_files_patterns=self._result_files_patterns,
            workingDir=self._tool.working_directory(tool_executable),
            environments=self._tool.environment(tool_executable),
            **lims_for_exec,
        )

        terminationreason = self.measurements.get("terminationreason")
        if terminationreason:
            logging.warning(
                "The actor %s was terminated by BenchExec. Termination reason: %s."
                " Possibly it did not produce the expected result."
                % (self.name(), terminationreason)
            )

        # Run executor is cleared, otherwise the old one will be stopped in future runs
        self.run_executor = None

        # Change back to the original directory
        os.chdir(cwd)

    def gen_xml_elem(self, inputs, outputs):
        super().gen_xml_elem(inputs, outputs)
        data = self.get_measurements_data_for_xml()
        self.xml_elem.append(ElementTree.Element("measurements", str_dict(data)))
        tool_output_elem = ElementTree.Element("tool_output")
        tool_output_elem.text = str(Actor._get_relative_path_to_actor(self.log_file()))
        self.xml_elem.append(tool_output_elem)

    def get_measurements_data_for_xml(self):
        data_filter = ["cputime", "walltime", "memory"]
        data = {k: self.measurements[k] for k in data_filter}
        return str_dict(data)

    def __set_directory_modes(self, inputs):
        # The default directory modes taken from container executor.
        self._dir_modes = {
            "/": DIR_READ_ONLY,
            "/run": DIR_HIDDEN,
            "/tmp": DIR_HIDDEN,  # noqa S108
        }
        # Update the default with the /sys and /home as hidden.
        self._dir_modes["/sys"] = DIR_HIDDEN
        self._dir_modes["/home"] = DIR_HIDDEN
        self._dir_modes[self.__config.tool_dir] = DIR_OVERLAY
        self._dir_modes[str(get_TOOL_INFO_DOWNLOAD_PATH())] = DIR_OVERLAY

        for v in inputs.values():
            if isinstance(v.path, str):
                p = str(Path(v.path).parent.resolve())
                self._dir_modes[p] = DIR_OVERLAY
            elif isinstance(v.path, list):
                for path in v.path:
                    p = str(Path(path).parent.resolve())
                    self._dir_modes[p] = DIR_OVERLAY

    def __create_config_for_container_execution(self):
        try:
            if Actor.trust_tool_info:
                return DummyConfig
        except AttributeError:
            # We use the standard container config if the field doesn't exist.
            pass

        parser = argparse.ArgumentParser()
        containerexecutor.add_basic_container_args(parser)
        containerexecutor.add_container_output_args(parser)
        mp = {
            DIR_HIDDEN: "--hidden-dir",
            DIR_OVERLAY: "--overlay-dir",
            DIR_READ_ONLY: "--read-only-dir",
            DIR_FULL_ACCESS: "--full-access-dir",
        }
        args = []
        for p in get_additional_paths_for_container_config():
            args += ["--full-access-dir", p]
        for k, v in self._dir_modes.items():
            args += [mp[v], k]
        config = parser.parse_args(args)
        config.container = True
        return config

    def _get_arg_substitutions(self, **kwargs):
        return {}

    def stop(self):
        logging.debug(f"Shutting down atomic actor: {self.name()}")
        try:
            self.run_executor.stop()
        except AttributeError:
            logging.debug("Couldn't stop, no run executor present")

            # This line will block the next execution
            self.force_stop = True
