import sys, traceback

try:
    import supabase
    print("IMPORT_OK", getattr(supabase, "__version__", "no-version"))
except Exception:
    traceback.print_exc()
    sys.exit(1)
