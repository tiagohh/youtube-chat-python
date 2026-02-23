import tkinter as tk
from tkinter.scrolledtext import ScrolledText


class ChatUI:
    """Very simple GUI for displaying chat messages."""

    def __init__(self, title="YouTube Chat"):
        self.root = tk.Tk()
        self.root.title(title)

        # ensure any Tk callbacks with exceptions pop up a dialog
        def _tk_error_handler(exc_type, exc_value, exc_traceback):
            try:
                from tkinter import messagebox
                messagebox.showerror("Tkinter error", str(exc_value))
            except Exception:
                pass
        self.root.report_callback_exception = lambda *args: _tk_error_handler(*args)

        self.text_area = ScrolledText(self.root, state="disabled", wrap="word")
        self.text_area.pack(expand=True, fill="both")

    def prompt_credentials(self):
        """Show a modal dialog asking for API key and a video URL/ID.

        The dialog blocks until **Connect** is pressed or the window is closed.
        It returns a tuple ``(api_key, video_id_or_url)``; empty strings mean
        the user cancelled/closed the dialog.
        """
        dlg = tk.Toplevel(self.root)
        dlg.title("Credentials")
        dlg.transient(self.root)
        dlg.grab_set()

        tk.Label(dlg, text="API Key:").grid(row=0, column=0, sticky="e")
        api_entry = tk.Entry(dlg, width=50)
        api_entry.grid(row=0, column=1, pady=5, padx=5)

        tk.Label(dlg, text="Video URL/ID:").grid(row=1, column=0, sticky="e")
        video_entry = tk.Entry(dlg, width=50)
        video_entry.grid(row=1, column=1, pady=5, padx=5)

        # variables to capture values before the window is destroyed
        result = {'api': '', 'video': ''}

        def on_ok():
            result['api'] = api_entry.get().strip()
            result['video'] = video_entry.get().strip()
            dlg.destroy()

        def on_close():
            # user closed window via [X]; leave results empty
            dlg.destroy()

        ok_btn = tk.Button(dlg, text="Connect", command=on_ok)
        ok_btn.grid(row=2, column=0, columnspan=2, pady=10)
        dlg.protocol("WM_DELETE_WINDOW", on_close)

        # wait for dialog to close
        self.root.wait_window(dlg)
        return result['api'], result['video']

    def append_message(self, author: str, message: str):
        """Add a line to the chat window."""
        self.text_area.configure(state="normal")
        self.text_area.insert("end", f"{author}: {message}\n")
        self.text_area.configure(state="disabled")
        self.text_area.yview("end")

    def start(self):
        """Run the Tk main loop."""
        self.root.mainloop()
