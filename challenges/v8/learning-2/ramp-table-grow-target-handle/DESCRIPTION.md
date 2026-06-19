The dispatch-table escape stages a computed trusted-dispatch-table handle immediately before growing a table.
The useful value is not copied from one fixed donor table; it is derived from the stride between nearby table handles and the target slot the later call path will use.

In this level, the harness gives you two calibration tables, one grow table, and guarded caged access only to their dispatch-handle fields.
Read the calibration handles, compute the target handle with `targetOffset`, write it into `growTable`, call `growStagedTable()`, and run `/challenge/run` with your solve file to get the flag.
