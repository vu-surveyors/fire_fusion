import pytest
from fastapi.testclient import TestClient
from src.api.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "FireFusion Harmonised Backend API"
    assert "endpoints" in data

def test_health_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["records"]["canonical_detections"] > 0
    assert data["records"]["fire_clusters"] > 0
    assert data["records"]["daily_aggregates"] > 0

def test_meta_endpoint(client):
    response = client.get("/api/v1/meta")
    assert response.status_code == 200
    data = response.json()
    assert data["project"] == "FireFusion"
    assert "disclaimer" in data

def test_summary_endpoint(client):
    response = client.get("/api/v1/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["total_detections"] == 51349
    assert data["total_harmonized_clusters"] == 18030
    assert data["corroborated_clusters"] > 0

def test_calendar_endpoint(client):
    response = client.get("/api/v1/calendar?year=2020&mode=harmonised")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert len(data["data"]) > 0
    first = data["data"][0]
    assert "date" in first
    assert "count" in first
    assert "harmonized_event_count" in first

def test_clusters_endpoint(client):
    response = client.get("/api/v1/clusters?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert len(data["data"]) == 5
    first = data["data"][0]
    assert "cluster_id" in first
    assert "centroid" in first
    assert "event_score" in first

def test_cluster_by_id(client):
    # First get one cluster id
    res = client.get("/api/v1/clusters?limit=1")
    cid = res.json()["data"][0]["cluster_id"]
    
    # Detail
    res_detail = client.get(f"/api/v1/clusters/{cid}")
    assert res_detail.status_code == 200
    c_data = res_detail.json()["data"]
    assert c_data["cluster_id"] == cid
    assert "members" in c_data

def test_cells_endpoint(client):
    response = client.get("/api/v1/cells?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 5
    assert "centroid_lat" in data["data"][0]

def test_validation_endpoint(client):
    response = client.get("/api/v1/validation")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "overlap_correlation" in data["metrics"]
    assert "overlap_ratio" in data["metrics"]
    assert "step_change_test" in data["metrics"]

def test_anomalies_endpoint(client):
    response = client.get("/api/v1/anomalies?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert "disclaimer" in data
    assert len(data["data"]) > 0

def test_baseline_endpoint(client):
    response = client.get("/api/v1/anomalies/baseline")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) > 0
    assert "baseline_median" in data["data"][0]

def test_brief_endpoint(client):
    response = client.get("/api/v1/brief?year=2025")
    assert response.status_code == 200
    data = response.json()
    assert "headline" in data
    assert "summary_text" in data
    assert "guardrails" in data

def test_bundle_endpoint(client):
    response = client.get("/api/v1/bundle?limit_clusters=10&limit_detections=10")
    assert response.status_code == 200
    data = response.json()
    assert "cells" in data["data"]
    assert "calendar" in data["data"]
    assert "clusters" in data["data"]
    assert "provenance" in data

def test_csv_downloads(client):
    res_cal = client.get("/api/v1/download/calendar.csv?year=2025")
    assert res_cal.status_code == 200
    assert "text/csv" in res_cal.headers["content-type"]
    
    res_hot = client.get("/api/v1/download/hotspots.csv?year=2025")
    assert res_hot.status_code == 200
    assert "text/csv" in res_hot.headers["content-type"]

