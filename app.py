"""Compatibility entry point for the MeasureTrace WSGI application."""

from measuretrace.web import application, main

app = application

if __name__ == "__main__":
    main()
