"""Golden tests for qlsc-parse. Each case states, by hand, what a correct parse must say.

Run: uv run --with 'sqlglot[c]>=30' --with pytest pytest pipeline/parser/tests -q
"""
import pytest

from qlsc_parse import Catalog, fingerprint, resolve

RULES = [{"pattern": r"_[0-9a-f]{12,}$", "replace": "_{hex}"},
         {"pattern": r"^LR_[0-9A-Z]{10,30}_", "replace": "LR_{id}_"}]
EVENT_PARAMS = "ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64>>>"
CAT = Catalog({
    "version": "test",
    "aliases": {"phys.fnb_raw": "p.raw"},
    "shard_families": ["p.ga.events_"],
    "tables": {
        "p.raw.customer": {"kind": "TABLE", "partition": None, "columns": {
            "CIF_NO": "STRING", "NAME": "STRING", "SSN": "STRING", "OPEN_DT": "DATE"}},
        "p.raw.account": {"kind": "TABLE", "partition": "BAL_DT", "columns": {
            "ACCT_ID": "INT64", "CIF_NO": "STRING", "BAL": "NUMERIC", "BAL_DT": "DATE"}},
        "p.dw.dim_customer": {"kind": "TABLE", "partition": None, "columns": {
            "customer_key": "INT64", "cif_number": "STRING", "segment": "STRING", "preferred_branch_id": "STRING"}},
        "p.dw.fct_txn": {"kind": "TABLE", "partition": "post_date", "columns": {
            "txn_id": "STRING", "customer_key": "INT64", "amount_cents": "INT64", "post_date": "DATE",
            "mcc": "STRING"}},
        "p.dw.dim_branch": {"kind": "TABLE", "partition": None, "columns": {
            "branch_id": "STRING", "branch_name": "STRING", "parent_branch_id": "STRING"}},
        "p.dw.stg_customer": {"kind": "VIEW", "partition": None, "columns": {
            "cif_number": "STRING", "name": "STRING"},
            "view_sql": "SELECT CIF_NO AS cif_number, NAME AS name FROM `p.raw.customer`"},
        "p.ga.events_*": {"kind": "WILDCARD", "partition": None, "columns": {
            "event_date": "STRING", "event_name": "STRING", "user_pseudo_id": "STRING", "user_id": "STRING",
            "event_params": EVENT_PARAMS, "collected_traffic_source": "STRUCT<manual_campaign_name STRING>",
            "_TABLE_SUFFIX": "STRING"}},
    }}, RULES)


def R(sql, project="p"):
    return resolve(sql, CAT, project)


def joins(rec):
    """Joins as (side, side, type), sides sorted by short name so tests read naturally."""
    out = set()
    for j in rec["joins"]:
        a, b = sorted(j[k]["table"].split(".")[-1] + "." + j[k]["column"] for k in ("left", "right"))
        out.add((a, b, j["type"]))
    return out


def read(rec, table, column, path=None):
    return next(r for r in rec["reads"] if r["table"].endswith(table) and r["column"] == column
                and r["path"] == path)


def lineage(rec):
    return {c["target"]: (c["kind"], sorted(f["table"].split(".")[-1] + "." + f["column"] for f in c["from"]))
            for w in rec["writes"] for c in w["columns"]}


# ------------------------------------------------------------------------ joins

def test_aliased_join():
    r = R("SELECT c.segment, SUM(t.amount_cents) FROM `p.dw.fct_txn` t "
          "JOIN `p.dw.dim_customer` c ON t.customer_key = c.customer_key GROUP BY 1")
    assert r["status"] == "ok"
    assert joins(r) == {("dim_customer.customer_key", "fct_txn.customer_key", "INNER")}
    assert read(r, "fct_txn", "amount_cents")["agg"] == ["SUM"]
    assert "group" in read(r, "dim_customer", "segment")["roles"]


def test_using_becomes_column_pair():
    r = R("SELECT segment FROM `p.dw.fct_txn` LEFT JOIN `p.dw.dim_customer` USING (customer_key)")
    assert joins(r) == {("dim_customer.customer_key", "fct_txn.customer_key", "LEFT")}


def test_join_through_cte_rename_traces_to_base():
    r = R("WITH a AS (SELECT x.CIF_NO AS cid FROM `p.raw.customer` x) "
          "SELECT d.segment FROM a JOIN `p.dw.dim_customer` d ON a.cid = d.cif_number")
    assert joins(r) == {("customer.CIF_NO", "dim_customer.cif_number", "INNER")}
    j = r["joins"][0]
    side = j["left"] if j["left"]["column"] == "CIF_NO" else j["right"]
    assert side["via"] == "rename"


def test_shadowed_alias_in_cte_and_outer_query():
    # `a` is dim_customer inside the CTE and account outside it
    r = R("WITH k AS (SELECT a.cif_number FROM `p.dw.dim_customer` a) "
          "SELECT a.BAL FROM `p.raw.account` a JOIN k ON a.CIF_NO = k.cif_number")
    assert joins(r) == {("account.CIF_NO", "dim_customer.cif_number", "INNER")}


def test_join_wrappers_recorded():
    r = R("SELECT 1 FROM `p.raw.account` a JOIN `p.dw.dim_customer` d "
          "ON LPAD(CAST(a.ACCT_ID AS STRING), 10, '0') = d.cif_number")
    j = r["joins"][0]
    acct = j["left"] if j["left"]["column"] == "ACCT_ID" else j["right"]
    assert acct["wrap"] == ["LPAD", "CAST<STRING>"]


def test_join_on_derived_transform_is_marked():
    r = R("SELECT 1 FROM (SELECT CONCAT('C', CIF_NO) AS k FROM `p.raw.customer`) s "
          "JOIN `p.dw.dim_customer` d ON s.k = d.cif_number")
    j = r["joins"][0]
    cust = j["left"] if j["left"]["column"] == "CIF_NO" else j["right"]
    assert cust["via"] == "transform" and "CONCAT" in cust["wrap"]


def test_aggregate_order_by_column_is_not_a_join_side():
    # first_seg is branch_id; parent_branch_id only picks which row wins
    r = R("WITH f AS (SELECT ARRAY_AGG(branch_id ORDER BY parent_branch_id)[OFFSET(0)] AS first_seg "
          "FROM `p.dw.dim_branch`) SELECT 1 FROM f JOIN `p.dw.dim_customer` d ON f.first_seg = d.preferred_branch_id")
    assert joins(r) == {("dim_branch.branch_id", "dim_customer.preferred_branch_id", "INNER")}


def test_control_origin_marked_in_lineage():
    r = R("CREATE TABLE `p.dw.t5` AS SELECT ARRAY_AGG(branch_id ORDER BY parent_branch_id)[OFFSET(0)] AS first_b "
          "FROM `p.dw.dim_branch`")
    src = {f["column"]: f.get("control", False) for f in r["writes"][0]["columns"][0]["from"]}
    assert src == {"branch_id": False, "parent_branch_id": True}


def test_case_condition_is_not_a_join_side():
    r = R("SELECT 1 FROM (SELECT CASE WHEN segment = 'A' THEN cif_number END AS k FROM `p.dw.dim_customer`) s "
          "JOIN `p.raw.customer` c ON s.k = c.CIF_NO")
    assert joins(r) == {("customer.CIF_NO", "dim_customer.cif_number", "INNER")}


def test_in_subquery_is_a_semi_join():
    r = R("SELECT txn_id FROM `p.dw.fct_txn` WHERE customer_key IN "
          "(SELECT customer_key FROM `p.dw.dim_customer` WHERE segment = 'AFFLUENT')")
    assert ("dim_customer.customer_key", "fct_txn.customer_key", "IN") in joins(r)


def test_correlated_exists_is_a_join():
    r = R("SELECT d.cif_number FROM `p.dw.dim_customer` d WHERE EXISTS "
          "(SELECT 1 FROM `p.dw.fct_txn` t WHERE t.customer_key = d.customer_key)")
    assert ("dim_customer.customer_key", "fct_txn.customer_key", "WHERE") in joins(r)


def test_self_join_on_hierarchy():
    r = R("SELECT b.branch_name, p.branch_name FROM `p.dw.dim_branch` b "
          "JOIN `p.dw.dim_branch` p ON b.parent_branch_id = p.branch_id")
    assert joins(r) == {("dim_branch.branch_id", "dim_branch.parent_branch_id", "INNER")}


def test_on_clause_literal_is_a_filter_not_a_join():
    r = R("SELECT 1 FROM `p.dw.fct_txn` t JOIN `p.dw.dim_customer` c "
          "ON t.customer_key = c.customer_key AND c.segment = 'MASS'")
    assert len(r["joins"]) == 1
    assert any(f["column"] == "segment" and f["clause"] == "on" for f in r["filters"])


# ---------------------------------------------------------------- filters, scan

def test_unnest_event_params_filter_and_path():
    sql = ("SELECT (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id') AS s "
           "FROM `p.ga.events_*` WHERE _TABLE_SUFFIX BETWEEN '20260401' AND '20260407' "
           "AND event_name = 'page_view'")
    r = R(sql)
    assert r["status"] == "ok"
    key = next(f for f in r["filters"] if f["column"] == "event_params")
    assert key["path"] == "key" and key["op"] == "="
    lits = fingerprint(sql, CAT, "p")["literals"]
    assert [lits[i] for i in key["slots"]] == ["ga_session_id"]
    assert read(r, "events_*", "event_params", "value.int_value")
    assert r["scan"]["partition_filter"]["p.ga.events_*"] == "pushed"


def test_group_by_alias_of_correlated_subquery():
    # qualify copies the subquery into GROUP BY unqualified; it must still resolve
    r = R("SELECT (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location') AS page, "
          "COUNT(*) FROM `p.ga.events_*` WHERE _TABLE_SUFFIX = '20260405' GROUP BY page")
    assert r["status"] == "ok", r["unresolved"]


def test_missing_partition_filter_and_select_star_limit():
    r = R("SELECT * FROM `p.dw.fct_txn` LIMIT 10")
    assert r["scan"] == {"select_star": True, "limit": 10, "partition_filter": {"p.dw.fct_txn": "none"}}


def test_partition_filter_pushed():
    r = R("SELECT SUM(amount_cents) FROM `p.dw.fct_txn` WHERE post_date >= '2026-06-01'")
    assert r["scan"]["partition_filter"]["p.dw.fct_txn"] == "pushed"


def test_partition_filter_after_aggregation_is_not_pushed():
    r = R("SELECT * FROM (SELECT post_date, SUM(amount_cents) AS s FROM `p.dw.fct_txn` GROUP BY 1) "
          "WHERE post_date >= '2026-06-01'")
    assert r["scan"]["partition_filter"]["p.dw.fct_txn"] == "none"


def test_filter_slots_and_in_list():
    sql = "SELECT 1 FROM `p.dw.fct_txn` WHERE mcc IN ('5411', '5812') AND amount_cents > 100"
    r, lits = R(sql), fingerprint(sql, CAT, "p")["literals"]
    f = {x["column"]: x for x in r["filters"]}
    assert f["mcc"]["op"] == "IN" and [lits[i] for i in f["mcc"]["slots"]] == ["5411", "5812"]
    assert f["amount_cents"]["op"] == ">" and [lits[i] for i in f["amount_cents"]["slots"]] == ["100"]


def test_qualify_and_window_roles():
    r = R("SELECT customer_key, txn_id FROM `p.dw.fct_txn` "
          "QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_key ORDER BY post_date DESC) = 1")
    assert "window" in read(r, "fct_txn", "post_date")["roles"]


def test_struct_field_path():
    r = R("SELECT collected_traffic_source.manual_campaign_name FROM `p.ga.events_*` "
          "WHERE _TABLE_SUFFIX = '20260401'")
    assert read(r, "events_*", "collected_traffic_source", "manual_campaign_name")


def test_case_insensitive_columns_use_catalog_spelling():
    r = R("SELECT cif_no, name FROM `p.raw.customer`")
    assert {x["column"] for x in r["reads"]} == {"CIF_NO", "NAME"}


# ------------------------------------------------------------------ writes

def test_ctas_lineage_kinds():
    r = R("CREATE OR REPLACE TABLE `p.dw.cust_summary` AS SELECT c.cif_number, c.segment AS seg, "
          "SUM(t.amount_cents) AS spend, CASE WHEN c.segment = 'A' THEN 1 ELSE 0 END AS is_a "
          "FROM `p.dw.dim_customer` c JOIN `p.dw.fct_txn` t USING (customer_key) GROUP BY 1, 2, 4")
    assert r["statement_type"] == "CREATE_TABLE_AS_SELECT"
    L = lineage(r)
    assert L["cif_number"] == ("passthrough", ["dim_customer.cif_number"])
    assert L["seg"] == ("rename", ["dim_customer.segment"])
    assert L["spend"] == ("aggregate", ["fct_txn.amount_cents"])
    assert L["is_a"] == ("transform", ["dim_customer.segment"])


def test_view_definition_lineage():
    r = R(CAT.get("p.dw.stg_customer")["view_sql"].replace("SELECT", "CREATE VIEW `p.dw.stg_customer` AS SELECT", 1))
    assert r["writes"][0]["mode"] == "VIEW"
    assert lineage(r) == {"cif_number": ("rename", ["customer.CIF_NO"]), "name": ("passthrough", ["customer.NAME"])}


def test_view_read_is_not_expanded():
    r = R("SELECT name FROM `p.dw.stg_customer`")
    assert r["tables"] == [{"id": "p.dw.stg_customer", "kind": "view"}]
    assert read(r, "stg_customer", "name")


def test_insert_positional_lineage():
    r = R("INSERT INTO `p.dw.dim_branch` (branch_id, branch_name) SELECT CIF_NO, UPPER(NAME) FROM `p.raw.customer`")
    L = lineage(r)
    assert L["branch_id"] == ("passthrough", ["customer.CIF_NO"])
    assert L["branch_name"] == ("transform", ["customer.NAME"])


def test_dbt_merge_lineage_and_keys():
    r = R("""merge into `p`.`dw`.`dim_customer` as DBT_INTERNAL_DEST using (
               select CIF_NO as cif_number, UPPER(NAME) as segment from `p`.`raw`.`customer`
             ) as DBT_INTERNAL_SOURCE
             on (DBT_INTERNAL_SOURCE.cif_number = DBT_INTERNAL_DEST.cif_number)
             when matched then update set `segment` = DBT_INTERNAL_SOURCE.`segment`
             when not matched then insert (`cif_number`, `segment`) values (`cif_number`, `segment`)""")
    w = r["writes"][0]
    assert w["mode"] == "MERGE"
    L = lineage(r)
    assert L["cif_number"] == ("rename", ["customer.CIF_NO"])
    assert L["segment"] == ("transform", ["customer.NAME"])
    assert w["merge_keys"] == [{"target": "cif_number", "from": [{"table": "p.raw.customer", "column": "CIF_NO"}]}]


def test_union_all_lineage_is_positional():
    r = R("CREATE VIEW `p.dw.v` AS WITH a AS (SELECT CIF_NO AS id, 'CORE' AS src FROM `p.raw.customer`), "
          "b AS (SELECT cif_number, 'DW' FROM `p.dw.dim_customer`) SELECT * FROM a UNION ALL SELECT * FROM b")
    assert lineage(r)["id"] == ("rename", ["customer.CIF_NO", "dim_customer.cif_number"])


def test_union_of_star_branches_over_unaliased_ctes():
    # later branches are SELECT * over CTEs whose outputs are unaliased and collide
    # (two CAST(NULL ...)); qualify leaves the * unexpanded; BigQuery unions by position
    r = R("CREATE TABLE `p.dw.u` AS WITH a AS (SELECT CIF_NO AS id, NAME AS nm, CAST(NULL AS STRING) AS x "
          "FROM `p.raw.customer`), b AS (SELECT cif_number, CAST(NULL AS STRING), CAST(NULL AS STRING) "
          "FROM `p.dw.dim_customer`), un AS (SELECT * FROM a UNION ALL SELECT * FROM b) SELECT u.id, u.nm FROM un u")
    assert lineage(r)["id"] == ("rename", ["customer.CIF_NO", "dim_customer.cif_number"])


def test_delete_filter():
    r = R("DELETE FROM `p.raw.account` WHERE BAL_DT = DATE '2026-06-01'")
    assert r["statement_type"] == "DELETE"
    assert r["filters"][0]["column"] == "BAL_DT"
    assert r["writes"] == [{"table": "p.raw.account", "mode": "DELETE", "columns": []}]


def test_negated_predicates():
    r = R("SELECT 1 FROM `p.dw.fct_txn` WHERE mcc IS NOT NULL AND mcc NOT IN ('1', '2') "
          "AND NOT (amount_cents > 5)")
    ops = sorted(f["op"] for f in r["filters"])
    assert ops == ["IS NOT NULL", "NOT >", "NOT IN"]


def test_group_by_all_marks_group_keys():
    r = R("SELECT segment, SUM(customer_key) FROM `p.dw.dim_customer` GROUP BY ALL")
    assert "group" in read(r, "dim_customer", "segment")["roles"]
    assert "group" not in read(r, "dim_customer", "customer_key")["roles"]


def test_ctas_with_parenthesized_body():
    r = R("CREATE OR REPLACE TABLE `p.dw.t2` PARTITION BY post_date AS (SELECT post_date, txn_id FROM `p.dw.fct_txn`)")
    assert lineage(r) == {"post_date": ("passthrough", ["fct_txn.post_date"]),
                          "txn_id": ("passthrough", ["fct_txn.txn_id"])}


def test_count_star_is_an_aggregate_not_a_constant():
    r = R("CREATE TABLE `p.dw.t3` AS SELECT segment, COUNT(*) AS n, 'X' AS k FROM `p.dw.dim_customer` GROUP BY 1")
    L = {c["target"]: (c["kind"], c["fn"]) for c in r["writes"][0]["columns"]}
    assert L["n"] == ("aggregate", ["COUNT"]) and L["k"] == ("constant", [])


def test_merge_insert_row():
    r = R("""merge into `p.dw.dim_customer` as DBT_INTERNAL_DEST using (
               select CIF_NO as cif_number, NAME as segment from `p.raw.customer`) as DBT_INTERNAL_SOURCE
             on FALSE
             when not matched by source and DBT_INTERNAL_DEST.segment = 'x' then delete
             when not matched then insert row""")
    assert lineage(r) == {"cif_number": ("rename", ["customer.CIF_NO"]), "segment": ("rename", ["customer.NAME"])}


def test_filters_not_duplicated_by_group_by_alias_copy():
    r = R("SELECT (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location') AS page, "
          "COUNT(*) FROM `p.ga.events_*` WHERE _TABLE_SUFFIX = '20260405' GROUP BY page")
    keys = [(f["column"], f["path"], f["op"]) for f in r["filters"]]
    assert sorted(keys) == [("_TABLE_SUFFIX", None, "="), ("event_params", "key", "=")]


def test_countif_uses_bigquery_spelling():
    r = R("SELECT COUNTIF(amount_cents > 0) FROM `p.dw.fct_txn`")
    assert read(r, "fct_txn", "amount_cents")["agg"] == ["COUNTIF"]


def test_looker_pdt_generations_share_one_table():
    cat = Catalog({"version": "t", "rules": RULES, "tables": {
        "p.looker_scratch.LR_6H0IZB3PQ4C6N_customer_facts": {"kind": "TABLE", "columns": {"k": "INT64"}}}})
    r = resolve("SELECT k FROM `p.looker_scratch.LR_9Z9Z9Z9Z9Z9Z9_customer_facts`", cat, "p")
    assert r["status"] == "ok" and r["tables"] == [{"id": "p.looker_scratch.LR_{id}_customer_facts", "kind": "table"}]


def test_scaling_constant_in_lineage():
    r = R("CREATE TABLE `p.dw.t4` AS SELECT SUM(amount_cents) / 100 AS spend_usd, SUM(amount_cents) AS raw_sum "
          "FROM `p.dw.fct_txn`")
    fn = {c["target"]: c["fn"] for c in r["writes"][0]["columns"]}
    assert "/100" in fn["spend_usd"] and "/100" not in fn["raw_sum"]


def test_columns_compared():
    r = R("SELECT CORR(a.BAL, t.amount_cents) FROM `p.raw.account` a JOIN `p.dw.fct_txn` t ON a.CIF_NO = t.txn_id")
    assert [({c["left"]["column"], c["right"]["column"]}, c["ops"]) for c in r["comparisons"]] == \
        [({"BAL", "amount_cents"}, ["CORR"])]


# ------------------------------------------------------------- health, names

def test_unknown_table_blames_the_table():
    r = R("SELECT days_to_close FROM sbx_typo.churn_cohort WHERE days_to_close < 5")
    assert r["status"] == "partial"
    kinds = {(u["kind"], u["reason"]) for u in r["unresolved"]}
    assert ("table", "not in catalog") in kinds and ("column", "table unresolved") in kinds


def test_typo_column_is_unresolved():
    r = R("SELECT segmnt FROM `p.dw.dim_customer`")
    assert r["status"] == "partial" and r["unresolved"][0]["kind"] == "column"


def test_information_schema_is_system():
    r = R("SELECT table_name FROM `p.dw`.INFORMATION_SCHEMA.COLUMNS WHERE column_name LIKE '%cif%'")
    assert r["status"] == "ok" and r["tables"][0]["kind"] == "system"


def test_transient_staging_table_is_expected():
    r = R("MERGE `p.raw.customer` T USING `p.raw.stage_customer_25ad1233b062` S ON T.CIF_NO = S.CIF_NO "
          "WHEN MATCHED THEN UPDATE SET NAME = S.NAME")
    assert r["status"] == "ok"
    assert {"id": "p.raw.stage_customer_{hex}", "kind": "transient"} in r["tables"]
    # no catalog entry to restore case from; BigQuery column names are case-insensitive
    assert lineage(r)["NAME"] == ("passthrough", ["stage_customer_{hex}.name"])


def test_physical_names_map_to_logical_and_shards_to_wildcard():
    r = R("SELECT NAME FROM `phys.fnb_raw.customer`")
    assert r["tables"] == [{"id": "p.raw.customer", "kind": "table"}]
    r = R("SELECT event_name FROM `p.ga.events_20260401`")
    assert r["tables"] == [{"id": "p.ga.events_*", "kind": "wildcard"}]


def test_family_ignores_identifiers():
    a = R("SELECT COUNT(*) AS row_count FROM `p.raw.account` WHERE BAL_DT >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)")
    b = R("SELECT COUNT(*) AS row_count FROM `p.dw.fct_txn` WHERE post_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)")
    c = R("SELECT MAX(post_date) FROM `p.dw.fct_txn`")
    assert a["family_id"] == b["family_id"] != c["family_id"]


def test_output_summary():
    probe = R("SELECT COUNT(*) AS failures, COUNT(*) != 0 AS should_warn FROM "
              "(SELECT cif_number FROM `p.dw.dim_customer` GROUP BY 1 HAVING COUNT(*) > 1) dbt_internal_test")
    assert probe["output"] == {"columns": 2, "aggregate_only": True, "grouped": False, "root_from": None}
    rows = R("SELECT segment, COUNT(*) FROM `p.dw.dim_customer` GROUP BY 1")
    assert rows["output"] == {"columns": 2, "aggregate_only": False, "grouped": True,
                              "root_from": "p.dw.dim_customer"}
    assert "output" not in R("CREATE TABLE `p.dw.x` AS SELECT 1 AS a")


# ------------------------------------------------------------- fingerprint

def test_fingerprint_ignores_literals_comments_whitespace_case():
    a = fingerprint("SELECT NAME FROM `p.raw.customer` WHERE CIF_NO = 'A1'", CAT, "p")
    b = fingerprint("/* x */ select  name\nfrom `p.raw.customer`  where cif_no = 'B2' -- y", CAT, "p")
    assert a["shape_id"] == b["shape_id"] and b["literals"] == ["B2"]


def test_fingerprint_keeps_in_list_length():
    a = fingerprint("SELECT 1 FROM `p.dw.fct_txn` WHERE mcc IN ('1', '2')", CAT, "p")
    b = fingerprint("SELECT 1 FROM `p.dw.fct_txn` WHERE mcc IN ('1', '2', '3')", CAT, "p")
    assert a["shape_id"] != b["shape_id"]


def test_fingerprint_canonicalizes_volatile_names():
    a = fingerprint("SELECT 1 FROM `p.raw.stage_customer_25ad1233b062`", CAT, "p")
    b = fingerprint("SELECT 1 FROM `p.raw.stage_customer_3dcb5817eea1`", CAT, "p")
    c = fingerprint("SELECT 1 FROM `p.ga.events_20260401`", CAT, "p")
    d = fingerprint("SELECT 1 FROM `p.ga.events_20260402`", CAT, "p")
    assert a["shape_id"] == b["shape_id"] and c["shape_id"] == d["shape_id"]


def test_fingerprint_annotations():
    f = fingerprint("-- Looker Query Context '{\"user_id\":113,\"history_slug\":\"2b3\"}'\nSELECT 1", CAT, "p")
    assert f["annotations"] == [{"source": "Looker Query Context", "user_id": 113, "history_slug": "2b3"}]
