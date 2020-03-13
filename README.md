# Jinja-SQL Transpiler
Transpile SQL Server code written using Jinja templating into pure SQL code within Visual Studio Code.

Most code can also be transpiled into an easy to debug format for SQL Server.

## Prerequisites
[Python 3.x](https://www.python.org/,3.x) and [Jinja2](https://jinja.palletsprojects.com/) must be installed on the machine running Visual Studio Code.

In addition, Jinja-SQL Transpiler will need to know which Python executable to use. The easiest way to do this is to install the [Microsoft Python extension](https://code.visualstudio.com/docs/languages/python) for Visual Studio Code and run the **Python: Select Interpreter** command.

> The alternative to using the Microsoft Python extension is to replace all instances of `${config:python.pythonPath}` in the task file with the path to the Python executable.

## Setup
1. Copy the *jinjasqltranspiler* folder into your project.
2. Copy the *task.json* file into your project's *.vscode* folder. If the folder does not exist, create it. If the *task.json* file already exists, you will need to merge the 2 JSON files if you want to keep existing tasks.
3. Copy the *JinjaSQLTranspiler.code-snippets* file into your project's *.vscode* folder.

---

## Tasks
All of Jinja-SQL Transpiler's actions can be run via Visual Studio Code's tasks.

1. Open the [Command Palette](https://code.visualstudio.com/docs/editor/tasks#_typescript-hello-world) (usually bound to `Ctrl+Shift+P`).
2. Search and select the `Tasks: Run Task` option.
3. Select the task you want to run. All Jinja-SQL Transpiler tasks are prefixed with *JST*.

### Set Options
Set the user defined options used by the transpiler. If none are specified, will use defaults.

| Option                | Default       | Description
|-----------------------|---------------|-------------
| Templates Directory   | `templates`   | Path† to the directory containing the project's templates.
| Transpiled Directory  | `transpiled`  | Path† to the directory where transpiled files will be output.
| Debug Directory       | `debug`       | Path† to the directory where debugging files will be output.
| ANSI Nulls            | `True`        | Whether to explicitly enable [ANSI-NULLS](https://docs.microsoft.com/en-us/sql/t-sql/statements/set-ansi-nulls-transact-sql?view=sql-server-ver15) in transpiled code.
| Quoted Identifier     | `True`        | Whether to explicitly enable [Quoted Identifiers](https://docs.microsoft.com/en-us/sql/t-sql/statements/set-quoted-identifier-transact-sql?view=sql-server-ver15) in transpiled code.
| Skip Prefixes         | `part,ext`    | All file name prefixes which will be skipped when transpiling project (comma-separated list).

† *Paths to folders may be relative from the root of the workspace root.*

### Transpile Current File
Transpile the file that is currently open in Visual Studio Code.

If a [Format Templates](#format-templates) was used, choose *Create* or *Replace* as the format. Otherwise, choose *None*.

### Debug Current File
Transpile the file that is currently open in Visual Studio Code into an easily debuggable structure. This task will only work on files that use a [Format Templates](#format-templates).

Function/procedure parameters will use placeholder values by default. These may be overidden by [parameter presets](#parameter-presets).

### Transpile Project
Transpile all files found in the *templates* folder, only skipping those that are prefixed with a value from the *skip prefixes* option (see [above](#set-options)).

If a [Format Templates](#format-templates) was used, choose *Create* or *Replace* as the format. Otherwise, choose *None*.

### Parameter Presets
When debugging, function/procedure parameters and table rows will be populated by placeholder values. These placeholder values can be replaced with preset values to allow for proper testing of the script.

Running this task will create a presets file if it doesn't already exist and will provide a link to the file in the terminal. Populate this file with the desired preset values for any function, procedure, or table.

#### Example
For a template file located in `<workspace>/templates/Procedures/MySP.jinja.sql`, you would add an entry to the presets file as follows:
```json
{
	…
	"Procedures/MySP.jinja.sql": {
		"@stringParam": "my value",
		"@dateParam": "2020-01-01 12:30:00",
		"@numberParam": 1234,
		"@nullParam": null
	}
}
```

Notes:
 * The path is relative to the *templates* folder and must use forward-slashes (`/`).
 * Any parameter/column that isn't defined will continue using placeholder value.

---

## Format Templates
Format templates are provided for most SQL item types as part of the Jinja-SQL Transpiler. When used, these modify the code in order to provide various output files.

The following output modes are available:

| Format   | Description
|----------|-------------
| Create   | Create the item. Will fail if the item already exists.
| Replace  | Replace or alter an existing item.
| Debug    | Modifies the code to allow for immediate execution and interactive debugging.
| None     | Does not use a format template.

Details on using the format templates in your Jinja templates can be found in: [Using Format Templates](UsingFormatTemplates.md).

---

## Snippets
The following Visual Studio Code [snippets](https://code.visualstudio.com/docs/editor/userdefinedsnippets) to scaffold Format Templates and provide quick access to common Jinja template blocks are provided:

### Format Templates
| Key               | Description
|-------------------|-------------
| jst-mssql-table   | SQL Server Table
| jst-mssql-view    | SQL Server View
| jst-mssql-sp      | SQL Server Stored Procedure
| jst-mssql-tvf     | SQL Server Table-valued Function
| jst-mssql-scalar  | SQL Server Scalar Function
| jst-mssql-trigger | SQL Server Trigger

### Jinja Template Blocks
| Key      | Block
|----------|-------
| jblock   | block
| jif      | if
| jelse    | if-else
| jelif    | if-elif-else
| jextend  | extend
| jfor     | for loop
| jfunc    | function
| jvar     | variable
| jset     | set
| jinclude | include

---

## Use Outside Visual Studio Code
The `jinjasqltranspiler.py` file can be used separately from Visual Studio code, only requiring Jinja2 to be installed in the Python environment.

Details on the arguments and commands can be obtained via command line help as follows:

```
> python jinjasqltranspiler.py -h
```

---

## Licensing

Copyright 2020 Esri Canada - All Rights Reserved

A copy of the license is available in the repository's [LICENSE](../master/LICENSE) file.

## Support

This code is distributed as is and is not supported in any way by Esri Canada, Esri Inc. or any other Esri distributor.

## Contributing

See our [contributing guidelines](CONTRIBUTING.md).
