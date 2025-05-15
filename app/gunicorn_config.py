import os

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
backlog = 1024

# ASGI configuration using Uvicorn worker for FastAPI
wsgi_app = "main:app"
worker_class = "uvicorn.workers.UvicornWorker"

# Worker processes - minimal for memory constraints
workers = 1  # Nur ein Worker um Memory-Probleme zu vermeiden
timeout = 300  # Längeres Timeout für bessere Stabilität
keepalive = 5
graceful_timeout = 10

# Logging - extensive for debugging
accesslog = "-"
errorlog = "-"
loglevel = "debug"
capture_output = True
access_log_format = '%({x-forwarded-for}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None

# Memory management
worker_tmp_dir = "/tmp"
max_requests = 0  # Deaktiviert, um Worker-Recycling zu vermeiden, das zu 502-Fehlern führen kann
max_requests_jitter = 0

# Debug options
reload = False
reload_engine = "auto"

# Security
limit_request_fields = 1000
limit_request_field_size = 8190

# Kein Preloading, um mögliche Probleme zu vermeiden
preload_app = False