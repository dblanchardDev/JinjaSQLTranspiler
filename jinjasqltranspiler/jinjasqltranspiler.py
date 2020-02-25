#! python3
# coding: utf-8
'''Jinja-SQL Transpiler: Automated transpiling of SQL Server code with Jinja templates into pure TSQL.
   Author: David Blanchard - Esri Canada
   Date: February 2020
   Python: 3.8'''

import argparse
import json
import os
import pathlib
from copy import copy

from jinja2 import Environment, FileSystemLoader

OPTION_FILE = "jinjasqltranspiler\\jst.options.json"
OPTION_DEFAULTS = {
	"templates": "templates",
	"transpiled": "transpiled",
	"debug": "debug",
	"ansi_nulls": True,
	"ignore": ["ext", "part"]
}


# UTILITIES #######################################################################################
def get_paths(file_path, workspace_path, out_format):
	'''Derive the template path and output path from a file path'''
	template_path = None
	tpl_dir = get_option("templates", workspace_path)

	# Ensure file is in template folder
	if os.path.commonpath([file_path, tpl_dir]).lower() == tpl_dir.lower():
		template_path = os.path.relpath(file_path, tpl_dir)

	# Otherwise, throw an error
	else:
		msg = "The requested file cannot be found in the templates directory. Either place the file in the templates directory or set the Jinja-SQL Transpiler options to the correct templates directory. >> {}" #pylint: disable=line-too-long
		raise Exception(msg.format(file_path))

	# Determine the destination from the format
	destination = None
	if out_format == "debug":
		destination = get_option("debug", workspace_path)
	else:
		destination = get_option("transpiled", workspace_path)

	# Derive the output path
	out_path = os.path.join(workspace_path, destination, template_path)

	if out_path.endswith(".jinja"):
		out_path = out_path[:-6]

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

		if key == "ignore" and val is not None:
			val = val.split(",")

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
def get_all_options():
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


def get_option(key, workspace=None):
	'''Get a single option value'''
	value = get_all_options()[key]

	if workspace is not None and not os.path.isabs(value):
		value = os.path.join(workspace, value)

	return value


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
		template_path = template_path.replace("\\", "/")
		template = self._jinja.get_template(template_path)

		sql = template.render({
			"out_format": out_format
		})

		# Write the template to file
		pathlib.Path(os.path.dirname(out_path)).mkdir(parents=True, exist_ok=True)
		with open(out_path, "w", encoding="utf-8") as sqlFile:
			sqlFile.write(sql)

		return



def transpile_file(args):
	'''Send a single file for transpiling.'''
	print(" 🗃 Transpiling file")

	template_path, out_path = get_paths(args.file, args.workspace, args.format)

	# Transpile the file
	tpl_folder = get_option("templates", args.workspace)
	transpiler = Transpiler(tpl_folder, get_option("ansi_nulls"))
	transpiler.transpile(template_path, out_path, args.format)

	# Output message
	rel_path = os.path.relpath(out_path, args.workspace)
	print(" ✔ File transpiled to: {}".format(rel_path))

	return



def transpile_project(args):
	'''Send the whole project to be transpiled.'''
	print(" 🗃 Transpiling project")

	ignore = tuple(get_option("ignore"))
	tpl_dir = get_option("templates", args.workspace)

	transpiler = Transpiler(tpl_dir, get_option("ansi_nulls"))

	# Loop through all files in the template directory
	tpl = get_option("templates", args.workspace)

	for (dirpath, dirnames, filenames) in os.walk(tpl): #pylint: disable=unused-variable
		for fn in filenames:
			if not fn.startswith(ignore):
				file_path = os.path.join(dirpath, fn)
				template_path, out_path = get_paths(file_path, args.workspace, args.format)
				transpiler.transpile(template_path, out_path, args.format)

	# Output message
	transpiled = get_option("transpiled", args.workspace)
	rel_path = os.path.relpath(transpiled, args.workspace)
	print(" ✔ Files transpiled to: {}".format(rel_path))
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
	option_parser.add_argument("-i", dest="ignore", help="Filename prefixes to ignore when transpiling project (comma-separated).")

	option_parser.set_defaults(func=set_options)

	# Transpile File
	transpile_file_parser = subparsers.add_parser("transpile_file", help="Transpile a single file")

	transpile_file_parser.add_argument(dest="workspace", help="The project's current workspace.")
	transpile_file_parser.add_argument(dest="file", help="Path to the Jinja template to be transpiled.")
	transpile_file_parser.add_argument(dest="format", help="The format of the transpiled file.", choices=("None", "Create", "Replace/Update", "Debug"))

	transpile_file_parser.set_defaults(func=transpile_file)

	# Transpile Project
	transpile_project_parser = subparsers.add_parser("transpile_project", help="Transpile the whole project")

	transpile_file_parser.add_argument(dest="workspace", help="The project's current workspace.")
	transpile_project_parser.add_argument(dest="format", help="The format of the transpiled file.", choices=("None", "Create", "Replace/Update", "Debug"))

	transpile_project_parser.set_defaults(func=transpile_project)

	# Run parser
	args = parser.parse_args()
	args.func(args)

	print("=======================================")
	return

if __name__ == "__main__":
	main()
