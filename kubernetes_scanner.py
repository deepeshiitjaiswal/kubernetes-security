from kubernetes import client, config
import logging
from datetime import datetime
import threading
import json
import requests
from collections import defaultdict
import concurrent.futures

logger = logging.getLogger(__name__)

class KubernetesScanner:
    def __init__(self):
        try:
            config.load_kube_config()
            self.v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
            self._scan_status = {
                'status': 'idle',
                'progress': 0,
                'last_scan': None
            }
            self._lock = threading.Lock()
            self._scan_cache = {}
            self._cache_timeout = 300  # 5 minutes
        except Exception as e:
            logger.error(f"Failed to initialize Kubernetes client: {str(e)}")
            raise

    def scan_cluster(self):
        """
        Perform a security scan of the Kubernetes cluster
        """
        try:
            # Check cache first
            current_time = datetime.now().timestamp()
            if self._scan_cache and (current_time - self._scan_cache.get('timestamp', 0) < self._cache_timeout):
                return self._scan_cache['results']

            with self._lock:
                self._scan_status['status'] = 'running'
                self._scan_status['progress'] = 0

            # Get all pods in the cluster
            pods = self.v1.list_pod_for_all_namespaces().items
            total_pods = len(pods)
            
            # Prepare scan results structure
            scan_results = {
                'vulnerabilities': {
                    'CRITICAL': [],
                    'HIGH': [],
                    'MEDIUM': [],
                    'LOW': []
                },
                'pods': [],
                'cves': []
            }

            # Use ThreadPoolExecutor for parallel scanning
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                future_to_pod = {executor.submit(self._scan_pod, pod): pod for pod in pods}
                completed = 0

                for future in concurrent.futures.as_completed(future_to_pod):
                    pod = future_to_pod[future]
                    try:
                        pod_result = future.result()
                        if pod_result:
                            scan_results['pods'].append(pod_result)
                            # Update CVEs
                            for vuln in pod_result.get('vulnerabilities', []):
                                if vuln.get('cves'):
                                    for cve_id in vuln['cves']:
                                        cve_info = self._get_cve_info(cve_id)
                                        if cve_info and cve_info not in scan_results['cves']:
                                            scan_results['cves'].append(cve_info)
                                            scan_results['vulnerabilities'][cve_info['severity']].append(cve_id)

                    except Exception as e:
                        logger.error(f"Error scanning pod {pod.metadata.name}: {str(e)}")

                    completed += 1
                    progress = (completed / total_pods) * 100
                    with self._lock:
                        self._scan_status['progress'] = progress

            # Cache the results
            self._scan_cache = {
                'timestamp': current_time,
                'results': scan_results
            }

            # Update final status
            with self._lock:
                self._scan_status['status'] = 'completed'
                self._scan_status['progress'] = 100
                self._scan_status['last_scan'] = datetime.now().isoformat()

            return scan_results

        except Exception as e:
            logger.error(f"Error during cluster scan: {str(e)}")
            with self._lock:
                self._scan_status['status'] = 'error'
            raise

    def _scan_pod(self, pod):
        """
        Scan a single pod and its containers
        """
        try:
            vulnerabilities = []
            
            # Check pod-level security
            if not pod.spec.security_context or not pod.spec.security_context.run_as_non_root:
                vulnerabilities.append({
                    'affected_resource': 'Security Context',
                    'description': 'Pod running as root',
                    'severity': 'HIGH',
                    'recommendation': 'Configure pod to run as non-root user',
                    'cves': ['CVE-2024-0001']
                })

            # Check each container
            for container in pod.spec.containers:
                container_vulns = self._scan_container(container)
                vulnerabilities.extend(container_vulns)

            return {
                'name': pod.metadata.name,
                'namespace': pod.metadata.namespace,
                'vulnerabilities': vulnerabilities,
                'cves': list(set([cve for vuln in vulnerabilities for cve in vuln.get('cves', [])]))
            }

        except Exception as e:
            logger.error(f"Error scanning pod {pod.metadata.name}: {str(e)}")
            return None

    def _scan_container(self, container):
        """
        Scan a container for vulnerabilities
        """
        vulnerabilities = []

        # Check privileged mode
        if container.security_context and container.security_context.privileged:
            vulnerabilities.append({
                'affected_resource': 'Container Security',
                'description': 'Container running in privileged mode',
                'severity': 'CRITICAL',
                'recommendation': 'Disable privileged mode',
                'cves': ['CVE-2024-0002']
            })

        # Check resource limits
        if not container.resources or not container.resources.limits:
            vulnerabilities.append({
                'affected_resource': 'Resource Management',
                'description': 'No resource limits defined',
                'severity': 'MEDIUM',
                'recommendation': 'Set resource limits',
                'cves': ['CVE-2024-9012']
            })

        # Check read-only root filesystem
        if not (container.security_context and container.security_context.read_only_root_filesystem):
            vulnerabilities.append({
                'affected_resource': 'Filesystem Security',
                'description': 'Writable root filesystem',
                'severity': 'MEDIUM',
                'recommendation': 'Enable read-only root filesystem',
                'cves': ['CVE-2024-7777']
            })

        return vulnerabilities

    def _get_cve_info(self, cve_id):
        """
        Get CVE information (simulated for demo)
        """
        cve_database = {
            'CVE-2024-0001': {
                'id': 'CVE-2024-0001',
                'severity': 'CRITICAL',
                'description': 'Remote code execution vulnerability in container runtime that allows attackers to escape container isolation and execute arbitrary commands on the host system.',
                'affected_components': ['containerd', 'docker'],
                'fix_version': '1.2.3',
                'published_date': '2024-01-15T00:00:00Z',
                'attack_vector': 'Network',
                'mitigation': 'Update container runtime to latest version and apply security patches',
                'link': f'https://nvd.nist.gov/vuln/detail/{cve_id}'
            },
            'CVE-2024-0002': {
                'id': 'CVE-2024-0002',
                'severity': 'CRITICAL',
                'description': 'Buffer overflow vulnerability in kubelet allows privilege escalation from compromised pods to gain root access on worker nodes.',
                'affected_components': ['kubelet'],
                'fix_version': '1.29.1',
                'published_date': '2024-01-18T00:00:00Z',
                'attack_vector': 'Local',
                'mitigation': 'Upgrade kubelet to version 1.29.1 or later',
                'link': f'https://nvd.nist.gov/vuln/detail/{cve_id}'
            },
            'CVE-2024-9012': {
                'id': 'CVE-2024-9012',
                'severity': 'MEDIUM',
                'description': 'Memory leak in container orchestration system leads to resource exhaustion and potential denial of service.',
                'affected_components': ['kubernetes'],
                'fix_version': '1.0.1',
                'published_date': '2024-01-30T00:00:00Z',
                'attack_vector': 'Local',
                'mitigation': 'Implement resource limits and regular container restarts',
                'link': f'https://nvd.nist.gov/vuln/detail/{cve_id}'
            },
            'CVE-2024-7777': {
                'id': 'CVE-2024-7777',
                'severity': 'MEDIUM',
                'description': 'Insecure file permissions in configuration files expose sensitive information to unauthorized users.',
                'affected_components': ['config-manager'],
                'fix_version': '3.0.2',
                'published_date': '2024-01-24T00:00:00Z',
                'attack_vector': 'Local',
                'mitigation': 'Update file permissions and implement proper access controls',
                'link': f'https://nvd.nist.gov/vuln/detail/{cve_id}'
            }
        }
        return cve_database.get(cve_id)

    def get_scan_status(self):
        """
        Get the current scan status
        """
        with self._lock:
            return self._scan_status.copy()
