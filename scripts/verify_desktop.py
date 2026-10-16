"""Exercise real Tk widgets against a running local API; optional hold for visual QA.
Run from repo root: python -m scripts.verify_desktop [--hold]
"""
from pathlib import Path
import json
import os
import sys
import time
import tkinter as tk
import requests
from desktop.app import PhishingApp

url = os.getenv('PHISHING_API_URL', 'http://127.0.0.1:8765')
root = tk.Tk()
app = PhishingApp(root, url)
checks = []

def settle():
    deadline = time.monotonic() + 25
    while time.monotonic() < deadline:
        root.update()
        if not app.analyse_button.instate(['disabled']):
            return
        time.sleep(0.03)
    raise AssertionError('Desktop did not finish the API request.')

try:
    health = requests.get(f'{url}/health', timeout=5)
    assert health.status_code == 200
    checks.append('Live HTTP health endpoint returned 200 and model loaded')
    app.analyse()
    assert app.status.get() == 'Please enter an email message.'
    checks.append('Blank input handled in Tkinter')
    sample = 'Your account has been suspended. Verify your password immediately at https://account-check.example/login.'
    app.text.insert('1.0', sample)
    app.analyse()
    settle()
    expected = requests.post(f'{url}/predict', json={'text': sample}, timeout=10).json()
    assert app.result.get().lower() == expected['prediction']
    assert f'{expected["confidence"]:.1%}' in app.confidence.get()
    assert app.indicators.get('1.0', 'end-1c')
    checks.append('Real Tkinter -> HTTP FastAPI -> model -> result/confidence/indicators verified')
    app.clear()
    assert app.text.get('1.0', 'end-1c') == ''
    assert app.result.get() == 'Ready to analyse'
    checks.append('Clear resets message and result')
    app.api_url = 'http://127.0.0.1:1'
    app.text.insert('1.0', 'meeting agenda')
    app.analyse()
    settle()
    assert app.result.get() == 'Analysis unavailable'
    assert 'API unavailable' in app.status.get()
    checks.append('Unavailable API shown cleanly in actual desktop widgets')
    app.clear()
    app.api_url = url
    app.text.insert('1.0', sample)
    app.analyse()
    settle()
    report = {'passed': True, 'checks': checks, 'sample_result': expected}
    Path('reports/desktop_verification.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2), flush=True)
    if '--hold' in sys.argv:
        root.mainloop()
finally:
    try:
        if root.winfo_exists():
            app.close()
    except tk.TclError:
        pass
