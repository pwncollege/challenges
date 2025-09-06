#!/usr/bin/python3

import subprocess
import requests
import time
import os

# Test basic server functionality
def test_server():
    # Start the server
    server = subprocess.Popen(["/challenge/server"], 
                             stdout=subprocess.PIPE, 
                             stderr=subprocess.PIPE)
    
    # Wait for server to start
    time.sleep(2)
    
    try:
        # Test that server is running
        response = requests.get("http://challenge.localhost:80/")
        assert response.status_code == 200
        assert "pwnpost" in response.text
        
        # Test login endpoint exists
        response = requests.post("http://challenge.localhost:80/login",
                                data={"username": "hacker", "password": "1337"})
        assert response.status_code in [200, 302]
        
        # Test that session is created
        session = requests.Session()
        response = session.post("http://challenge.localhost:80/login",
                               data={"username": "hacker", "password": "1337"})
        
        # Test publish endpoint requires POST  
        response = session.post("http://challenge.localhost:80/publish")
        assert response.status_code in [200, 302]
        
        print("Server functionality test passed!")
        
    finally:
        server.terminate()
        server.wait()

if __name__ == "__main__":
    test_server()