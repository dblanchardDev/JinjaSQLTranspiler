#! python3
# coding: utf-8
'''Jinja-SQL Transpiler: Automated transpiling of SQL Server code with Jinja templates into pure TSQL.
   Author: David Blanchard - Esri Canada
   Date: February 2020
   Python: 3.8'''

import argparse
import json
from copy import copy
from os import path

OPTION_FILE = "jinjasqltranspiler\\jst.options.json"
OPTION_DEFAULTS = {
	"templates": "templates",
	"transpiled": "transpiled",
	"debug": "debug",
	"ansi_nulls": True,
}


# OPTIONS HANDLERS ################################################################################
def set_options(args):
	'''Set the transpiler options, writing them to file.'''

	# Assemble the options, using defaults if None in arguments
	options = copy(OPTION_DEFAULTS)
	userDefined = vars(args)

	for key in OPTION_DEFAULTS.keys():
		val = userDefined[key]

		if key == "ansi_nulls":
			val = (val == "True")

		if val is not None:
			options[key] = val

	options_json = json.dumps(options)

	# Write to file
	with open(OPTION_FILE, "w", encoding="utf-8") as optFile:
		optFile.write(options_json)

	# Output
	print("Options have been saved.")

	return


def get_options():
	'''Get the transpiler options, using defaults if no file.'''
	options = None

	# If a file exists, use those
	if path.isfile(OPTION_FILE):
		with open(OPTION_FILE, "r", encoding="utf-8") as optFile:
			options = json.loads(optFile.read())

	# Otherwise, use defaults
	else:
		options = OPTION_DEFAULTS

	return options


# MAIN / ARGUMENTS ################################################################################
def main():
	'''Parse arguments and call the corresponding function.'''
	parser = argparse.ArgumentParser()
	subparsers = parser.add_subparsers(help="commands")

	# Set Options
	option_parser = subparsers.add_parser("options", help="Setup transpile options")
	option_parser.add_argument("-t", dest="templates", help="Project folder containing all Jinja/SQL Templates.", default="templates")
	option_parser.add_argument("-p", dest="transpiled", help="Output folder for transpiled SQL Files.", default="transpiled")
	option_parser.add_argument("-d", dest="debug", help="Output folder for transpiled SQL debugging Files.", default="debug")
	nulls_help = "Whether to explicitly set ANSI-NULLS to on for programmability code."
	option_parser.add_argument("-n", dest="ansi_nulls", help=nulls_help, choices=("True", "False"), default="True")
	option_parser.set_defaults(func=set_options)

	# Run parser
	args = parser.parse_args()
	args.func(args)

	return

if __name__ == "__main__":
	main()
