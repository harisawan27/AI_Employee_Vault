import subprocess
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger("HealthMonitor")

SERVICES = ['webxes-api', 'orchestrator', 'gmail-watcher']

def check_services():
    for service in SERVICES:
        result = subprocess.run(['systemctl', 'is-active', service], capture_output=True, text=True)
        if result.stdout.strip() != 'active':
            logger.warning(f"Service {service} is down! Attempting restart...")
            subprocess.run(['sudo', 'systemctl', 'restart', service])
        else:
            logger.info(f"{service} is running healthily.")

if __name__ == "__main__":
    logger.info("Starting WEBXES Health Monitor...")
    while True:
        try:
            check_services()
        except Exception as e:
            logger.error(f"Monitor error: {e}")
        time.sleep(60)  # Check every 60 seconds
