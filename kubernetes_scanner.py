from kubernetes import client, config
import logging
from error_handler import KubernetesError
import os
import requests
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class KubernetesScanner:
    def __init__(self):
        try:
            # Check if kubeconfig exists
            kubeconfig_path = os.path.expanduser('~/.kube/config')
            if not os.path.exists(kubeconfig_path):
                raise KubernetesError(
                    "Kubernetes configuration file not found. Please ensure that:\n"
                    "1. You have a Kubernetes cluster running\n"
                    "2. Your kubeconfig file is present at ~/.kube/config\n"
                    "3. You have the necessary permissions"
                )

            # Try to load the kubeconfig
            config.load_kube_config()
            
            # Test the connection
            self.core_v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
            
            # Try to list nodes to verify connection
            self.core_v1.list_node()
            
        except config.config_exception.ConfigException as e:
            logger.error(f"Kubernetes config error: {str(e)}")
            raise KubernetesError(
                "Invalid Kubernetes configuration. Please ensure that:\n"
                "1. Your kubeconfig file is properly formatted\n"
                "2. The cluster context is correctly set\n"
                f"Error details: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Kubernetes client: {str(e)}")
            raise KubernetesError(
                "Failed to connect to Kubernetes cluster. Please ensure that:\n"
                "1. Your cluster is running (try 'kubectl cluster-info')\n"
                "2. You have the necessary permissions\n"
                f"Error details: {str(e)}"
            )

    def get_cluster_resources(self):
        try:
            pods = self.core_v1.list_pod_for_all_namespaces()
            services = self.core_v1.list_service_for_all_namespaces()
            nodes = self.core_v1.list_node()

            return {
                'pods': len(pods.items),
                'services': len(services.items),
                'nodes': len(nodes.items)
            }
        except Exception as e:
            logger.error(f"Failed to get cluster resources: {str(e)}")
            raise KubernetesError(f"Failed to get cluster resources: {str(e)}")

    def scan_cluster(self):
        try:
            pods = self.core_v1.list_pod_for_all_namespaces()
            vulnerabilities = {
                'CRITICAL': 0,
                'HIGH': 0,
                'MEDIUM': 0,
                'LOW': 0
            }
            
            scanned_pods = []
            total_cves = []
            
            for pod in pods.items:
                pod_vulns, pod_cves = self._scan_pod(pod)
                scanned_pods.append({
                    'name': pod.metadata.name,
                    'namespace': pod.metadata.namespace,
                    'vulnerabilities': pod_vulns,
                    'cves': pod_cves
                })
                
                # Update vulnerability counts
                for vuln in pod_vulns:
                    vulnerabilities[vuln['severity']] += 1
                
                # Add CVEs to total list
                total_cves.extend(pod_cves)
            
            # Get unique CVEs
            unique_cves = {cve['id']: cve for cve in total_cves}.values()
            
            return {
                'vulnerabilities': vulnerabilities,
                'pods': scanned_pods,
                'cves': list(unique_cves),
                'scan_time': datetime.utcnow().isoformat(),
                'summary': {
                    'total_pods': len(pods.items),
                    'vulnerable_pods': len([p for p in scanned_pods if p['vulnerabilities'] or p['cves']]),
                    'total_cves': len(unique_cves)
                }
            }
        except Exception as e:
            logger.error(f"Failed to scan cluster: {str(e)}")
            raise KubernetesError(f"Failed to scan cluster: {str(e)}")

    def _scan_pod(self, pod):
        """
        Scan a pod for vulnerabilities and CVEs.
        """
        vulnerabilities = []
        cves = []
        
        try:
            # Check for privileged containers
            for container in pod.spec.containers:
                if container.security_context and container.security_context.privileged:
                    vulnerabilities.append({
                        'severity': 'HIGH',
                        'description': f'Container {container.name} is running with privileged access',
                        'affected_resource': container.name,
                        'recommendation': 'Remove privileged access unless absolutely necessary'
                    })
                
                # Check for latest tag
                if container.image.endswith(':latest'):
                    vulnerabilities.append({
                        'severity': 'MEDIUM',
                        'description': f'Container {container.name} uses latest tag which is not recommended',
                        'affected_resource': container.name,
                        'recommendation': 'Use specific version tags for container images'
                    })
                
                # Mock CVE checks for container images
                image_cves = self._check_image_cves(container.image)
                cves.extend(image_cves)
            
            # Check for resource limits
            if not pod.spec.containers[0].resources or not pod.spec.containers[0].resources.limits:
                vulnerabilities.append({
                    'severity': 'LOW',
                    'description': 'Pod does not have resource limits set',
                    'affected_resource': pod.metadata.name,
                    'recommendation': 'Set resource limits to prevent resource exhaustion'
                })
            
            # Check for security context
            if not pod.spec.security_context:
                vulnerabilities.append({
                    'severity': 'MEDIUM',
                    'description': 'Pod does not have security context defined',
                    'affected_resource': pod.metadata.name,
                    'recommendation': 'Define security context with appropriate settings'
                })
            
            return vulnerabilities, cves
            
        except Exception as e:
            logger.error(f"Error scanning pod {pod.metadata.name}: {str(e)}")
            return [], []

    def _check_image_cves(self, image):
        """
        Mock function to check for CVEs in container images.
        In a real implementation, this would use tools like Trivy, Clair, or Anchore.
        """
        # Mock CVE data for demonstration
        common_cves = [
            {
                'id': 'CVE-2023-1234',
                'severity': 'CRITICAL',
                'description': 'Remote code execution vulnerability in container runtime',
                'affected_versions': ['1.0.0-1.2.0'],
                'fix_version': '1.2.1',
                'link': 'https://nvd.nist.gov/vuln/detail/CVE-2023-1234',
                'affected_components': ['container-runtime'],
                'exploit_available': True,
                'published_date': '2023-06-15'
            },
            {
                'id': 'CVE-2023-5678',
                'severity': 'HIGH',
                'description': 'Privilege escalation vulnerability in base image',
                'affected_versions': ['2.0.0-2.1.0'],
                'fix_version': '2.1.1',
                'link': 'https://nvd.nist.gov/vuln/detail/CVE-2023-5678',
                'affected_components': ['base-image'],
                'exploit_available': False,
                'published_date': '2023-07-20'
            },
            {
                'id': 'CVE-2023-9012',
                'severity': 'MEDIUM',
                'description': 'Information disclosure in package manager',
                'affected_versions': ['3.0.0-3.0.5'],
                'fix_version': '3.0.6',
                'link': 'https://nvd.nist.gov/vuln/detail/CVE-2023-9012',
                'affected_components': ['package-manager'],
                'exploit_available': False,
                'published_date': '2023-08-10'
            }
        ]
        
        # In a real implementation, we would:
        # 1. Extract the image digest
        # 2. Query vulnerability databases
        # 3. Parse and analyze the results
        # 4. Return actual CVEs found
        
        # For demo, return random subset of mock CVEs
        import random
        return random.sample(common_cves, random.randint(1, len(common_cves)))
