# Jinja-SQL Transpiler
Transpile SQL Server code written using Jinja templates into pure T-SQL code.

Programmability code can also be transpiled into an easy to debug format.

## Prerequisites
[Python 3.x](https://www.python.org/,3.x) and [Jinja2](https://jinja.palletsprojects.com/) must be installed on the machine running Visual Studio Code.

In addition, Jinja-SQL Transpiler will need to know which Python executable to use. The easiest way to do this is to install the [Microsoft Python extension](https://code.visualstudio.com/docs/languages/python) for Visual Studio Code and run the **Python: Select Interpreter** command.

> The alternative to using the Microsoft Python extension is to replace all instances of `${config:python.pythonPath}` in the task file with the path to the Python executable.

## Setup
1. Copy the *jinjasqltranspiler* folder into your project.
2. Copy the *task.json* file into your projects *.vscode* folder. If the folder does not yet exist, create it. If the *task.json* file already exists, you will need to merge the 2 JSON files if you want to keep existing tasks.

## Tasks
All of Jinja-SQL Transpiler's actions can be run via Visual Studio Code's tasks.

1. Open the [Command Palette](https://code.visualstudio.com/docs/editor/tasks#_typescript-hello-world) usually bound `Ctrl+Shift+P`).
2. Search and select the `Tasks: Run Task` option.
3. Select the task you want to run. All Jinja-SQL Transpiler tasks are prefixed with *JST*.

### Set Options
Modify the default input/output folders and other options that affect how files are transpiled.

| Option | Description |
|--------|-------------|
| Templates | Project folder containing all Jinja/SQL Templates to be transpiled.
| Transpiled | Output folder for transpiled SQL Files.
| Debug | Output folder for transpiled SQL debugging Files.
| ANSI Nulls | Whether to explicitly set [ANSI-NULLS](https://docs.microsoft.com/en-us/sql/t-sql/statements/set-ansi-nulls-transact-sql?view=sql-server-ver15) to on for programmability code.

*Paths to folders may be relative from the root of the workspace root.*

### Transpile Current File
Transpile the file that is currently open in Visual Studio Code.