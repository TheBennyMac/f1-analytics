"""Tests for the Jolpica API client using mocked HTTP responses."""

import json
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

import src.data.jolpica_client as jc


def _mock_response(data: dict) -> MagicMock:
    m = MagicMock()
    m.json.return_value = data
    m.raise_for_status.return_value = None
    return m


RACES_PAYLOAD = {
    "MRData": {
        "RaceTable": {
            "Races": [
                {"round": "1", "raceName": "Australian Grand Prix"},
                {"round": "2", "raceName": "Malaysian Grand Prix"},
            ]
        }
    }
}

STANDINGS_PAYLOAD = {
    "MRData": {
        "StandingsTable": {
            "StandingsLists": [
                {
                    "ConstructorStandings": [
                        {
                            "position": "1",
                            "points": "43",
                            "Constructor": {"constructorId": "mercedes", "name": "Mercedes"},
                        },
                        {
                            "position": "2",
                            "points": "25",
                            "Constructor": {"constructorId": "red_bull", "name": "Red Bull"},
                        },
                    ]
                }
            ]
        }
    }
}

RESULTS_PAYLOAD = {
    "MRData": {
        "RaceTable": {
            "Races": [
                {
                    "round": "1",
                    "raceName": "Australian Grand Prix",
                    "Results": [
                        {
                            "position": "1",
                            "Driver": {"driverId": "rosberg"},
                            "Constructor": {"constructorId": "mercedes"},
                            "status": "Finished",
                            "points": "25",
                            "laps": "57",
                            "Time": {"millis": "0", "time": "1:32:58.710"},
                        },
                        {
                            "position": "2",
                            "Driver": {"driverId": "hamilton"},
                            "Constructor": {"constructorId": "mercedes"},
                            "status": "Finished",
                            "points": "18",
                            "laps": "57",
                            "Time": {"millis": "26777", "time": "+26.777"},
                        },
                    ],
                }
            ]
        }
    }
}


@patch("src.data.jolpica_client.requests.get")
@patch("src.data.jolpica_client._cache_path")
def test_get_constructor_standings_shape(mock_cache_path, mock_get, tmp_path):
    cache_file = tmp_path / "constructor_standings_2014.json"
    mock_cache_path.return_value = cache_file

    mock_get.side_effect = [
        _mock_response(RACES_PAYLOAD),      # races call
        _mock_response(STANDINGS_PAYLOAD),  # round 1
        _mock_response(STANDINGS_PAYLOAD),  # round 2
    ]

    df = jc.get_constructor_standings_by_round(2014)

    assert isinstance(df, pd.DataFrame)
    assert set(df.columns) >= {"season", "round", "constructor_id", "points", "position"}
    assert len(df) == 4  # 2 rounds × 2 constructors
    assert (df["season"] == 2014).all()
    assert set(df["round"].unique()) == {1, 2}


@patch("src.data.jolpica_client.requests.get")
@patch("src.data.jolpica_client._cache_path")
def test_get_constructor_standings_uses_cache(mock_cache_path, mock_get, tmp_path):
    cached_rows = [{"season": 2014, "round": 1, "constructor_id": "mercedes",
                    "constructor_name": "Mercedes", "points": 43.0, "position": 1}]
    cache_file = tmp_path / "constructor_standings_2014.json"
    cache_file.write_text(json.dumps(cached_rows), encoding="utf-8")
    mock_cache_path.return_value = cache_file

    df = jc.get_constructor_standings_by_round(2014)

    mock_get.assert_not_called()
    assert len(df) == 1


@patch("src.data.jolpica_client.requests.get")
@patch("src.data.jolpica_client._cache_path")
def test_get_race_results_columns(mock_cache_path, mock_get, tmp_path):
    cache_file = tmp_path / "race_results_2014.json"
    mock_cache_path.return_value = cache_file
    mock_get.return_value = _mock_response(RESULTS_PAYLOAD)

    df = jc.get_race_results(2014)

    assert isinstance(df, pd.DataFrame)
    expected_cols = {"season", "round", "race_name", "driver_id", "constructor_id",
                     "position", "status", "points", "laps", "gap_ms"}
    assert expected_cols.issubset(set(df.columns))
    assert len(df) == 2


@patch("src.data.jolpica_client.requests.get")
@patch("src.data.jolpica_client._cache_path")
def test_get_race_results_gap_ms_winner_is_zero(mock_cache_path, mock_get, tmp_path):
    cache_file = tmp_path / "race_results_2014.json"
    mock_cache_path.return_value = cache_file
    mock_get.return_value = _mock_response(RESULTS_PAYLOAD)

    df = jc.get_race_results(2014)
    winner = df[df["position"] == 1].iloc[0]
    assert winner["gap_ms"] == 0


@patch("src.data.jolpica_client.requests.get")
@patch("src.data.jolpica_client._cache_path")
def test_get_race_results_gap_ms_p2(mock_cache_path, mock_get, tmp_path):
    cache_file = tmp_path / "race_results_2014.json"
    mock_cache_path.return_value = cache_file
    mock_get.return_value = _mock_response(RESULTS_PAYLOAD)

    df = jc.get_race_results(2014)
    p2 = df[df["position"] == 2].iloc[0]
    assert p2["gap_ms"] == 26777
