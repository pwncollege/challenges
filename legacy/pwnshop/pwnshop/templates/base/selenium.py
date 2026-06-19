#!/opt/pwn.college/python

import shutil
import psutil
import urllib
import atexit
import time
import sys
import os

from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

os.setuid(os.geteuid())
os.environ.clear()
os.environ["PATH"] = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

options = FirefoxOptions()
options.add_argument("--headless")
service = FirefoxService(log_path="/dev/null", executable_path=shutil.which("geckodriver"))
browser = webdriver.Firefox(service=service, options=options)
atexit.register(browser.quit)

open_ports = { s.laddr.port for s in psutil.net_connections(kind="inet") if s.status == 'LISTEN' }
if {{challenge.port or 80}} not in open_ports:
    print("Service doesn't seem to be running?")
    sys.exit(1)

{% if not challenge.specify_url %}
challenge_url = "{{ challenge.victim_url or "http://challenge.localhost:80/" }}"
{% else %}
if len(sys.argv) == 1:
    print(f"Usage: {sys.argv[0]} URL")
    sys.exit(1)

challenge_url = sys.argv[1]

url_parsed = urllib.parse.urlparse(challenge_url)
if url_parsed.hostname != "challenge.localhost":
    print("Hostname should be 'challenge.localhost'.")
    sys.exit(2)
if url_parsed.port not in { None, {{challenge.port or 80}} }:
    print("Port should be {{challenge.port or 80}}.")
    sys.exit(3)
{% endif %}

{% if challenge.flag_in_query %}
print(f"Visiting {challenge_url} (with the flag).")
challenge_url += f"""?flag={open("/flag").read().strip()}"""
{% else %}
print(f"Visiting {challenge_url}")
{% endif %}
browser.get(challenge_url)

{% if challenge.form_fields %}
{% for k,v in challenge.form_fields.items() %}
browser.find_element(By.NAME, "{{k}}").send_keys({{v}})
{% endfor %}
browser.find_element(By.NAME, "submit").submit()
{% endif %}

{% if challenge.print_page %}
print("Retrieved the following HTML:")
{% if challenge.ensure_html %}
if "<html" not in browser.page_source.lower():
    print("Doesn't look like we retrieved an HTML page...")
    sys.exit(1)
{% endif %}
print(browser.page_source)
{% endif %}

{% if challenge.reward_alert %}
try:
    WebDriverWait(browser, 1).until(EC.alert_is_present())
except TimeoutException:
    print("Failure: JavaScript alert did not trigger...")
    sys.exit(3)
else:
    print("Alert triggered! Your reward:")
    print(open("/flag").read().strip())
{% else %}
time.sleep(2)
print("{{ challenge.epilogue or "Visited! Go check if the attack worked!"}}")
{% endif %}
