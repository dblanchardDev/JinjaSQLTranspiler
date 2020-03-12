# Using Format Templates
*[Return to the main Jinja-SQL Transpiler documentation.](README.md)*

Using a format template when writing the code for a database item allows for easy transition between various types of versions of the transpiled output: creation, replacing/altering, and debugging.

## Extending a Format Template
In order for the Jinja-SQL Transpiler to know what format template to use, add an [extend](https://jinja.palletsprojects.com/en/2.11.x/templates/#child-template) statement to the top of your file.

The statement is written as
```jinja
{% extends "jst/<db_key>/<item_key>.sql.jinja %}
```
where `<db_key>` is replaced with a key for the [Database Engine](#database-engines) and `<item_key>` is replaced with a key for a [Database Item](#database-items).

For example, when creating a table in Microsoft SQL Server, use

## Adding Code Blocks
In order to modify the code from one format to another, the Jinja-SQL Transpiler must be able to find the relevant parts of the code. This is accomplished by surrounding relevant code with  [Jinja Blocks](https://jinja.palletsprojects.com/en/2.11.x/templates/#base-template).

For example, when creating a table, the transpiler needs to know the **name** and the **columns**:
```sql
CREATE TABLE {% block name %} my_schema.Vehicles {% endblock %} (
	{% block columns %}
	Vehicle_ID AS INT,
	Vehicle_Name AS VARCHAR(50),
	License_Plate AS VARCHAR(20)
	{% endblock %}
);
```

---

## Database Engines
Each database engine may vary slightly in how they require items to be defined.

> If your database engine is not available, you may [define your own format templates](#writing-new-format-templates).

| Database Engine            | Key     |
|----------------------------|---------|
| Microsoft SQL Server 2012+ | `mssql` |

## Database Items
The database items for which the format templates are available may vary depending on the database engine.

| Item                    | Key          | MSSQL |
|-------------------------|--------------|-------|
| Tables                  | `table`      | ✔     |
| Views                   | `view`       | ✔     |
| Stored Procedures       | `procedure`  | ✔     |
| Table-valued Functions  | `tvf`        | ✔     |
| Scalar Functions        | `scalar`     | ✔     |
| Triggers                | `trigger`    | ✔†    |

† *Only available for after triggers.*

> The templates do not always support more advanced definition parameters may therefore require modification.

### Available Code Blocks
The following code blocks are available for each of the above listed items.

#### Tables
| Block             | MSSQL    | Description
|-------------------|----------|-------------
| `comments`        | Optional | Comments to be placed at the top of the file.
| `name`            | Required | The table's name (and schema).
| `columns`         | Required | The comma-separated list of column definitions.

#### Views
| Block             | MSSQL    | Description
|-------------------|----------|-------------
| `comments`        | Optional | Comments to be placed at the top of the file.
| `name`            | Required | The view's name (and schema).
| `select`          | Required | The select statement which creates the view.

#### Stored Procedures
| Block             | MSSQL    | Description
|-------------------|----------|-------------
| `comments`        | Optional | Comments to be placed at the top of the file.
| `name`            | Required | The procedure's name (and schema).
| `parameters`      | Optional | The comma-separated list of input parameters.
| `logic`           | Required | The body of the stored procedure.

#### Table-valued Functions
| Block             | MSSQL    | Description
|-------------------|----------|-------------
| `comments`        | Optional | Comments to be placed at the top of the file.
| `name`            | Required | The function's name (and schema).
| `parameters`      | Optional | The comma-separated list of input parameters.
| `data_type`		| Optional | The data-type definition (defaults to `TABLE`).
| `logic`           | Required | The statements which returns the table.

#### Scalar Functions
| Block             | MSSQL    | Description
|-------------------|----------|-------------
| `comments`        | Optional | Comments to be placed at the top of the file.
| `name`            | Required | The function's name (and schema).
| `parameters`      | Optional | The comma-separated list of input parameters.
| `data_type`       | Required | The data-type that is returned.
| `parameters`      | Optional | The comma-separated list of input parameters.
| `logic`           | Required | The body of the function. The last nine should contain the `RETURN` statement.


#### Triggers
| Block             | MSSQL    | Description
|-------------------|----------|-------------
| `comments`        | Optional | Comments to be placed at the top of the file.
| `name`            | Required | The trigger's name (and schema).
| `table`           | Required | The table (and schema) on which the trigger will fire.
| `activated`       | Required | The comma-separated list of actions on which the trigger will be activated.
| `logic`           | Required | The body of the trigger.

---

## Examples
> The following examples are for Microsoft SQL Server but will be similar for other database engines.

### Table
```sql
{% extends "jst/mssql/table.sql.jinja" %}

{% block comments %}
-- Table containing a record of all vehicles
{% endblock %}

CREATE TABLE {% block name %} data_owner.Vehicles {% endblock %} (
	{% block columns %}
	Vehicle_ID AS INT,
	Vehicle_Name AS VARCHAR(50),
	License_Plate AS VARCHAR(20),
	Vehicle_Type AS INT
	{% endblock %}
);
```

### View
```sql
	{% extends "jst/mssql/view.sql.jinja" %}

	{% block comments %}
	-- View all vehicles of type pickup
	{% endblock %}

	CREATE VIEW {% block name %} data_owner.Pickups {% endblock %} AS
	{% block select %}
		SELECT
			v.Vehicle_ID,
			v.Vehicle_Name,
			v.License_Plate
		FROM data_owner.Vehicles AS v
		LEFT JOIN data_owner.VehicleTypes AS t
			ON v.Vehicle_Type = t.Type_ID
		WHERE t.Type_Name = 'Pickup';
	{% endblock %}
```

### Stored Procedures
```sql
{% extends "jst/mssql/procedure.sql.jinja" %}

{% block comments %}
/*	Maximum speed reached for each vehicle in the last 24-hours.

	Params:
		Start_Time datetime2(7): When the report starts in UTC.

	Result Set 1:
		Vehicle_ID int: The ID of the vehicle.
		Max_Speed int: The maximum speed during reporting period.
*/
{% endblock comments %}

CREATE PROCEDURE {% block name %} data_owner.MaxVehicleSpeed {% endblock %}
	{% block parameters %}
	@Start_Time AS DATETIME2(7)
	{% endblock %}
) AS
BEGIN
{% block logic %}

	DECLARE @End_Time AS DATETIME2(7);
	SET @End_Time = DATEADD(day, 1, @Start_Time);

	SELECT
		Vehicle_ID,
		MAX(Speed)
	FROM data_owner.Vehicle_Positions
	WHERE Date_Time >= @Start_Time
	AND Date_Time < @End_Time;

{% endblock %}
```

### Table-valued Functions

```sql
{% extends "jst/mssql/tvf.sql.jinja" %}

{% block comments %}
/* Get vehicle related information
	…
*/
{% endblock %}

CREATE FUNCTION {% block name %} data_owner.RelatedInfo {% endblock %} (
	{% block parameters %}
	@Start_Time AS DATETIME2(7),
	@End_Time AS DATETIME2(7),
	@Vehicle_ID AS VARCHAR(30)
	{% endblock %}
)
RETURNS {% block data_type %} TABLE WITH SCHEMABINDING {% endblock %} AS
RETURN
	{% block logic %}

	SELECT *
	FROM data_owner.InfoTable
	WHERE st >= @Start_Time AND et <= @End_Time
	AND Vehicle_ID = @Vehicle_ID;

	{% endblock %}
```

### Scalar Functions

```sql
{% extends "jst/mssql/scalar.sql.jinja" %}

{% block comments %}
/* Provide the connection key valid at a particular time.
	…
*/
{% endblock %}

CREATE FUNCTION {% block name %} data_owner.AccessKey {% endblock %} (
	{% block parameters %}
	@Date_Time AS DATETIME2(7)
	{% endblock %}
)
RETURNS {% block data_type %} VARCHAR(50) {% endblock %} AS
BEGIN
	{% block logic %}

	DECLARE @key AS VARCHAR(50);
	SELECT @key = machine_key
	WHERE st >= @Date_Time AND et <= @Date_Time;

	RETURN @key;

	{% endblock %}
END;
```

### Triggers

```sql
{% extends "jst/mssql/trigger.sql.jinja" %}

{% block comments %}
/*	Update the key master table when a new vehicle is created.
	…
*/
{% endblock %}

CREATE TRIGGER {% block name %} data_owner.MaintainKeyMaster {% endblock %}
ON {% block table %} data_owner.Vehicles {% endblock  %}
AFTER {% block activated %} UPDATE {% endblock %}
AS
	{% block logic %}

	INSERT INTO data_owner.KeyMaster(
		Vehicle_ID,
		Created
	)
	SELECT
		Vehicle_ID,
		CURRENT_TIMESTAMP
	FROM updated;

	{% endblock %}
```

---

## Writing New Format Templates

Format templates are in the *jinjasqltranspiller/formats* folder and are organized in subfolders, first by action (create, replace, debug) and then by database engine (e.g. `mssql`).

If you need to create code for a different database engine, create a new folder for that database engine in all 3 action folders and add your format templates in those folders.