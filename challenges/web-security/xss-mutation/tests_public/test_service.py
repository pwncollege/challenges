#!/usr/bin/python3

import subprocess
import time

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService


server = subprocess.Popen(["/challenge/server"])
browser = None
try:
    for _ in range(100):
        try:
            requests.get("http://challenge.localhost/", timeout=1).raise_for_status()
            break
        except requests.RequestException:
            time.sleep(0.1)
    else:
        raise AssertionError("server did not become ready in time")

    payload = "<strong>formatted review</strong>"
    requests.post(
        "http://challenge.localhost/payload", data={"payload": payload}
    ).raise_for_status()
    response = requests.get("http://challenge.localhost/")
    response.raise_for_status()
    assert payload not in response.text

    options = FirefoxOptions()
    options.add_argument("--headless")
    service = FirefoxService(
        executable_path="/usr/local/bin/geckodriver", log_path="/dev/null"
    )
    browser = webdriver.Firefox(service=service, options=options)
    browser.get("http://challenge.localhost/preview")

    preview = browser.find_element(By.ID, "preview")
    assert preview.get_attribute("textContent") == payload
    assert not preview.find_elements(By.TAG_NAME, "strong")
finally:
    if browser is not None:
        browser.quit()
    server.terminate()
    server.wait()
