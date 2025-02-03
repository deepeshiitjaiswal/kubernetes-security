from kubernetes import client, config
from datetime import datetime
import psutil
import os

class ClusterMonitor:
    def __init__(self):
        try:
            config.load_incluster_config()
        except config.ConfigException:
            try:
                config.load_kube_config()
            except config.ConfigException:
                raise Exception("Could not configure kubernetes client")
        
        self.core_v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()

    def get_cluster_metrics(self):
        """Get comprehensive cluster metrics"""
        try:
            # Get nodes information
            nodes = self.core_v1.list_node().items
            node_metrics = []
            
            for node in nodes:
                # Get node status
                status = "Ready"
                for condition in node.status.conditions:
                    if condition.type == "Ready":
                        status = "Ready" if condition.status == "True" else "NotReady"
                        break
                
                # Get node capacity
                allocatable = node.status.allocatable
                capacity = node.status.capacity
                
                # Convert CPU millicores to cores
                cpu_capacity = float(capacity['cpu'])
                memory_capacity = int(self._parse_memory(capacity['memory']))
                
                # Get node metrics
                cpu_usage = self._get_node_cpu_usage(node.metadata.name)
                memory_usage = self._get_node_memory_usage(node.metadata.name)
                pods_running = len(self.core_v1.list_pod_for_all_namespaces(
                    field_selector=f'spec.nodeName={node.metadata.name}').items)
                
                node_metrics.append({
                    'name': node.metadata.name,
                    'status': status,
                    'cpu_capacity': cpu_capacity,
                    'cpu_usage': cpu_usage,
                    'memory_capacity': memory_capacity,
                    'memory_usage': memory_usage,
                    'pods_running': pods_running
                })
            
            # Get cluster-wide metrics
            all_pods = self.core_v1.list_pod_for_all_namespaces().items
            all_services = self.core_v1.list_service_for_all_namespaces().items
            all_namespaces = self.core_v1.list_namespace().items
            
            # Calculate cluster-wide resource usage
            cluster_cpu_usage = sum(node['cpu_usage'] for node in node_metrics)
            cluster_memory_usage = sum(node['memory_usage'] for node in node_metrics)
            cluster_cpu_capacity = sum(node['cpu_capacity'] for node in node_metrics)
            cluster_memory_capacity = sum(node['memory_capacity'] for node in node_metrics)
            
            return {
                'timestamp': datetime.now().isoformat(),
                'total_nodes': len(nodes),
                'total_pods': len(all_pods),
                'total_services': len(all_services),
                'total_namespaces': len(all_namespaces),
                'cluster_cpu_usage': cluster_cpu_usage,
                'cluster_cpu_capacity': cluster_cpu_capacity,
                'cluster_memory_usage': cluster_memory_usage,
                'cluster_memory_capacity': cluster_memory_capacity,
                'nodes': node_metrics
            }
            
        except Exception as e:
            print(f"Error getting cluster metrics: {str(e)}")
            return None

    def _get_node_cpu_usage(self, node_name):
        """Get CPU usage for a node"""
        try:
            # In a real cluster, you would use metrics-server
            # For local development, we'll simulate with random values
            return psutil.cpu_percent(interval=1) / 100
        except:
            return 0.0

    def _get_node_memory_usage(self, node_name):
        """Get memory usage for a node"""
        try:
            # In a real cluster, you would use metrics-server
            # For local development, we'll simulate with random values
            return psutil.virtual_memory().used
        except:
            return 0

    def _parse_memory(self, memory_str):
        """Convert Kubernetes memory string to bytes"""
        try:
            if memory_str.endswith('Ki'):
                return int(memory_str[:-2]) * 1024
            elif memory_str.endswith('Mi'):
                return int(memory_str[:-2]) * 1024 * 1024
            elif memory_str.endswith('Gi'):
                return int(memory_str[:-2]) * 1024 * 1024 * 1024
            else:
                return int(memory_str)
        except:
            return 0
