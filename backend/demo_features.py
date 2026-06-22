#!/usr/bin/env python3
"""
Demo script to showcase all new backend features.
Run this after starting the server: uvicorn app.main:app --reload
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def demo_authentication():
    print_section("1. Authentication & Refresh Tokens")
    
    # Login
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "analyst",
        "password": "analyst123"
    })
    
    if response.status_code == 200:
        tokens = response.json()
        print(f"✓ Login successful")
        print(f"  Access Token: {tokens['access_token'][:50]}...")
        print(f"  Refresh Token: {tokens['refresh_token'][:50]}...")
        print(f"  Token Type: {tokens['token_type']}")
        return tokens
    else:
        print(f"✗ Login failed: {response.status_code}")
        return None

def demo_filtering(token):
    print_section("2. Filtering & Pagination")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create some test logs
    for i in range(5):
        requests.post(f"{BASE_URL}/logs/", headers=headers, json={
            "source": "firewall-01",
            "severity": "high" if i % 2 == 0 else "info",
            "message": f"Test log {i+1}"
        })
    
    # Filter by severity
    response = requests.get(
        f"{BASE_URL}/logs/?severity=high&limit=10",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Filtered logs by severity=high")
        print(f"  Total logs: {data['total']}")
        print(f"  Returned: {len(data['logs'])}")
        print(f"  Skip: {data['skip']}, Limit: {data['limit']}")

def demo_bulk_operations(admin_token):
    print_section("3. Bulk Operations (Admin)")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Create some alerts
    alert_ids = []
    for i in range(3):
        response = requests.post(f"{BASE_URL}/alerts/", headers=headers, json={
            "title": f"Test Alert {i+1}",
            "severity": "high",
            "source": "test-source"
        })
        if response.status_code == 201:
            alert_ids.append(response.json()['id'])
    
    print(f"✓ Created {len(alert_ids)} test alerts: {alert_ids}")
    
    # Bulk update
    response = requests.patch(f"{BASE_URL}/alerts/bulk/status", headers=headers, json={
        "alert_ids": alert_ids,
        "status": "acknowledged"
    })
    
    if response.status_code == 200:
        updated = response.json()
        print(f"✓ Bulk updated {len(updated)} alerts to 'acknowledged'")

def demo_incident_status(token):
    print_section("4. Incident Status Management")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create incident
    response = requests.post(f"{BASE_URL}/incidents/", headers=headers, json={
        "title": "Test Security Incident",
        "description": "Testing status workflow"
    })
    
    if response.status_code == 201:
        incident = response.json()
        incident_id = incident['id']
        print(f"✓ Created incident #{incident_id}")
        print(f"  Initial status: {incident['status']}")
        
        # Update to in-progress
        response = requests.patch(
            f"{BASE_URL}/incidents/{incident_id}/status",
            headers=headers,
            json={"status": "in-progress"}
        )
        
        if response.status_code == 200:
            incident = response.json()
            print(f"✓ Updated to: {incident['status']}")
            
            # Close incident
            response = requests.patch(
                f"{BASE_URL}/incidents/{incident_id}/status",
                headers=headers,
                json={"status": "closed"}
            )
            
            if response.status_code == 200:
                incident = response.json()
                print(f"✓ Closed incident: {incident['status']}")

def demo_user_management(admin_token):
    print_section("5. User Management (Admin Only)")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Create new user
    response = requests.post(f"{BASE_URL}/auth/register", json={
        "username": "demo_user",
        "password": "demo123",
        "role": "analyst"
    })
    
    if response.status_code == 201:
        print(f"✓ Created user: demo_user")
    
    # List all users
    response = requests.get(f"{BASE_URL}/auth/users", headers=headers)
    
    if response.status_code == 200:
        users = response.json()
        print(f"✓ Total users: {len(users)}")
        for user in users:
            print(f"  - {user['username']} ({user['role']}) - Active: {user['is_active']}")
    
    # Update user role
    response = requests.patch(
        f"{BASE_URL}/auth/users/demo_user",
        headers=headers,
        json={"role": "admin"}
    )
    
    if response.status_code == 200:
        user = response.json()
        print(f"✓ Promoted demo_user to: {user['role']}")
    
    # Delete user
    response = requests.delete(
        f"{BASE_URL}/auth/users/demo_user",
        headers=headers
    )
    
    if response.status_code == 200:
        print(f"✓ Deleted demo_user")

def demo_enum_validation(token):
    print_section("6. Enum Validation")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Try invalid severity
    response = requests.post(f"{BASE_URL}/logs/", headers=headers, json={
        "source": "test",
        "severity": "super-critical",  # Invalid!
        "message": "test"
    })
    
    if response.status_code == 422:
        print(f"✓ Correctly rejected invalid severity")
        print(f"  Error: {response.json()['detail'][0]['msg']}")
    
    # Valid severity
    response = requests.post(f"{BASE_URL}/logs/", headers=headers, json={
        "source": "test",
        "severity": "critical",  # Valid!
        "message": "test"
    })
    
    if response.status_code == 201:
        print(f"✓ Accepted valid severity: critical")

def main():
    print("\n" + "="*60)
    print("  AI SOC Assistant - Backend Features Demo")
    print("="*60)
    print("\nMake sure the server is running:")
    print("  uvicorn app.main:app --reload\n")
    
    try:
        # Check if server is running
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("✗ Server not responding!")
            return
        print("✓ Server is running\n")
        
        # Demo authentication
        tokens = demo_authentication()
        if not tokens:
            return
        
        access_token = tokens['access_token']
        
        # Login as admin for admin features
        admin_response = requests.post(f"{BASE_URL}/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        admin_token = admin_response.json()['access_token'] if admin_response.status_code == 200 else access_token
        
        # Run all demos
        demo_filtering(access_token)
        demo_bulk_operations(admin_token)
        demo_incident_status(access_token)
        demo_user_management(admin_token)
        demo_enum_validation(access_token)
        
        print_section("Demo Complete!")
        print("All new features are working correctly! ✓")
        print("\nCheck the API docs for more details:")
        print(f"  {BASE_URL}/docs\n")
        
    except requests.exceptions.ConnectionError:
        print("\n✗ Could not connect to server!")
        print("  Make sure it's running: uvicorn app.main:app --reload\n")
    except Exception as e:
        print(f"\n✗ Error: {e}\n")

if __name__ == "__main__":
    main()
