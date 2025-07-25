"""
Gunicorn configuration file for kgcomponents project.
"""

import multiprocessing
import os

# Bind to 0.0.0.0:8000
bind = "0.0.0.0:8000"

# Number of worker processes
# A good rule of thumb is 2-4 x number of CPU cores
workers = multiprocessing.cpu_count() * 2 + 1

# Worker class
worker_class = "uvicorn.workers.UvicornWorker"

# Maximum number of requests a worker will process before restarting
max_requests = 1000
max_requests_jitter = 50

# Timeout for worker processes in seconds
timeout = 120

# Restart workers that have been silent for this many seconds
keepalive = 5

# Log level
loglevel = "info"

# Access log format
accesslog = "-"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(L)s'

# Error log
errorlog = "-"

# Preload the application
preload_app = True

# Process name
proc_name = "kgcomponents"

# Server hooks
def on_starting(server):
    """
    Called just before the master process is initialized.
    """
    print("Starting Gunicorn server...")

def on_exit(server):
    """
    Called just before exiting.
    """
    print("Shutting down Gunicorn server...")

def post_fork(server, worker):
    """
    Called just after a worker has been forked.
    """
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def pre_fork(server, worker):
    """
    Called just before a worker is forked.
    """
    pass

def pre_exec(server):
    """
    Called just before a new master process is forked.
    """
    server.log.info("Forked child, re-executing.")

def when_ready(server):
    """
    Called when the server is ready to serve requests.
    """
    server.log.info("Server is ready. Spawning workers...")

def worker_int(worker):
    """
    Called when a worker receives SIGINT or SIGQUIT.
    """
    worker.log.info("Worker received INT or QUIT signal")

def worker_abort(worker):
    """
    Called when a worker receives SIGABRT.
    """
    worker.log.info("Worker received ABORT signal")

