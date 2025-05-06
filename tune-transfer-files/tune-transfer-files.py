import subprocess
import requests
import time
import argparse
import yaml
import os
from datetime import datetime

def load_config(config_path):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def parse_args():
    parser = argparse.ArgumentParser(description='JFrog Transfer Thread Tuner')
    parser.add_argument('--config', '-c', 
                      default='config.yaml',
                      help='Path to configuration file (default: config.yaml)')
    parser.add_argument('--base-url', '-u',
                      help='JFrog base URL (e.g., https://your-domain.jfrog.io)')
    parser.add_argument('--access-token', '-t',
                      help='JFrog Access Token')
    parser.add_argument('--verbose', '-v',
                      action='store_true',
                      help='Enable verbose output')
    return parser.parse_args()

def get_artifactory_config(args, config):
    # Priority: Command line args > Environment variables > Config file
    base_url = (args.base_url or 
                os.environ.get('JFROG_BASE_URL') or 
                config['artifactory']['base_url'])
    
    token = (args.access_token or 
             os.environ.get('JFROG_ACCESS_TOKEN') or 
             config['artifactory']['access_token'])
    
    if not base_url or not token:
        raise ValueError("Base URL and Access Token must be provided via arguments, environment variables, or config file")
    
    # Remove trailing slash if present
    base_url = base_url.rstrip('/')
    
    return base_url, token

# --- Configuration ---
THREAD_STEP = 64
MIN_THREADS = 8
MAX_THREADS = 1024
CHECK_INTERVAL = 300  # seconds

# --- Thresholds ---
CPU_LOW = 0.40
CPU_HIGH = 0.85
HEAP_LOW = 0.60
HEAP_HIGH = 0.85
DB_CONN_HIGH = 0.90

current_threads = 128

# --- Get Artifactory metrics ---
def get_metrics(base_url, access_token):
    url = f"{base_url}/artifactory/api/v1/metrics"
    headers = {
        "Accept": "*/*",
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(url, headers=headers, verify=False)
    response.raise_for_status()
    return response.text

def parse_timestamp(timestamp_ms):
    timestamp_sec = timestamp_ms / 1000
    return datetime.fromtimestamp(timestamp_sec).strftime('%Y-%m-%d %H:%M:%S UTC')

def format_bytes(bytes_value):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} TB"

# --- Extract metric value ---
def parse_metric(metrics, name):
    lines = metrics.splitlines()
    metric_type = None

    for i, line in enumerate(lines):
        if line.startswith(name) or line.startswith(name + "{"):
            # Search backwards for the most recent TYPE line for this metric
            for j in range(i - 1, -1, -1):
                if lines[j].startswith('# TYPE') and name in lines[j]:
                    parts = lines[j].split()
                    if len(parts) >= 4 and parts[2] == name:
                        metric_type = parts[3]
                        break

            try:
                parts = line.strip().split()
                if len(parts) < 2:
                    return None  # not enough data to extract value

                if metric_type == 'gauge':
                    if len(parts) == 2:
                        return float(parts[1])  # only value, no timestamp
                    else:
                        return float(parts[-2])  # second-last is value
                else:
                    return float(parts[-2])  # same logic for now
            except (ValueError, IndexError):
                return None

    return None




# --- Adjust threads using non-interactive JFrog CLI ---
def adjust_threads(new_count, config):
    global current_threads
    new_count = max(config['threads']['min'], min(config['threads']['max'], new_count))
    if new_count == current_threads:
        print(f"[=] Threads unchanged: {current_threads}")
        return
    try:
        print(f"[⇅] Changing threads: {current_threads} → {new_count}")
        subprocess.run(
            ['bash', '-c', f'echo {new_count} | jf rt transfer-settings'],
            check=True
        )
        current_threads = new_count
    except subprocess.CalledProcessError as e:
        print(f"[!] Thread adjustment failed: {e}")

# --- Main monitor loop ---
def monitor_and_scale(config, args, base_url, access_token):
    global current_threads
    try:
        metrics = get_metrics(base_url, access_token)
        
        # Save metrics to file in verbose mode
        if args.verbose:
            metrics_file = "artifactory_metrics.txt"
            with open(metrics_file, 'w') as f:
                f.write(metrics)
            print(f"\n[💾] Metrics saved to {metrics_file}")
            
            # Extract timestamp from the first metric line that has a value
            for line in metrics.split('\n'):
                if line and not line.startswith('#') and ' ' in line:
                    try:
                        timestamp_ms = float(line.split()[-1])
                        print(f"[⏰] Metrics timestamp: {parse_timestamp(timestamp_ms)}")
                        break
                    except (ValueError, IndexError):
                        continue
        
        # System metrics
        cpu_usage = parse_metric(metrics, "process_cpu_usage")
        system_load = parse_metric(metrics, "system_load_average_1m")
        
        # JVM metrics
        heap_used = parse_metric(metrics, "jfrt_runtime_heap_totalmemory_bytes")
        heap_max = parse_metric(metrics, "jfrt_runtime_heap_maxmemory_bytes")
        heap_free = parse_metric(metrics, "jfrt_runtime_heap_freememory_bytes")
        
        # Database metrics
        db_active = parse_metric(metrics, "jfrt_db_connections_active_total")
        db_max = parse_metric(metrics, "jfrt_db_connections_max_active_total")
        db_idle = parse_metric(metrics, "jfrt_db_connections_idle_total")
        
        # Thread metrics
        live_threads = parse_metric(metrics, "jvm_threads_live_threads")
        daemon_threads = parse_metric(metrics, "jvm_threads_daemon_threads")
        
        if any(x is None for x in [cpu_usage, heap_used, heap_max, db_active, db_max]):
            print("[DEBUG] Metric values:", cpu_usage, heap_used, heap_max, db_active, db_max)
            print("[!] Missing metrics. Skipping iteration.")
            return


        heap_ratio = heap_used / heap_max
        db_ratio = db_active / db_max
        cpu_ratio = cpu_usage

        if args.verbose:
            # Print metrics in tabular format
            print("\n[📊] System Metrics:")
            print("┌──────────────────────────────────────┬──────────────────────┬──────────────┐")
            print("│ Metric Name                          │ Source Metric        │ Value        │")
            print("├──────────────────────────────────────┼──────────────────────┼──────────────┤")
            print(f"│ CPU Usage                           │ process_cpu_usage    │ {cpu_ratio:.2%}      │")
            print(f"│ System Load (1m)                    │ system_load_average_1m │ {system_load:.2f}    │")
            print("└──────────────────────────────────────┴──────────────────────┴──────────────┘")
            
            print("\n[📊] JVM Metrics:")
            print("┌──────────────────────────────────────┬──────────────────────┬──────────────┐")
            print("│ Metric Name                          │ Source Metric        │ Value        │")
            print("├──────────────────────────────────────┼──────────────────────┼──────────────┤")
            print(f"│ JVM Heap Memory Allocated           │ jfrt_runtime_heap_totalmemory_bytes │ {format_bytes(heap_used)} │")
            print(f"│ JVM Heap Memory Maximum             │ jfrt_runtime_heap_maxmemory_bytes │ {format_bytes(heap_max)} │")
            print(f"│ JVM Heap Memory Free                │ jfrt_runtime_heap_freememory_bytes │ {format_bytes(heap_free)} │")
            print(f"│ JVM Heap Memory Usage Ratio         │ heap_used / heap_max │ {heap_ratio:.2%}      │")
            print("└──────────────────────────────────────┴──────────────────────┴──────────────┘")
            
            print("\n[📊] Database Metrics:")
            print("┌──────────────────────────────────────┬──────────────────────┬──────────────┐")
            print("│ Metric Name                          │ Source Metric        │ Value        │")
            print("├──────────────────────────────────────┼──────────────────────┼──────────────┤")
            print(f"│ Active DB Connections               │ jfrt_db_connections_active_total │ {db_active}         │")
            print(f"│ Max DB Connections                  │ jfrt_db_connections_max_active_total │ {db_max}         │")
            print(f"│ Idle DB Connections                 │ jfrt_db_connections_idle_total │ {db_idle}         │")
            print(f"│ DB Connection Usage Ratio           │ db_active / db_max   │ {db_ratio:.2%}      │")
            print("└──────────────────────────────────────┴──────────────────────┴──────────────┘")
            
            print("\n[📊] Thread Metrics:")
            print("┌──────────────────────────────────────┬──────────────────────┬──────────────┐")
            print("│ Metric Name                          │ Source Metric        │ Value        │")
            print("├──────────────────────────────────────┼──────────────────────┼──────────────┤")
            print(f"│ Live Threads                        │ jvm_threads_live_threads │ {live_threads}         │")
            print(f"│ Daemon Threads                      │ jvm_threads_daemon_threads │ {daemon_threads}         │")
            print(f"│ Current Transfer Threads            │ (internal)           │ {current_threads}         │")
            print("└──────────────────────────────────────┴──────────────────────┴──────────────┘")
            
            print("\n[⚙️] Thresholds:")
            print("┌──────────────────────────┬──────────────┐")
            print("│ Threshold                │ Value        │")
            print("├──────────────────────────┼──────────────┤")
            print(f"│ CPU Low                 │ {config['thresholds']['cpu']['low']:.2%}      │")
            print(f"│ CPU High                │ {config['thresholds']['cpu']['high']:.2%}      │")
            print(f"│ Heap Low                │ {config['thresholds']['heap']['low']:.2%}      │")
            print(f"│ Heap High               │ {config['thresholds']['heap']['high']:.2%}      │")
            print(f"│ DB Connections High     │ {config['thresholds']['db_connections']['high']:.2%}      │")
            print("└──────────────────────────┴──────────────┘")

        if (cpu_ratio < config['thresholds']['cpu']['low'] and 
            heap_ratio < config['thresholds']['heap']['low'] and 
            db_ratio < config['thresholds']['db_connections']['high']):
            adjust_threads(current_threads + config['threads']['step'], config)
        elif (cpu_ratio > config['thresholds']['cpu']['high'] or 
              heap_ratio > config['thresholds']['heap']['high'] or 
              db_ratio > config['thresholds']['db_connections']['high']):
            adjust_threads(current_threads - config['threads']['step'], config)
        elif args.verbose:
            print("[✓] Conditions stable. No scaling needed.")
    except Exception as e:
        print(f"[!] Monitor failed: {e}")

# --- Run continuously ---
if __name__ == "__main__":
    args = parse_args()
    config = load_config(args.config)
    base_url, access_token = get_artifactory_config(args, config)
    current_threads = config['threads']['min']
    
    while True:
        monitor_and_scale(config, args, base_url, access_token)
        time.sleep(config['monitoring']['check_interval'])