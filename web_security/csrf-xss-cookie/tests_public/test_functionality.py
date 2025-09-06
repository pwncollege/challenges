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
        
        # Test ephemeral endpoint with XSS vulnerability
        response = requests.get("http://challenge.localhost:80/ephemeral?msg=<script>test</script>")
        assert response.status_code == 200
        assert "<script>test</script>" in response.text
        
        # Test login with cookies
        response = requests.post("http://challenge.localhost:80/login",
                                data={"username": "hacker", "password": "1337"},
                                allow_redirects=False)
        assert response.status_code == 302
        assert "auth" in response.cookies
        
        print("Server functionality test passed!")
        
    finally:
        server.terminate()
        server.wait()

if __name__ == "__main__":
    test_server()