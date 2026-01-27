"""Gradio frontend launcher.

This is the entry point for the Gradio web interface. It delegates UI construction
to the `ui` module and launches the application.
"""
from ui import build_ui

if __name__ == "__main__":
    # Build and launch the UI
    demo = build_ui()
    demo.launch(server_name="0.0.0.0", server_port=7860, root_path="/nlp_tresnak")
