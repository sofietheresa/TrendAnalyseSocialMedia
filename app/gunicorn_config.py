import os

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', '8080')}"
backlog = 1024

# WSGI entry point: file name "main.py" and Flask app instance "app"
wsgi_app = "main:app"

# Worker processes - using a fixed small number for memory constraints
workers = 2  # Using just 2 workers to conserve memory
worker_class = 'sync'
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 2

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'debug'
access_log_format = '%({x-forwarded-for}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = 'trendanalyse-api'

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Memory management
worker_tmp_dir = '/dev/shm'  # Using shared memory for temp files
max_requests = 1000  # Restart workers after this many requests
max_requests_jitter = 50  # Add randomness to max_requests

# SSL
keyfile = None
certfile = None

# Debugging
reload = False
reload_engine = 'auto'

# Security
limit_request_fields = 32768
limit_request_field_size = 8192

# Preload app to save memory
preload_app = True ##