import pwnshop
import pwn

TABLE_NAME_DATA = [
    "data", "secrets", "notes",
    "entries", "records", "storage",
    "payloads", "repository", "items", "resources", "archive",
    "details", "information", "fragments", "logs", "dataset",
    "assets", "flags",
]

COLUMN_NAME_DATA = [
    "value", "content", "entry", "item",
    "record", "payload", "flag", "solution", "secret",
    "note", "text", "info", "field", "detail",
    "blob", "datum", "snippet",
    "element", "resource"
]

class SQLQuery(pwnshop.PythonChallenge):
	TEMPLATE_PATH = "sql.py"
	doc_hint = "https://www.sqlite.org/lang_select.html"
	db_state = "trivial"

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.table_name = self.random.choice(TABLE_NAME_DATA)
		self.column_name = self.random.choice(COLUMN_NAME_DATA)

	def verify(self, **kwargs):
		with self.run_challenge(**kwargs) as process:
			process.writeline(f"select * from {self.table_name}")
			assert self.flag in process.readall()

class SQLQuerySubstr(SQLQuery):
	max_characters = 5
	doc_hint = "https://www.sqlite.org/lang_corefunc.html#substr"
	def verify(self, **kwargs):
		flag_chars = b""
		for i in range(len(self.flag)):
			with self.run_challenge(**kwargs) as process:
				process.writeline(f"select * from {self.table_name}")
				assert self.flag not in process.readall()
			with self.run_challenge(**kwargs) as process:
				process.writeline(f"select substr({self.column_name}, {i+1}, 1) from {self.table_name}")
				flag_chars += process.readall().split(b"'")[-2]
		assert flag_chars == self.flag

class SQLQueryWhere(SQLQuery):
	doc_hint = "https://www.sqlite.org/lang_select.html#whereclause"
	db_state = "flooded"
	max_rows = 1
	max_columns = None
	flag_tag = True
	tag_value_noflag = 1
	tag_value_flag = 1337
	random_flag_tag = False

	def verify(self, **kwargs):
		with self.run_challenge(**kwargs) as process:
			process.writeline(f"select {self.column_name} from {self.table_name}")
			assert self.flag not in process.readall()
		with self.run_challenge(**kwargs) as process:
			if self.random_flag_tag:
				process.writeline(f"select * from {self.table_name} where flag_tag <> {self.tag_value_noflag}")
			else:
				process.writeline(f"select * from {self.table_name} where flag_tag = {self.tag_value_flag}")
			if self.max_columns:
				assert self.flag not in process.readall()
			else:
				assert self.flag in process.readall()
		with self.run_challenge(**kwargs) as process:
			if self.random_flag_tag:
				process.writeline(f"select {self.column_name} from {self.table_name} where flag_tag <> {self.tag_value_noflag}")
			else:
				process.writeline(f"select {self.column_name} from {self.table_name} where flag_tag = {self.tag_value_flag}")
			assert self.flag in process.readall()

class SQLQueryWhereOne(SQLQueryWhere):
	doc_hint = "https://www.sqlite.org/syntax/result-column.html"
	max_columns = 1

class SQLQueryWhereOneRandomTag(SQLQueryWhereOne):
	doc_hint = "https://www.sqlite.org/lang_expr.html"
	random_flag_tag = True

class SQLQueryWhereOneStringTag(SQLQueryWhereOne):
	doc_hint = "https://www.sqlite.org/lang_expr.html"
	tag_value_noflag = "'nope'"
	tag_value_flag = "'yep'"

class SQLQueryWhereOneNoTag(SQLQueryWhereOne):
	doc_hint = "https://www.sqlite.org/lang_corefunc.html#substr"
	flag_tag = False
	def verify(self, **kwargs):
		with self.run_challenge(**kwargs) as process:
			process.writeline(f"select {self.column_name} from {self.table_name} where flag_tag <> {self.tag_value_noflag}")
			assert b"no such column: flag_tag" in process.readall()
		with self.run_challenge(**kwargs) as process:
			process.writeline(f"select {self.column_name} from {self.table_name} where substr({self.column_name}, 1, 5) = 'pwn.c'")
			assert self.flag in process.readall()

class SQLQueryWhereDecoys(SQLQueryWhereOne):
	decoy_flags = True
	doc_hint = "https://www.geeksforgeeks.org/sql-and-and-or-operators/"
	def verify(self, **kwargs):
		with self.run_challenge(**kwargs) as process:
			process.writeline(f"select {self.column_name} from {self.table_name} where flag_tag <> {self.tag_value_noflag}")
			assert self.flag not in process.readall()
		with self.run_challenge(**kwargs) as process:
			process.writeline(f"select {self.column_name} from {self.table_name} where substr({self.column_name}, 1, 5) = 'pwn.c'")
			assert self.flag not in process.readall()
		with self.run_challenge(**kwargs) as process:
			process.writeline(f"select {self.column_name} from {self.table_name} where substr({self.column_name}, 1, 5) = 'pwn.c' and flag_tag <> {self.tag_value_noflag}")
			assert self.flag in process.readall()

class SQLQueryWhereDecoysNoTag(SQLQueryWhereOneNoTag):
	flag_tag = False
	decoy_flags = True
	doc_hint = "https://www.sqlite.org/lang_select.html#limitoffset"
	def verify(self, **kwargs):
		with self.run_challenge(**kwargs) as process:
			process.writeline(f"select {self.column_name} from {self.table_name} where substr({self.column_name}, 1, 5) = 'pwn.c'")
			assert self.flag not in process.readall()
		with self.run_challenge(**kwargs) as process:
			process.writeline(f"select {self.column_name} from {self.table_name} where substr({self.column_name}, 1, 5) = 'pwn.c' limit 1")
			assert self.flag in process.readall()

class SQLQueryRandomTable(pwnshop.PythonChallenge):
	TEMPLATE_PATH = "sql.py"
	doc_hint = "https://www.sqlite.org/schematab.html"
	db_state = "randomized"
	max_columns = 1
	num_queries = 2

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.column_name = self.random.choice(COLUMN_NAME_DATA)

	def verify(self, **kwargs):
		with self.run_challenge(**kwargs) as process:
			process.writeline("SELECT tbl_name FROM sqlite_master""")
			process.readuntil("\n- ")
			table_name = process.clean().split(b"'")[-2].decode()
			process.writeline(f"select * from {table_name}")
			assert self.flag in process.readall()
