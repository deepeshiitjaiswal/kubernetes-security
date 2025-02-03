import psutil
import time
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ResourceMonitor:
    def __init__(self):
        try:
            self.prev_cpu_times = psutil.cpu_times()
            self.prev_time = time.time()
            logger.info("ResourceMonitor initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing ResourceMonitor: {str(e)}")
            raise

    def get_cpu_cores(self):
        """Get the number of CPU cores"""
        try:
            cores = psutil.cpu_count()
            logger.debug(f"CPU cores: {cores}")
            return cores
        except Exception as e:
            logger.error(f"Error getting CPU cores: {str(e)}")
            return 1

    def get_cpu_usage(self):
        """Get CPU usage in cores"""
        try:
            current_cpu_times = psutil.cpu_times()
            current_time = time.time()

            # Calculate the difference
            time_diff = current_time - self.prev_time
            idle_diff = current_cpu_times.idle - self.prev_cpu_times.idle
            total_diff = sum(getattr(current_cpu_times, field) - getattr(self.prev_cpu_times, field)
                           for field in current_cpu_times._fields)

            # Update previous values
            self.prev_cpu_times = current_cpu_times
            self.prev_time = current_time

            # Calculate usage
            if total_diff == 0:
                return 0
            
            cpu_usage = (total_diff - idle_diff) / total_diff
            cores_usage = cpu_usage * self.get_cpu_cores()
            logger.debug(f"CPU usage: {cores_usage:.2f} cores")
            return cores_usage
        except Exception as e:
            logger.error(f"Error getting CPU usage: {str(e)}")
            return 0

    def get_memory_info(self):
        """Get memory usage in GB"""
        try:
            memory = psutil.virtual_memory()
            total_gb = memory.total / (1024 ** 3)  # Convert to GB
            used_gb = (memory.total - memory.available) / (1024 ** 3)  # Convert to GB
            logger.debug(f"Memory usage: {used_gb:.2f}GB / {total_gb:.2f}GB")
            return used_gb, total_gb
        except Exception as e:
            logger.error(f"Error getting memory info: {str(e)}")
            return 0, 1

    def get_disk_info(self):
        """Get disk usage in GB"""
        try:
            disk = psutil.disk_usage('/')
            total_gb = disk.total / (1024 ** 3)  # Convert to GB
            used_gb = disk.used / (1024 ** 3)  # Convert to GB
            logger.debug(f"Disk usage: {used_gb:.2f}GB / {total_gb:.2f}GB")
            return used_gb, total_gb
        except Exception as e:
            logger.error(f"Error getting disk info: {str(e)}")
            return 0, 1

    def get_metrics(self):
        """Get all resource metrics"""
        try:
            logger.info("Getting resource metrics...")
            cpu_cores = self.get_cpu_cores()
            cpu_usage = self.get_cpu_usage()
            memory_usage, memory_total = self.get_memory_info()
            disk_usage, disk_total = self.get_disk_info()

            metrics = {
                'timestamp': datetime.now().isoformat(),
                'cpu_cores': cpu_cores,
                'cpu_usage': round(cpu_usage, 2),
                'memory_usage': round(memory_usage, 2),
                'memory_total': round(memory_total, 2),
                'disk_usage': round(disk_usage, 2),
                'disk_total': round(disk_total, 2)
            }
            logger.info(f"Resource metrics collected successfully: {metrics}")
            return metrics
        except Exception as e:
            logger.error(f"Error getting resource metrics: {str(e)}")
            return None
