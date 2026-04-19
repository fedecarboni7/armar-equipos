"""Tests for PWA (Progressive Web App) functionality"""
import json


def test_manifest_json_accessible(client):
    """Test that the manifest.json file is accessible"""
    response = client.get("/static/favicon/site.webmanifest")
    assert response.status_code == 200
    content_type = response.headers.get("content-type", "")
    assert "json" in content_type.lower()

def test_service_worker_accessible(client):
    """Test that the service worker file is accessible"""
    response = client.get("/static/service-worker.js")
    assert response.status_code == 200
    assert "javascript" in response.headers.get("content-type", "").lower()

def test_pwa_install_script_accessible(client):
    """Test that the PWA install script is accessible"""
    response = client.get("/static/js/pwa-install.js")
    assert response.status_code == 200
    assert "javascript" in response.headers.get("content-type", "").lower()

def test_landing_page_includes_pwa_meta(client):
    """Test that the landing page includes PWA meta tags"""
    response = client.get("/")
    assert response.status_code == 200
    
    html_content = response.text
    
    # Check for PWA-related meta tags
    assert 'name="mobile-web-app-capable"' in html_content
    assert 'name="apple-mobile-web-app-capable"' in html_content
    assert 'name="theme-color"' in html_content
    assert 'rel="manifest"' in html_content
    
    # Check for PWA install script
    assert '/static/js/pwa-install.js' in html_content

def test_manifest_json_content(client):
    """Test that the manifest.json has correct PWA configuration"""
    response = client.get("/static/favicon/site.webmanifest")
    assert response.status_code == 200
    
    manifest = json.loads(response.content)
    
    # Check required PWA manifest fields
    assert "name" in manifest
    assert manifest["name"] == "Armar Equipos"
    assert "short_name" in manifest
    assert "display" in manifest
    assert manifest["display"] == "standalone"
    assert "start_url" in manifest
    assert "icons" in manifest
    assert len(manifest["icons"]) >= 2
    assert "theme_color" in manifest
    assert "background_color" in manifest
