#!/usr/bin/env python3

import requests
import json

def login_and_get_token():
    url = "http://localhost:8000/api/auth/login"
    headers = {"Content-Type": "application/json"}
    data = {
        "email": "admin@adara.com",
        "password": "SuperAdmin123!"
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")

        if response.status_code == 200:
            result = response.json()
            token = result.get("access_token")
            print(f"\nBearer Token: {token}")
            return token
        else:
            print("Login failed")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    login_and_get_token()