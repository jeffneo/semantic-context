"""Warehouse connectors: chosen by config, and SQL in logical names is rewritten to the deployed tables."""

from __future__ import annotations

import json

import pytest

from qlsc import config
from qlsc.warehouse import connect


def settings(tmp_path, kind="bigquery"):
    (tmp_path / "estate.yaml").write_text(
        f"warehouse: {{type: {kind}, project: phys, gcloud_config: none, location: US, dataset_prefix: fnb_}}\n"
    )
    s = config.load(tmp_path / "estate.yaml")
    (s.work / "catalog.json").write_text(
        json.dumps(
            {
                "aliases": {"phys.fnb_core": "bank-dw.core"},
                "tables": {
                    "bank-dw.core.accounts": {"kind": "TABLE"},
                    "bank-dw.core.LR_{id}_daily": {"kind": "TABLE", "physical": ["LR_1_daily", "LR_2_daily"]},
                },
            }
        )
    )
    return s


def test_unknown_warehouse_is_a_clear_error(tmp_path):
    with pytest.raises(config.ConfigError, match="no connector for warehouse type 'oracle'"):
        connect(settings(tmp_path, "oracle"))


def test_logical_names_are_rewritten_to_the_deployed_tables(tmp_path):
    wh = connect(settings(tmp_path))
    sql = wh.physical_sql(
        "SELECT a.id FROM `bank-dw.core.accounts` a JOIN `bank-dw.core.LR_{id}_daily` d USING (id)"
    )
    assert "phys.fnb_core.accounts" in sql.replace("`", "")
    assert "phys.fnb_core.LR_2_daily" in sql.replace("`", "")  # the newest generation


def test_unparseable_sql_fails_the_dry_run_without_calling_the_warehouse(tmp_path):
    assert connect(settings(tmp_path)).dry_run("SELEC nothing FROM")["ok"] is False
