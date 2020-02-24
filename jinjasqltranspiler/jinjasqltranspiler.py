#! python3
# coding: utf-8
'''Jinja-SQL Transpiler: Automated transpiling of SQL Server code with Jinja templates into pure TSQL.
   Author: David Blanchard - Esri Canada
   Date: February 2020
   Python: 3.8'''

import argparse
import json
from copy import copy
import os

from jinja2 import Environment, FileSystemLoader

OPTION_FILE = "jinjasqltranspiler\\jst.options.json"
OPTION_DEFAULTS = {
	"templates": "templates",
	"transpiled": "transpiled",
	"debug": "debug",
	"ansi_nulls": True,
}


# UTILITIES #######################################################################################
def get_paths(file_path, workspace_path, out_format):
	'''Derive the template path and output path from a file path'''
	template_path = None
	tpl_dir = get_abs_path("templates", workspace_path)

	# Determine the destination from the format
	destination = None
	if out_format == "debug":
		destination = get_abs_path("debug", workspace_path)
	else:
		destination = get_abs_path("transpiled", workspace_path)

	# Ensure file is in template folder
	if os.path.commonpath([file_path, tpl_dir]).lower() == tpl_dir.lower():
		template_path = os.path.relpath(file_path, tpl_dir)

	# Otherwise, throw an error
	else:
		msg = "The requested file cannot be found in the templates directory. Either place the file in the templates directory or set the Jinja-SQL Transpiler options to the correct templates directory. >> {}" #pylint: disable=line-too-long
		raise Exception(msg.format(file_path))

	out_path = os.path.join(workspace_path, destination, template_path)

	return template_path, out_path



# OPTIONS HANDLERS ################################################################################
def set_options(args):
	'''Set the transpiler options, writing them to file.'''
	print(" ⚙ Setting options")

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
	print(" ✔ Options have been saved")

	return


_optionCache = None
def get_options():
	'''Get the transpiler options, using defaults if no file.'''
	options = None

	# If already cached
	if _optionCache is not None:
		options = _optionCache

	# If a file exists, use those
	elif os.path.isfile(OPTION_FILE):
		with open(OPTION_FILE, "r", encoding="utf-8") as optFile:
			options = json.loads(optFile.read())

	# Otherwise, use defaults
	else:
		options = OPTION_DEFAULTS

	return options


def get_abs_path(key, workspace):
	'''Return the absolute path from an option key.'''
	path = None
	base = get_options()[key]

	if os.path.isabs(base):
		path = base

	else:
		path = os.path.join(workspace, base)

	return path


# TRANSPILING #####################################################################################
class Transpiler():
	'''Transpile files from SQL-Jinja templates to a final TSQL version.'''

	_jinja = None

	def __init__(self, template_dir, ansi_nulls=True):

		# Build Jinja Environment
		self._jinja = Environment(
			loader=FileSystemLoader(template_dir),
			autoescape=False,
			trim_blocks=True,
			lstrip_blocks=True
		)

		# Custom Jinja Globals
		self._jinja.globals["ansi_nulls"] = ansi_nulls

		return



	def transpile(self, template_path, out_path, out_format="CREATE"):
		'''Transpile a single SQL/Jinja file into a TSQL file'''

		# Render the template
		template = self._jinja.get_template(template_path)
		sql = template.render({
			"out_format": out_format
		})

		# Write the template to file
		with open(out_path, "w", encoding="utf-8") as sqlFile:
			sqlFile.write(sql)

		return



def transpile_file(args):
	'''Send a single file for transpiling.'''
	print(" 🗃 Transpiling file")

	options = get_options()

	template_path, out_path = get_paths(args.file, args.workspace, args.format)

	# Transpile the file
	transpiler = Transpiler(options["templates"], options["ansi_nulls"])
	transpiler.transpile(template_path, out_path, args.format)

	# Output message
	rel_path = os.path.relpath(out_path, args.workspace)
	print(" ✔ File transpiled to: {}".format(rel_path))

	return


# MAIN / ARGUMENTS ################################################################################
def main():
	'''Parse arguments and call the corresponding function.'''

	print("======== Jinja-SQL Transpiler =========")
	parser = argparse.ArgumentParser()
	subparsers = parser.add_subparsers(help="commands")

	# Set Options
	option_parser = subparsers.add_parser("options", help="Setup transpile options")
	nulls_help = "Whether to explicitly set ANSI-NULLS to on for programmability code."

	option_parser.add_argument("-t", dest="templates", help="Project folder containing all Jinja/SQL Templates.")
	option_parser.add_argument("-p", dest="transpiled", help="Output folder for transpiled SQL Files.")
	option_parser.add_argument("-d", dest="debug", help="Output folder for transpiled SQL debugging Files.")
	option_parser.add_argument("-n", dest="ansi_nulls", help=nulls_help, choices=("True", "False"))

	option_parser.set_defaults(func=set_options)

	# Transpile File
	transpile_file_parser = subparsers.add_parser("transpile_file", help="Transpile a single file")

	transpile_file_parser.add_argument(dest="file", help="Path to the Jinja template to be transpiled.")
	transpile_file_parser.add_argument(dest="format", help="The format of the transpiled file.", choices=("None", "Create", "Replace/Update", "Debug"))
	transpile_file_parser.add_argument("-w", dest="workspace", help="The current project's workspace, used for relative paths.")

	transpile_file_parser.set_defaults(func=transpile_file)

	# Run parser
	args = parser.parse_args()
	args.func(args)

	print("=======================================")
	return

if __name__ == "__main__":
	main()
