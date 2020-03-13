#! python3
# coding: utf-8
"""Jinja-SQL Transpiler: Transpile SQL Server code written using Jinja templating into pure SQL code.
   Author: David Blanchard - Esri Canada
   Date: February 2020
   Python: 3.8

   Copyright 2020 Esri Canada - All Rights Reserved
   Released under the MIT license. See LICENSE file for details"""

import argparse
import ctypes
import json
import os
import pathlib
import shutil
from copy import copy

from jinja2 import Environment, FileSystemLoader


# JINJA-SQL TRANSPILER CLASS ######################################################################
class JinjaSQLTranspiler():
	"""Transpile SQL Server code written using Jinja templating into pure SQL code.

	Args:
		workspace (str): The absolute path to the VS Code project workspace.
		out_format (str): The format used when transpiling ["Create", "Replace", "None"].

	Constants:
		OPTION_FILE (str): The relative path to option storage file.
		OPTION_DEFAULTS (obj: str): The default values for options, used when no file exists.
	"""

	_workspace_dir = None
	_out_format = None

	_templates_dir = None
	_transpiled_dir = None
	_debug_dir = None
	_ansi_nulls = None
	_quoted_id = None
	_skip_prefixes = None

	_jinja = None


	# CONSTANTS -----------------------------------------------------------------------------------
	OPTION_FILE = "jinjasqltranspiler\\jst.options.json"
	PRESET_FILE = "jinjasqltranspiler\\jst.presets.json"
	OPTION_DEFAULTS = {
		"templates_dir": "templates",
		"transpiled_dir": "transpiled",
		"debug_dir": "debug",
		"ansi_nulls": True,
		"quoted_id": True,
		"skip_prefixes": ["ext", "part"]
	}


	# INSTANTIATION -------------------------------------------------------------------------------
	def __init__(self, workspace, out_format):
		print("======== Jinja-SQL Transpiler =========")

		# Save init parameters
		self._workspace_dir = workspace
		self._out_format = out_format

		# Get & save options
		options = self.get_options()
		self._templates_dir = self._get_abs_path(options["templates_dir"])
		self._transpiled_dir = self._get_abs_path(options["transpiled_dir"])
		self._debug_dir = self._get_abs_path(options["debug_dir"])
		self._ansi_nulls = options["ansi_nulls"]
		self._quoted_id = options["quoted_id"]
		self._skip_prefixes = options["skip_prefixes"]

		# Build Jinja Environment
		self._jinja = Environment(
			loader=FileSystemLoader(self._templates_dir),
			autoescape=False,
			trim_blocks=True,
			lstrip_blocks=True
		)

		# Custom Filters
		self._jinja.filters["columntovalue"] = self._columnToValue

		# return


	# TRANSPILING ---------------------------------------------------------------------------------
	def _transpile(self, template_path, out_path):
		"""Do the actual transpiling of a SQL file with Jinja templates into a pure SQL file.

		Args:
			template_path (str): The path to the template file, relative to the template directory.
			out_path (str): The absolute path to which the transpiled file is to be written.
		"""

		# Create a symbolic link to bring in format templates
		link = os.path.join(self._templates_dir, "jst")
		if self._out_format in ["Create", "Replace", "Debug"]:
			if self._is_admin:
				dirName = self._out_format.lower().replace("/", "_")
				source = os.path.join(self._workspace_dir, "jinjasqltranspiler/formats", dirName)
				os.symlink(source, link, True)
			else:
				raise Exception("\n\n✖ When requesting a format template such as Create, Replace, or Debug, the process must be run as an administrator.\n")

		try:
			# Get and render the template
			template_path = template_path.replace("\\", "/")
			template = self._jinja.get_template(template_path)

			rendered = template.render({
				"out_format": self._out_format,
				"ansi_nulls": self._ansi_nulls,
				"quoted_id": self._quoted_id,
				"presets": self.get_presets(template_path),
			})

			# Write the template to file
			pathlib.Path(os.path.dirname(out_path)).mkdir(parents=True, exist_ok=True)

			with open(out_path, "w", encoding="utf-8") as openFile:
				openFile.write(rendered)

		finally:
			# Remove the symbolic link from format templates
			if os.path.islink(link):
				os.unlink(link)

		return


	def transpile_file(self, file_path):
		"""Process a single file through the transpiler.

		Args:
			file_path (str): The relative (to the workspace) or absolute path to the template file
				to be transpiled. This file must be located in the template directory.
		"""

		# Starting message
		print(" 🗃 Transpiling file")

		# Transpile the file
		template_path, out_path = self._derive_paths(file_path)
		self._transpile(template_path, out_path)

		# Completed message
		rel_path = os.path.relpath(out_path, self._workspace_dir)
		print(" ✔ File transpiled to: {}".format(rel_path))

		return


	def transpile_project(self):
		"""Process the entire project through the transpiler. Will include all files in the
		template directory which do not match a skipped prefix.
		"""

		# Starting message
		print(" 🗃 Transpiling project")

		# Empty the transpiling directory
		for item in os.listdir(self._transpiled_dir):
			path = os.path.join(self._transpiled_dir, item)

			if os.path.isdir(path):
				shutil.rmtree(path)
			else:
				os.remove(path)

		# Loop through all files in the template directory
		for (dirpath, dirnames, filenames) in os.walk(self._templates_dir): #pylint: disable=unused-variable
			for fn in filenames:

				# If file is not to be skipped
				if not fn.startswith(tuple(self._skip_prefixes)):

					# Transpile the file
					file_path = os.path.join(dirpath, fn)
					template_path, out_path = self._derive_paths(file_path)

					self._transpile(template_path, out_path)


		# Completed message
		print(" ✔ Files transpiled to: {}".format(self._transpiled_dir))

		return


	# OPTIONS -------------------------------------------------------------------------------------
	@staticmethod
	def set_options(workspace, templates_dir=None, transpiled_dir=None, debug_dir=None, ansi_nulls=None, quoted_id=None, skip_prefixes=None):
		"""Set the user defined options used by the transpiler.

		Args:
			templates_dir (str, optional): Path† to the directory containing the project's templates.
			transpiled_dir (str, optional): Path† to the directory where transpiled files will be output.
			debug_dir (str, optional): Path† to the directory where debuging files will be output.
			ansi_nulls (bool, optional): Whether to explicitly enable ANSI Nulls in transpiled code.
			quoted_id (bool, optional): Whether to explicitly enable quoted identifiers in transpiled code.
			skip_prefixes (list: str, optional): All file name prefixes which will be skipped when transpiling project.

		† Path can be absolute or relative to the VS Code workspace.
		(Default values defined in DEFAULT_OPTIONS)
		"""

		# Starting message
		print(" ⚙ Setting options")

		# Assemble the options, using defaults if None in arguments
		options = copy(JinjaSQLTranspiler.OPTION_DEFAULTS)

		if templates_dir is not None:
			options["templates_dir"] = templates_dir

		if transpiled_dir is not None:
			options["transpiled_dir"] = transpiled_dir

		if debug_dir is not None:
			options["debug_dir"] = debug_dir

		if ansi_nulls is not None:
			options["ansi_nulls"] = ansi_nulls == "True"

		if quoted_id is not None:
			options["quoted_id"] = quoted_id == "True"

		if skip_prefixes is not None:
			options["skip_prefixes"] = skip_prefixes.split(",")

		# Write to file
		options_json = json.dumps(options)
		options_path = os.path.join(workspace, JinjaSQLTranspiler.OPTION_FILE)
		with open(options_path, "w", encoding="utf-8") as optFile:
			optFile.write(options_json)

		# Completed Message
		print(" ✔ Options have been saved")

		return


	def get_options(self):
		"""Get the transpiler options, using defaults is no user defined options are set.

		Returns:
			(obj): {
				templates_dir (str): Path† to the directory containing the project's templates,
				transpiled_dir (str): Path† to the directory where transpiled files will be output,
				debug_dir (str): Path† to the directory where debuging files will be output,
				ansi_nulls (bool): Whether to explicitly enable ANSI Nulls in transpiled code,
				quoted_id (bool): Whether to explicitly enable quoted identifiers in transpiled code,
				skip_prefixes (list: str): All file name prefixes which will be skipped when transpiling project,
			}

		† Path may be absolute or relative to VS Code workspace.
		"""
		options = None

		# If a file exists, use those
		options_path = os.path.join(self._workspace_dir, self.OPTION_FILE)
		if os.path.isfile(options_path):
			with open(self.OPTION_FILE, "r", encoding="utf-8") as optFile:
				options = json.loads(optFile.read())

		# Otherwise, use defaults
		else:
			options = self.OPTION_DEFAULTS

		return options


	# PARAMETER PRESETS ---------------------------------------------------------------------------
	@staticmethod
	def create_parameter_presets(workspace):
		"""Create the parameters presets JSON file and populate it with an example.

		Args:
			workspace (str): The absolute path to the VS Code project workspace.
		"""
		presets_path = os.path.join(workspace, JinjaSQLTranspiler.PRESET_FILE)

		if not os.path.exists(presets_path):
			# Create a sample
			preset_json = json.dumps({
				"path_relative_to_templates/use_forward_slashes/example.sql.jinja": {
					"@stringParameter": "preset value",
					"@dateParameter": "2020-01-01T00:00:00",
					"@numberParameter": 123,
					"@nullParameter": None,
				}
			}, indent="\t")

			# Create the file
			with open(JinjaSQLTranspiler.PRESET_FILE, "w", encoding="utf-8") as presetFile:
				presetFile.write(preset_json)

		# Provide path in output
		print(" ⚙  Parameter presets file: {}".format(JinjaSQLTranspiler.PRESET_FILE))

		return


	def get_presets(self, template_path):
		"""Get the parameter presets for a template, returning None if not found.

		Args:
			template_path (str)†: The path to the template file, relative to the template directory.

		Returns:
			(obj): As defined in the jst.presets.json file for that template.

		† Path may be absolute or relative to VS Code workspace.
		"""

		# Make template path relative to templates
		if os.path.isabs(template_path):
			template_path = os.path.relpath(template_path, self._templates_dir)

		template_path = template_path.replace("\\", "/")

		# Fetch the parameter presets if available
		presets = None
		presets_path = os.path.join(self._workspace_dir, self.PRESET_FILE)

		if os.path.isfile(presets_path):
			presetData = None
			with open(self.PRESET_FILE, "r", encoding="utf-8") as presetFile:
				presetData = json.loads(presetFile.read())

			presets = presetData.get(template_path)

		return presets


	# UTILITIES -----------------------------------------------------------------------------------
	def _get_abs_path(self, path):
		"""Return the absolute path, using the VS Code workspace as the root.

		Args:
			path (str): The path to be made absolute (if already absolute, returned unchanged).

		Returns:
			(str): The absolute path derived from the relative path.
		"""

		resolved = None

		if not os.path.isabs(path):
			resolved = os.path.join(self._workspace_dir, path)

		else:
			resolved = path

		return resolved


	def _derive_paths(self, file_path):
		"""Derive the template path and output path from a file path.

		Args:
			file_path (str): The relative (to the workspace) path to the template file
				to be transpiled. This file must be located in the template directory.

		Returns:
			(str): The relative path to the template from the templates directory.
			(str): The absolute path to which the transpiled file is to be written.
		"""
		template_path = None

		# Ensure file is in template folder
		common = os.path.commonpath([file_path, self._templates_dir])
		if common.lower() == self._templates_dir.lower():

			# Get relative path to file starting at templates directory
			template_path = os.path.relpath(file_path, self._templates_dir)


		# Otherwise, throw an error
		else:
			raise Exception("\n\n✖ The file could not be found in the templates directory: {}\n".format(file_path))


		# Determine the destination directory
		destination = None
		if self._out_format == "Debug":
			destination = self._debug_dir

		else:
			destination = self._transpiled_dir

		# Derive the output path
		out_path = os.path.join(self._workspace_dir, destination, template_path)

		if out_path.endswith(".jinja"):
			out_path = out_path[:-6]

		return template_path, out_path


	@property
	def _is_admin(self):
		"""Whether the process is being run as an administrator."""
		is_admin = None

		try:
			is_admin = os.getuid() == 0
		except AttributeError:
			is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0

		return is_admin


	def _columnToValue(self, definition, presets=None):
		"""Return a value that is suitable for the defined column.

		Args:
			definition (string): The column definition from the SQL code.
			presets (JSON string): Object containing an preset value for the columns.

		Returns:
			(str): Value that fits the SQL insert requirements for that column.
			       Will use preset values if available.
		"""

		value = None

		# Check for availability in presets
		paramName = definition.strip().split(" ")[0]
		if presets is not None and paramName in presets:
			raw_value = presets[paramName]

			if type(raw_value) == str:
				value = "'{}'".format(raw_value)

			elif type(raw_value) in [int, float]:
				value = str(raw_value)

			elif type(raw_value) == bool:
				value = "1" if raw_value else "0"

			else:
				value = "NULL"

		# Otherwise, use default if available
		elif "=" in definition:
			value = definition.split("=")[1].strip()

			if value.endswith(","):
				value = value[:-1].strip()

		# Otherwise, use placeholder values
		else:
			definition = definition.lower()

			value = "NULL"

			# Numeric
			if "bingint" in definition:
				value = "6223372036854775807"
			elif "smallint" in definition:
				value = "2515"
			elif "tinyint" in definition:
				value = "12"
			elif "int" in definition:
				value = "845655"

			elif "bit" in definition:
				value = "1"

			elif "smallmoney" in definition:
				value = "5.12"
			elif "money" in definition:
				value = "158.25"

			elif "decimal" in definition:
				value = "1.23434"
			elif "numeric" in definition:
				value = "1.2344"
			elif "float" in definition:
				value = "9.33432"
			elif "real" in definition:
				value = "9.33432"

			# Date/Time
			elif "smalldatetime" in definition:
				value = "'2020-01-01 11:45'"
			elif "datetime" in definition:
				value = "'2020-01-01 11:45:54'"

			# Text
			elif "nvarchar" in definition:
				value = "N'A'"
			elif "varchar" in definition:
				value = "'A'"
			elif "nchar" in definition:
				value = "N'X'"
			elif "char" in definition:
				value = "'X'"
			elif "ntext" in definition:
				value = "N'B'"
			elif "text" in definition:
				value = "'B'"

			# Others
			elif "varbinary" in definition:
				length = definition.split("(")[1].split(")")[0]
				value = "123456 AS VARBINARY({})".format(length)

			elif "binary" in definition:
				length = definition.split("(")[1].split(")")[0]
				value = "123456 AS BINARY({})".format(length)

			elif "geometry" in definition:
				value = "GEOMETRY::STPointFromText('POINT (100 100)', 0)"

			elif "geography" in definition:
				value = "GEOGRAPHY::STGeomFromText('LINESTRING(-122.360 47.656, -122.343 47.656)', 4326)"

		return value


# MAIN / ARGUMENTS ################################################################################
def _parse_arguments():
	"""Parse the arguments according to the requested command.

	Returns:
		(namespace): Parsed arguments namespace.
	"""

	parser = argparse.ArgumentParser()
	subparsers = parser.add_subparsers(help="commands", dest="command")

	# Command: Set Options
	option_parser = subparsers.add_parser("set_options", help="Set the user defined options used by the transpiler.")
	nulls_help = "Whether to explicitly enable ANSI Nulls in transpiled code."
	quoted_help = "Whether to explicitly enable QUOTED IDENTEFIERS in transpiled code."

	option_parser.add_argument(dest="workspace", help="The absolute path to the VS Code project workspace.")
	option_parser.add_argument("-t", dest="templates_dir", help="Path to the directory containing the project's templates.")
	option_parser.add_argument("-p", dest="transpiled_dir", help="Path to the directory where transpiled files will be output.")
	option_parser.add_argument("-d", dest="debug_dir", help="Path to the directory where debuging files will be output.")
	option_parser.add_argument("-n", dest="ansi_nulls", help=nulls_help, choices=("True", "False"))
	option_parser.add_argument("-q", dest="quoted_id", help=quoted_help, choices=("True", "False"))
	option_parser.add_argument("-s", dest="skip_prefixes", help=" All file name prefixes which will be skipped when transpiling project.")

	# Command: Transpile File
	transpile_file_parser = subparsers.add_parser("transpile_file", help="Process a single file through the transpiler.")

	transpile_file_parser.add_argument(dest="workspace", help="The absolute path to the VS Code project workspace.")
	transpile_file_parser.add_argument(dest="file_path", help="The path to the template file to be transpiled.")
	transpile_file_parser.add_argument(dest="out_format", help="The format used when transpiling.", choices=("None", "Create", "Replace", "Debug"))

	# Command: Transpile Project
	transpile_project_parser = subparsers.add_parser("transpile_project", help="Process the entire project through the transpiler.")

	transpile_project_parser.add_argument(dest="workspace", help="The absolute path to the VS Code project workspace.")
	transpile_project_parser.add_argument(dest="out_format", help="The format used when transpiling.", choices=("None", "Create", "Replace", "Debug"))

	# Command: Parameter Presets
	parameter_presets_parser = subparsers.add_parser("parameter_presets", help="Create a parameters preset file.")
	parameter_presets_parser.add_argument(dest="workspace", help="The absolute path to the VS Code project workspace.")

	# Run parser
	return parser.parse_args()


def _main():
	"""Get the parsed arguments, instantiate the transpiler and perform the requested action."""

	# Get the parsed arguments
	args = _parse_arguments()

	# Call function and instantiate the transpiler if required
	command = args.command
	delattr(args, "command")

	if command == "set_options":
		JinjaSQLTranspiler.set_options(**vars(args))

	elif command == "parameter_presets":
		JinjaSQLTranspiler.create_parameter_presets(**vars(args))

	else:
		jst = JinjaSQLTranspiler(args.workspace, args.out_format)
		delattr(args, "workspace")
		delattr(args, "out_format")

		if command == "transpile_file":
			jst.transpile_file(**vars(args))

		elif command == "transpile_project":
			jst.transpile_project()

		else:
			raise Exception("The command '{}' is not recognized.".format(command))

	return


if __name__ == "__main__":
	_main()
