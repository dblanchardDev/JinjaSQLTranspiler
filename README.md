# Jinja-SQL Transpiler
Transpile SQL Server code written using Jinja templating into pure SQL code within Visual Studio Code.

Most code can also be transpiled into an easy to debug format for SQL Server.

## Prerequisites
[Python 3.x](https://www.python.org/,3.x) and [Jinja2](https://jinja.palletsprojects.com/) must be installed on the machine running Visual Studio Code.

In addition, Jinja-SQL Transpiler will need to know which Python executable to use. The easiest way to do this is to install the [Microsoft Python extension](https://code.visualstudio.com/docs/languages/python) for Visual Studio Code and run the **Python: Select Interpreter** command.

> The alternative to using the Microsoft Python extension is to replace all instances of `${config:python.pythonPath}` in the task file with the path to the Python executable.

---

## Setup
1. Copy the *jinjasqltranspiler* folder into your project.
2. Copy the *task.json* file into your project's *.vscode* folder. If the folder does not exist, create it. If the *task.json* file already exists, you will need to merge the 2 JSON files if you want to keep existing tasks.

---

## Tasks
All of Jinja-SQL Transpiler's actions can be run via Visual Studio Code's tasks.

1. Open the [Command Palette](https://code.visualstudio.com/docs/editor/tasks#_typescript-hello-world) (usually bound to `Ctrl+Shift+P`).
2. Search and select the `Tasks: Run Task` option.
3. Select the task you want to run. All Jinja-SQL Transpiler tasks are prefixed with *JST*.

### Set Options
Set the user defined options used by the transpiler. If none are specified, will use defaults.

| Option | Description | Default |
|--------|-------------|---------|
| Templates | Path† to the directory containing the project's templates. | `templates`
| Transpiled | Path† to the directory where transpiled files will be output. | `transpiled`
| Debug | Path† to the directory where debugging files will be output. | `debug`
| ANSI Nulls | Whether to explicitly enable [ANSI-NULLS](https://docs.microsoft.com/en-us/sql/t-sql/statements/set-ansi-nulls-transact-sql?view=sql-server-ver15) in programmability code. | `True`
| Ignore | All file name prefixes which will be skipped when transpiling project (comma-separated list). | `part,ext`

† *Paths to folders may be relative from the root of the workspace root.*

### Transpile Current File
Transpile the file that is currently open in Visual Studio Code.

See [Format Templates](#format-templates) below for details on the options.

### Debug Current File
Transpile the file that is currently open in Visual Studio Code into an easily debuggable format.

### Transpile Project
Transpile all files found in the *templates* folder, only skipping those that are prefixed with a value from the *skipped prefixes* option (see [above](#set-options)).

Therefore, all files except those marked to be skipped must be Jinja templates.

See [Format Templates](#format-templates) below for details on the options.

---

## Format Templates
_**Not yet implemented**_

| Format | Description |
|--------|-------------|
| Create | … |
| Replace/Update | … |
| None | … |

---

## Use Outside Visual Studio Code
The `jinjasqltranspiler.py` file can be used separately from Visual Studio code, only requiring Jinja2 to be installed in the Python environment.

Details on the arguments and commands can be obtained via command line help as follows:

```
> python jinjasqltranspiler.py -h
```