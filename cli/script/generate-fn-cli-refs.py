#!/usr/bin/env python

import argparse
import os
from textwrap import dedent
from string import Template
import subprocess
import sys


class InvalidFnCommand(Exception):
    pass


class FnCliDocWriter:
    """Generates Fn's Cli documentation

    This class takes a list of Fn commands as an input and writes the help
    documentation to an output destination.

    Attributes:
        command_filename: the file containing the list of fn commands that you
            want to obtain documentation for e.g. fn-command-list.txt
        output_dir: the location that you want to write the generated
            documentation to e.g. refs/

    Class varriables:
        FN_COMMAND: the name of the fn command
        doc_template: the template to use when writing the documentation.
    """
    FN_COMMAND = 'fn'

    doc_template = Template(
        dedent('''\
            # `$command`

            ```c
            $$ $command
            $command_output
            ```'''
        )
    )

    def __init__(self, command_filename, output_dir, no_action=False,
                 verbose=0):
        """Initialises FnCliDocWriter"""
        self.command_filename = command_filename
        self.output_dir = output_dir

        self._no_action = no_action

        self._verbose = verbose
        # There is no point running no-action without verbose so set so ensure
        # it is set
        if no_action:
            self._verbose = self._verbose or 1

        self._verbose = verbose or no_action

    def _get_command_list(self):
        """Returns a list of fn commands from the fn command list file"""
        try:
            with open(self.command_filename, 'r') as f:
                return f.read().split("\n")
        except IOError as err:
            sys.exit(err)

    def _run_command(self, command):
        """Returns the help documentation for the specified fn command

        Args:
            command: a list contain the fn command to obtain the help
                documentation for e.g. ["fn", "build"]

        Returns:
            The output of the fn command's help documentation

        Raises:
            InvalidFnCommand: The command provided is not an fn command
        """
        # Safe guard to ensure we only run the fn command
        if command[0] != FnCliDocWriter.FN_COMMAND:
            raise InvalidFnCommand

        # We're only interested in getting the doc
        command.append('--help')

        self._log('Running command: {}'.format(command))

        if self._no_action:
            return ""

        return subprocess.check_output(command)

    def _get_doc_filename(self, command):
        """Get the file name and location for the specified command

        Args:
            command: a list containing the fn command we are obtaining info
                for e.g. ["fn", "build"]

        Returns:
            The filename and location for where we should write the
            documentation
        """
        return self.output_dir + '-'.join(command) + '.md'

    def _write_doc(self, command_string, command_output):
        """Write the help documentation for the command

        Args:
            command_string: the string representation for the command we're
                getting info for e.g. "fn build"
            command_output: the help documentation returned by the command
        """
        command = command_string.split()

        output_file = self._get_doc_filename(command)

        self._log("Writing documentation to: {}".format(output_file))

        if self._no_action:
            return

        try:
            with open(output_file, 'w') as f:
                f.write(
                    self.doc_template.substitute(
                        command=command_string,
                        command_output=command_output
                    )
                )
        except IOError as err:
            sys.exit(err)

    def _log(self, message, log_level=1):
        """Write a log message to stderr if verbose is set"""
        if self._verbose >= log_level:
            sys.stderr.write(message + "\n")

    def generate_doc(self):
        """Generate and write the Fn cli documentation"""
        command_list = self._get_command_list()

        for command_string in command_list:
            self._log("Found command: '{}'".format(command_string))

            command = command_string.split()

            # Protection against blank lines
            if len(command) < 1:
                continue

            try:
                command_output = self._run_command(command)
            except InvalidFnCommand:
                sys.stderr.write(
                    "{} is an invalid Fn command. Skipping...\n".format(
                        command_string
                    )
                )
                continue

            self._write_doc(command_string, command_output)
            self._log('')


if __name__ == '__main__':

    arg_parser = argparse.ArgumentParser(
            'Provided with a list of fn commands, generate help documentation'
            ' and write this to the specified directory')

    arg_parser.add_argument(
            '-c', '--command-list-file', required=True,
            help='The location of a new line seperated file containing the'
            ' list of fn commands you want to generate documentation for e.g.'
            ' fn-command-list.txt'
    )
    arg_parser.add_argument(
            '-o', '--output-dir', required=True,
            help='The location where to write the generated documentation'
            ' files e.g. docs/cli/ref/'
    )
    arg_parser.add_argument(
            '-n', '--no-action', action='store_true',
            help='If set, do not write write any documentation or run any'
            ' shell commands'
    )
    arg_parser.add_argument(
            '-v', '--verbose', default=0, action='count',
            help='Log what the script is doing to stderr')

    args = arg_parser.parse_args()

    if not os.path.isdir(args.output_dir):
        sys.exit(
            "'{}' is not a valid directory. Please provide a valid directory"
            " to '--output-dir'".format(args.output_dir)
        )

    doc_writer = FnCliDocWriter(
            args.command_list_file, args.output_dir, no_action=args.no_action,
            verbose=args.verbose
    )

    doc_writer.generate_doc()
