from kubernetes import client, config
import logging
from datetime import datetime
import threading
import json
import requests
from collections import defaultdict
import concurrent.futures
import os
import random
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KubernetesScanner:
    def __init__(self):
        self._scan_status = {
            'status': 'idle',
            'progress': 0,
            'last_scan': None,
            'message': '',
            'error': None
        }
        self._lock = threading.Lock()
        self._initialize_kubernetes_client()

    def _initialize_kubernetes_client(self):
        """Initialize Kubernetes client with fallback options"""
        try:
            # Try loading from default location
            config.load_kube_config()
            logger.info("Successfully loaded kube config from default location")
            self.v1 = client.CoreV1Api()
            # Test connection
            self.v1.list_namespace(limit=1)
            logger.info("Successfully connected to Kubernetes cluster using kube config")
            return
        except Exception as e:
            logger.warning(f"Could not load kube config: {str(e)}")

        try:
            # Try loading from service account
            config.load_incluster_config()
            logger.info("Successfully loaded in-cluster config")
            self.v1 = client.CoreV1Api()
            # Test connection
            self.v1.list_namespace(limit=1)
            logger.info("Successfully connected to Kubernetes cluster using in-cluster config")
            return
        except Exception as e:
            logger.warning(f"Could not load in-cluster config: {str(e)}")

        # If we reach here, we'll use mock data for demo purposes
        logger.warning("Could not connect to Kubernetes cluster. Using mock data for demonstration.")
        self.use_mock_data = True

    def scan_cluster(self):
        """Perform a security scan of the Kubernetes cluster"""
        try:
            with self._lock:
                self._scan_status.update({
                    'status': 'running',
                    'progress': 5,
                    'message': 'Initializing scan...',
                    'error': None
                })

            # Use mock data if no Kubernetes connection
            if hasattr(self, 'use_mock_data') and self.use_mock_data:
                return self._mock_cluster_scan()

            # Phase 1: Get namespaces (5% - 10%)
            try:
                namespaces = self.v1.list_namespace()
                logger.info(f"Found {len(namespaces.items)} namespaces")
                with self._lock:
                    self._scan_status.update({
                        'progress': 10,
                        'message': f'Found {len(namespaces.items)} namespaces'
                    })
            except Exception as e:
                logger.error(f"Error listing namespaces: {str(e)}")
                return self._mock_cluster_scan()

            # Phase 2: Get pods (10% - 15%)
            try:
                pods = self.v1.list_pod_for_all_namespaces()
                total_pods = len(pods.items)
                logger.info(f"Found {total_pods} pods to scan")
                with self._lock:
                    self._scan_status.update({
                        'progress': 15,
                        'message': f'Found {total_pods} pods to scan'
                    })
            except Exception as e:
                logger.error(f"Error listing pods: {str(e)}")
                return self._mock_cluster_scan()

            # Continue with the rest of the scan...
            return self._process_pods(pods.items)

        except Exception as e:
            error_msg = f"Error during cluster scan: {str(e)}"
            logger.error(error_msg)
            with self._lock:
                self._scan_status.update({
                    'status': 'error',
                    'error': error_msg,
                    'message': 'Scan failed',
                    'progress': 0
                })
            raise

    def _mock_cluster_scan(self):
        """Generate mock scan data for demonstration"""
        try:
            # Simulate scanning progress
            with self._lock:
                self._scan_status.update({
                    'progress': 10,
                    'message': 'Found mock namespaces'
                })

            time.sleep(1)  # Simulate work

            with self._lock:
                self._scan_status.update({
                    'progress': 20,
                    'message': 'Found mock pods'
                })

            # Generate mock pods
            mock_pods = [
                {
                    'name': 'nginx-pod',
                    'namespace': 'default',
                    'containers': [{'name': 'nginx', 'image': 'nginx:latest'}]
                },
                {
                    'name': 'mysql-pod',
                    'namespace': 'database',
                    'containers': [{'name': 'mysql', 'image': 'mysql:8.0'}]
                },
                {
                    'name': 'redis-pod',
                    'namespace': 'cache',
                    'containers': [{'name': 'redis', 'image': 'redis:6'}]
                }
            ]

            # Process mock pods
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

            total_pods = len(mock_pods)
            for i, pod_data in enumerate(mock_pods):
                progress = 20 + ((i + 1) / total_pods * 60)  # Progress from 20% to 80%
                with self._lock:
                    self._scan_status.update({
                        'progress': progress,
                        'message': f'Scanning pod {i + 1}/{total_pods} ({pod_data["name"]})'
                    })

                # Generate vulnerabilities for each pod
                pod_result = {
                    'name': pod_data['name'],
                    'namespace': pod_data['namespace'],
                    'containers': [],
                    'vulnerabilities': []
                }

                for container in pod_data['containers']:
                    vulns = self._mock_vulnerability_scan(container['image'])
                    if vulns:
                        pod_result['vulnerabilities'].extend(vulns)
                        for vuln in vulns:
                            for cve_id in vuln['cves']:
                                cve_info = self._get_cve_info(cve_id)
                                if cve_info:
                                    if cve_info not in scan_results['cves']:
                                        scan_results['cves'].append(cve_info)
                                    severity = cve_info['severity']
                                    if cve_id not in scan_results['vulnerabilities'][severity]:
                                        scan_results['vulnerabilities'][severity].append(cve_id)

                scan_results['pods'].append(pod_result)

            # Finalize
            with self._lock:
                self._scan_status.update({
                    'status': 'completed',
                    'progress': 100,
                    'last_scan': datetime.now().isoformat(),
                    'message': f'Scan completed. Found {len(scan_results["cves"])} vulnerabilities across {len(scan_results["pods"])} pods.'
                })

            return scan_results

        except Exception as e:
            error_msg = f"Error during mock scan: {str(e)}"
            logger.error(error_msg)
            with self._lock:
                self._scan_status.update({
                    'status': 'error',
                    'error': error_msg,
                    'message': 'Mock scan failed',
                    'progress': 0
                })
            raise

    def _process_pods(self, pods):
        """
        Process pods and scan for vulnerabilities
        """
        try:
            # Phase 3: Prepare scan (15% - 20%)
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

            with self._lock:
                self._scan_status.update({
                    'progress': 20,
                    'message': 'Starting pod security scan...'
                })

            # Phase 4: Scan pods (20% - 90%)
            completed = 0
            for pod in pods:
                try:
                    logger.info(f"Scanning pod: {pod.metadata.name}")
                    pod_result = self._scan_pod(pod)
                    
                    if pod_result:
                        scan_results['pods'].append(pod_result)
                        # Update CVEs and vulnerabilities
                        for vuln in pod_result.get('vulnerabilities', []):
                            if vuln.get('cves'):
                                for cve_id in vuln['cves']:
                                    cve_info = self._get_cve_info(cve_id)
                                    if cve_info:
                                        if cve_info not in scan_results['cves']:
                                            scan_results['cves'].append(cve_info)
                                        severity = cve_info['severity']
                                        if cve_id not in scan_results['vulnerabilities'][severity]:
                                            scan_results['vulnerabilities'][severity].append(cve_id)
                    
                    completed += 1
                    progress = 20 + (completed / len(pods) * 70)  # Progress from 20% to 90%
                    
                    with self._lock:
                        self._scan_status.update({
                            'progress': progress,
                            'message': f'Scanning pods: {completed}/{len(pods)} ({pod.metadata.name})'
                        })
                        
                except Exception as e:
                    logger.error(f"Error scanning pod {pod.metadata.name}: {str(e)}")

            # Phase 5: Process results (90% - 100%)
            with self._lock:
                self._scan_status.update({
                    'progress': 95,
                    'message': 'Processing scan results...'
                })

            # Finalize
            current_time = datetime.now()
            with self._lock:
                self._scan_status.update({
                    'status': 'completed',
                    'progress': 100,
                    'last_scan': current_time.isoformat(),
                    'message': f'Scan completed. Found {len(scan_results["cves"])} vulnerabilities across {len(scan_results["pods"])} pods.'
                })

            logger.info("Scan completed successfully")
            return scan_results

        except Exception as e:
            error_msg = f"Error during cluster scan: {str(e)}"
            logger.error(error_msg)
            with self._lock:
                self._scan_status.update({
                    'status': 'error',
                    'error': error_msg,
                    'message': 'Scan failed',
                    'progress': 0
                })
            raise

    def _scan_pod(self, pod):
        """
        Scan a single pod for vulnerabilities
        """
        try:
            pod_info = {
                'name': pod.metadata.name,
                'namespace': pod.metadata.namespace,
                'containers': [],
                'vulnerabilities': []
            }

            # Scan each container in the pod
            for container in pod.spec.containers:
                container_info = {
                    'name': container.name,
                    'image': container.image,
                    'vulnerabilities': []
                }

                # Mock vulnerability scan - replace with actual scanner
                mock_vulnerabilities = self._mock_vulnerability_scan(container.image)
                if mock_vulnerabilities:
                    container_info['vulnerabilities'].extend(mock_vulnerabilities)
                    pod_info['vulnerabilities'].extend(mock_vulnerabilities)

                pod_info['containers'].append(container_info)

            return pod_info
        except Exception as e:
            logger.error(f"Error scanning pod {pod.metadata.name}: {str(e)}")
            return None

    def _mock_vulnerability_scan(self, image):
        """
        Mock vulnerability scan for demo purposes
        Replace this with actual vulnerability scanner integration
        """
        vulnerabilities = []
        
        # Common critical vulnerabilities
        if random.random() < 0.4:  # 40% chance for critical vulnerabilities
            vulnerabilities.extend([
                {
                    'name': 'remote-code-execution',
                    'severity': 'CRITICAL',
                    'description': 'Remote code execution vulnerability in container runtime',
                    'cves': ['CVE-2024-1234']
                },
                {
                    'name': 'privilege-escalation',
                    'severity': 'CRITICAL',
                    'description': 'Privilege escalation vulnerability in container',
                    'cves': ['CVE-2024-5678']
                }
            ])
        
        # Image specific vulnerabilities
        if 'nginx' in image.lower():
            vulnerabilities.extend([
                {
                    'name': 'nginx-rce-vuln',
                    'severity': 'CRITICAL',
                    'description': 'Remote code execution vulnerability in nginx',
                    'cves': ['CVE-2024-9012']
                },
                {
                    'name': 'nginx-info-disclosure',
                    'severity': 'HIGH',
                    'description': 'Information disclosure vulnerability in nginx',
                    'cves': ['CVE-2024-3456']
                }
            ])
        elif 'mysql' in image.lower():
            vulnerabilities.extend([
                {
                    'name': 'mysql-auth-bypass',
                    'severity': 'CRITICAL',
                    'description': 'Authentication bypass vulnerability in MySQL',
                    'cves': ['CVE-2024-7890']
                },
                {
                    'name': 'mysql-data-leak',
                    'severity': 'HIGH',
                    'description': 'Data leak vulnerability in MySQL',
                    'cves': ['CVE-2024-4567']
                }
            ])
        elif 'redis' in image.lower():
            vulnerabilities.extend([
                {
                    'name': 'redis-rce',
                    'severity': 'CRITICAL',
                    'description': 'Remote code execution in Redis',
                    'cves': ['CVE-2024-8901']
                },
                {
                    'name': 'redis-auth-bypass',
                    'severity': 'HIGH',
                    'description': 'Authentication bypass in Redis',
                    'cves': ['CVE-2024-2345']
                }
            ])

        # Common vulnerabilities for all containers
        if random.random() < 0.5:  # 50% chance
            vulnerabilities.extend([
                {
                    'name': 'container-escape',
                    'severity': 'CRITICAL',
                    'description': 'Container escape vulnerability',
                    'cves': ['CVE-2024-0001']
                },
                {
                    'name': 'kernel-vulnerability',
                    'severity': 'HIGH',
                    'description': 'Kernel vulnerability in container runtime',
                    'cves': ['CVE-2024-0002']
                }
            ])

        return vulnerabilities

    def _get_cve_info(self, cve_id):
        """
        Get detailed information about a CVE
        """
        try:
            # Mock CVE data with more critical vulnerabilities
            mock_cve_data = {
                'CVE-2024-1234': {
                    'id': 'CVE-2024-1234',
                    'severity': 'CRITICAL',
                    'description': 'Remote code execution vulnerability allowing unauthorized access',
                    'attack_vector': 'Network',
                    'fix_version': '2.0.0',
                    'published_date': '2024-01-15',
                    'link': f'https://nvd.nist.gov/vuln/detail/CVE-2024-1234',
                    'mitigation': 'Upgrade to version 2.0.0 or apply security patch'
                },
                'CVE-2024-5678': {
                    'id': 'CVE-2024-5678',
                    'severity': 'CRITICAL',
                    'description': 'Privilege escalation vulnerability allowing root access',
                    'attack_vector': 'Local',
                    'fix_version': '1.5.0',
                    'published_date': '2024-01-20',
                    'link': f'https://nvd.nist.gov/vuln/detail/CVE-2024-5678',
                    'mitigation': 'Apply latest security patches'
                },
                'CVE-2024-9012': {
                    'id': 'CVE-2024-9012',
                    'severity': 'CRITICAL',
                    'description': 'Remote code execution in web server',
                    'attack_vector': 'Network',
                    'fix_version': '1.20.0',
                    'published_date': '2024-01-25',
                    'link': f'https://nvd.nist.gov/vuln/detail/CVE-2024-9012',
                    'mitigation': 'Update to latest version'
                },
                'CVE-2024-7890': {
                    'id': 'CVE-2024-7890',
                    'severity': 'CRITICAL',
                    'description': 'Authentication bypass vulnerability in database server',
                    'attack_vector': 'Network',
                    'fix_version': '8.0.35',
                    'published_date': '2024-01-30',
                    'link': f'https://nvd.nist.gov/vuln/detail/CVE-2024-7890',
                    'mitigation': 'Apply security patches'
                },
                'CVE-2024-8901': {
                    'id': 'CVE-2024-8901',
                    'severity': 'CRITICAL',
                    'description': 'Remote code execution in cache server',
                    'attack_vector': 'Network',
                    'fix_version': '6.2.0',
                    'published_date': '2024-02-01',
                    'link': f'https://nvd.nist.gov/vuln/detail/CVE-2024-8901',
                    'mitigation': 'Update to latest version'
                },
                'CVE-2024-0001': {
                    'id': 'CVE-2024-0001',
                    'severity': 'CRITICAL',
                    'description': 'Container escape vulnerability allowing host system access',
                    'attack_vector': 'Container',
                    'fix_version': '1.0.0',
                    'published_date': '2024-02-02',
                    'link': f'https://nvd.nist.gov/vuln/detail/CVE-2024-0001',
                    'mitigation': 'Update container runtime'
                },
                'CVE-2024-3456': {
                    'id': 'CVE-2024-3456',
                    'severity': 'HIGH',
                    'description': 'Information disclosure in web server',
                    'attack_vector': 'Network',
                    'fix_version': '1.18.0',
                    'published_date': '2024-01-22',
                    'link': f'https://nvd.nist.gov/vuln/detail/CVE-2024-3456',
                    'mitigation': 'Apply security patches'
                },
                'CVE-2024-4567': {
                    'id': 'CVE-2024-4567',
                    'severity': 'HIGH',
                    'description': 'Data leak vulnerability in database',
                    'attack_vector': 'Network',
                    'fix_version': '8.0.34',
                    'published_date': '2024-01-28',
                    'link': f'https://nvd.nist.gov/vuln/detail/CVE-2024-4567',
                    'mitigation': 'Update to latest version'
                },
                'CVE-2024-2345': {
                    'id': 'CVE-2024-2345',
                    'severity': 'HIGH',
                    'description': 'Authentication bypass in cache system',
                    'attack_vector': 'Network',
                    'fix_version': '6.1.0',
                    'published_date': '2024-01-18',
                    'link': f'https://nvd.nist.gov/vuln/detail/CVE-2024-2345',
                    'mitigation': 'Apply security patches'
                },
                'CVE-2024-0002': {
                    'id': 'CVE-2024-0002',
                    'severity': 'HIGH',
                    'description': 'Kernel vulnerability in container runtime',
                    'attack_vector': 'Local',
                    'fix_version': '5.15.0',
                    'published_date': '2024-02-01',
                    'link': f'https://nvd.nist.gov/vuln/detail/CVE-2024-0002',
                    'mitigation': 'Update kernel and apply patches'
                }
            }

            return mock_cve_data.get(cve_id)
        except Exception as e:
            logger.error(f"Error getting CVE info for {cve_id}: {str(e)}")
            return None

    def get_scan_status(self):
        """
        Get the current scan status
        """
        with self._lock:
            return self._scan_status.copy()
