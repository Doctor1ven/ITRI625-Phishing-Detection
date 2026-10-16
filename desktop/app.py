"""Tkinter → FastAPI client. No model or ML library is loaded by the GUI."""
import os
import queue
import threading
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

import requests

API_URL = os.getenv('PHISHING_API_URL', 'http://127.0.0.1:8000').rstrip('/')
MAX_TEXT_LENGTH = 100_000


def request_prediction(text, api_url=API_URL):
    try:
        response = requests.post(f'{api_url}/predict', json={'text': text}, timeout=(3, 20))
        response.raise_for_status()
        result = response.json()
        if (not isinstance(result, dict)
                or result.get('prediction') not in ('phishing', 'legitimate')
                or not isinstance(result.get('confidence'), (int, float))
                or not 0 <= result['confidence'] <= 1
                or not isinstance(result.get('phishing_probability'), (int, float))
                or not 0 <= result['phishing_probability'] <= 1
                or not isinstance(result.get('model'), str)
                or not isinstance(result.get('indicators'), list)
                or any(not isinstance(item, dict) or not isinstance(item.get('term'), str)
                       or not isinstance(item.get('probability_drop'), (int, float))
                       for item in result['indicators'])):
            raise ValueError('Invalid prediction response.')
        return result
    except requests.ConnectionError as exc:
        raise RuntimeError('API unavailable. Start FastAPI in a separate terminal, then try again.') from exc
    except requests.Timeout as exc:
        raise RuntimeError('The API timed out. Check the server and try again.') from exc
    except requests.HTTPError as exc:
        raise RuntimeError(f'API error ({exc.response.status_code}). Check the server status and model files.') from exc
    except (ValueError, KeyError, requests.RequestException) as exc:
        raise RuntimeError('The API returned an invalid response. Check the server logs.') from exc


class PhishingApp:
    def __init__(self, root, api_url=API_URL):
        self.root = root
        self.api_url = api_url
        self.events = queue.Queue()
        self.generation = 0
        root.title('ITRI625 | Phishing Email Detector')
        root.geometry('850x750')
        root.minsize(720, 670)
        style = ttk.Style(root)
        style.configure('Title.TLabel', font=('Helvetica', 22, 'bold'))
        style.configure('Result.TLabel', font=('Helvetica', 18, 'bold'))
        style.configure('Body.TLabel', font=('Helvetica', 11))
        frame = ttk.Frame(root, padding=24)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='Phishing Email Detector', style='Title.TLabel').pack(anchor='w')
        ttk.Label(frame, text='Paste an email subject and message, then select Analyse Email.',
                  style='Body.TLabel').pack(anchor='w', pady=(8, 14))
        self.text = ScrolledText(frame, height=12, wrap='word', font=('Helvetica', 12), padx=10, pady=10)
        self.text.pack(fill='both', expand=True)
        buttons = ttk.Frame(frame)
        buttons.pack(fill='x', pady=12)
        self.analyse_button = ttk.Button(buttons, text='Analyse Email', command=self.analyse)
        self.analyse_button.pack(side='left')
        ttk.Button(buttons, text='Clear', command=self.clear).pack(side='left', padx=10)
        self.result = tk.StringVar(value='Ready to analyse')
        self.confidence = tk.StringVar(value='')
        self.status = tk.StringVar(value=f'API: {api_url}')
        ttk.Label(frame, textvariable=self.result, style='Result.TLabel').pack(anchor='w', pady=(5, 6))
        ttk.Label(frame, textvariable=self.confidence, style='Body.TLabel').pack(anchor='w')
        ttk.Label(frame, text='Local indicators — change in phishing probability when a term is removed',
                  wraplength=750).pack(anchor='w', pady=(14, 5))
        self.indicators = ScrolledText(frame, height=5, wrap='word', font=('Helvetica', 11), state='disabled')
        self.indicators.pack(fill='x')
        ttk.Label(frame, textvariable=self.status, wraplength=750).pack(anchor='w', pady=(10, 5))
        ttk.Label(frame, text='Classroom prototype: positive labels include spam. Confidence is a model estimate; '
                  'a Legitimate prediction does not guarantee safety.', wraplength=750).pack(anchor='w', pady=(5, 0))
        self.poll_id = root.after(100, self.poll)
        root.protocol('WM_DELETE_WINDOW', self.close)

    def set_indicators(self, value):
        self.indicators.configure(state='normal')
        self.indicators.delete('1.0', tk.END)
        self.indicators.insert('1.0', value)
        self.indicators.configure(state='disabled')

    def analyse(self):
        text = self.text.get('1.0', 'end-1c')
        if not text.strip():
            self.status.set('Please enter an email message.')
            return
        if len(text) > MAX_TEXT_LENGTH:
            self.status.set(f'Please use at most {MAX_TEXT_LENGTH:,} characters.')
            return
        self.generation += 1
        generation = self.generation
        self.analyse_button.state(['disabled'])
        self.result.set('Analysing…')
        self.confidence.set('')
        self.set_indicators('')
        self.status.set('Waiting for the local API…')
        # Network work stays off the Tk main thread; only poll() updates widgets.
        def worker():
            try:
                self.events.put((generation, request_prediction(text, self.api_url), None))
            except Exception as exc:
                self.events.put((generation, None, str(exc)))
        threading.Thread(target=worker, daemon=True).start()

    def poll(self):
        try:
            while True:
                generation, response, error = self.events.get_nowait()
                if generation != self.generation:
                    continue  # Ignore results for a message that was cleared/replaced.
                self.analyse_button.state(['!disabled'])
                if error:
                    self.result.set('Analysis unavailable')
                    self.status.set(error)
                    continue
                self.result.set(response['prediction'].title())
                self.confidence.set(f'Confidence: {response["confidence"]:.1%}   |   '
                                    f'P(Phishing): {response["phishing_probability"]:.1%}')
                lines = [f'{item["term"]}: {item["probability_drop"]:+.3f}'
                         for item in response.get('indicators', [])]
                self.set_indicators('\n'.join(lines) or 'No known terms available for explanation.')
                self.status.set(response.get('warning') or f'Complete · {response["model"]}. '
                                'Positive indicator values support the phishing score.')
        except queue.Empty:
            pass
        self.poll_id = self.root.after(100, self.poll)

    def clear(self):
        self.generation += 1
        self.text.delete('1.0', tk.END)
        self.result.set('Ready to analyse')
        self.confidence.set('')
        self.set_indicators('')
        self.status.set(f'API: {self.api_url}')
        self.analyse_button.state(['!disabled'])
        self.text.focus_set()

    def close(self):
        self.root.after_cancel(self.poll_id)
        self.root.destroy()


def main():
    root = tk.Tk()
    PhishingApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
