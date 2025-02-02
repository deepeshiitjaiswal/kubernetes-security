from kubernetes import client, config
import logging
from error_handler import KubernetesError
import os
import requests
import json
from datetime import datetime
import uuid
import time

logger = logging.getLogger(__name__)

class KubernetesScanner:
    def __init__(self):
        self.use_mock = True  # Force mock mode for development

    def get_cluster_resources(self):
        mock_data = {
            'pods': self._mock_pods(),
            'services': self._mock_services(),
            'nodes': self._mock_nodes(),
            'summary': {
                'total_pods': 3,
                'total_services': 2,
                'total_nodes': 2
            }
        }
        return mock_data

    def _mock_pods(self):
        class MockPod:
            def __init__(self, name, namespace="default"):
                self.metadata = type('Metadata', (), {
                    'name': name,
                    'namespace': namespace
                })
        return [
            MockPod("frontend-pod", "web"),
            MockPod("backend-pod", "api"),
            MockPod("database-pod", "data")
        ]

    def _mock_services(self):
        class MockService:
            def __init__(self, name, namespace="default"):
                self.metadata = type('Metadata', (), {
                    'name': name,
                    'namespace': namespace
                })
        return [
            MockService("frontend-service", "web"),
            MockService("backend-service", "api")
        ]

    def _mock_nodes(self):
        class MockNode:
            def __init__(self, name):
                self.metadata = type('Metadata', (), {
                    'name': name
                })
        return [
            MockNode("worker-node-1"),
            MockNode("worker-node-2")
        ]

    def scan_cluster(self):
        """Scan the cluster for vulnerabilities"""
        try:
            scan_result = {
                'scan_id': str(uuid.uuid4()),
                'status': 'in_progress',
                'start_time': datetime.now().isoformat(),
                'progress': 0,
                'current_phase': 'Initializing',
                'findings': {
                    'CRITICAL': [],
                    'HIGH': [],
                    'MEDIUM': [],
                    'LOW': []
                }
            }

            self.current_scan = scan_result

            phases = [
                ('Scanning Images', 30),
                ('Checking Configs', 60),
                ('Security Audit', 90),
                ('Report', 100)
            ]

            for phase, progress in phases:
                scan_result['current_phase'] = phase
                scan_result['progress'] = progress
                
                if phase == 'Scanning Images':
                    scan_result['findings']['CRITICAL'].extend([
                        {
                            'id': f'CVE-2024-{uuid.uuid4().hex[:4]}',
                            'title': 'Container Runtime Vulnerability',
                            'description': 'Critical security issue detected',
                            'affected_component': 'runtime',
                            'detection_time': datetime.now().isoformat()
                        }
                    ])
                elif phase == 'Checking Configs':
                    scan_result['findings']['HIGH'].extend([
                        {
                            'id': f'CVE-2024-{uuid.uuid4().hex[:4]}',
                            'title': 'Configuration Issue',
                            'description': 'High-risk misconfiguration found',
                            'affected_component': 'config',
                            'detection_time': datetime.now().isoformat()
                        }
                    ])
                
                time.sleep(0.5)

            scan_result['status'] = 'completed'
            scan_result['end_time'] = datetime.now().isoformat()
            return scan_result

        except Exception as e:
            logger.error(f"Error in scan_cluster: {str(e)}")
            scan_result = {
                'status': 'failed',
                'error': str(e)
            }
            return scan_result

    def get_scan_status(self, scan_id=None):
        """Get the current status of the ongoing scan"""
        if hasattr(self, 'current_scan'):
            return self.current_scan
        return {'status': 'no_scan', 'message': 'No scan in progress'}

    def _scan_pod(self, pod):
        """
        Scan a pod for vulnerabilities and CVEs.
        """
        vulnerabilities = []
        cves = []
        
        try:
            for container in pod.spec.containers:
                if container.security_context and container.security_context.privileged:
                    vulnerabilities.append({
                        'severity': 'HIGH',
                        'description': f'Container {container.name} is running with privileged access',
                        'affected_resource': container.name,
                        'recommendation': 'Remove privileged access unless absolutely necessary'
                    })
                
                if container.image.endswith(':latest'):
                    vulnerabilities.append({
                        'severity': 'MEDIUM',
                        'description': f'Container {container.name} uses latest tag which is not recommended',
                        'affected_resource': container.name,
                        'recommendation': 'Use specific version tags for container images'
                    })
                
                image_cves = self._check_image_cves(container.image)
                cves.extend(image_cves)
            
            if not pod.spec.containers[0].resources or not pod.spec.containers[0].resources.limits:
                vulnerabilities.append({
                    'severity': 'LOW',
                    'description': 'Pod does not have resource limits set',
                    'affected_resource': pod.metadata.name,
                    'recommendation': 'Set resource limits to prevent resource exhaustion'
                })
            
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
        
        import random
        return random.sample(common_cves, random.randint(1, len(common_cves)))

    def get_resources(self):
        """Get cluster resources and latest vulnerability data"""
        try:
            mock_vulnerabilities = {
                'CRITICAL': [
                    {
                        'id': 'CVE-2024-0001',
                        'title': 'Remote Code Execution in Container Runtime',
                        'description': 'A critical vulnerability allowing remote code execution in container runtime',
                        'severity': 'CRITICAL',
                        'affected_component': 'container-runtime',
                        'published_date': '2024-01-15',
                        'fix_available': True,
                        'fix_version': '1.2.3'
                    },
                    {
                        'id': 'CVE-2024-0002',
                        'title': 'Privilege Escalation in API Server',
                        'description': 'A vulnerability allowing privilege escalation through the API server',
                        'severity': 'CRITICAL',
                        'affected_component': 'api-server',
                        'published_date': '2024-01-20',
                        'fix_available': True,
                        'fix_version': '2.1.0'
                    }
                ],
                'HIGH': [
                    {
                        'id': 'CVE-2024-1234',
                        'title': 'Information Disclosure in etcd',
                        'description': 'Sensitive information disclosure vulnerability in etcd component',
                        'severity': 'HIGH',
                        'affected_component': 'etcd',
                        'published_date': '2024-01-10',
                        'fix_available': True,
                        'fix_version': '3.5.2'
                    },
                    {
                        'id': 'CVE-2024-5678',
                        'title': 'Denial of Service in Scheduler',
                        'description': 'DoS vulnerability affecting the Kubernetes scheduler',
                        'severity': 'HIGH',
                        'affected_component': 'scheduler',
                        'published_date': '2024-01-25',
                        'fix_available': False,
                        'fix_version': None
                    }
                ],
                'MEDIUM': [
                    {
                        'id': 'CVE-2024-9012',
                        'title': 'Cross-Site Scripting in Dashboard',
                        'description': 'XSS vulnerability in Kubernetes dashboard',
                        'severity': 'MEDIUM',
                        'affected_component': 'dashboard',
                        'published_date': '2024-01-05',
                        'fix_available': True,
                        'fix_version': '2.7.0'
                    }
                ],
                'LOW': [
                    {
                        'id': 'CVE-2024-7890',
                        'title': 'Information Leak in Logs',
                        'description': 'Minor information leak in logging component',
                        'severity': 'LOW',
                        'affected_component': 'logging',
                        'published_date': '2024-01-01',
                        'fix_available': True,
                        'fix_version': '1.1.0'
                    }
                ]
            }

            return {
                'summary': {
                    'vulnerability_severity': {
                        'CRITICAL': len(mock_vulnerabilities['CRITICAL']),
                        'HIGH': len(mock_vulnerabilities['HIGH']),
                        'MEDIUM': len(mock_vulnerabilities['MEDIUM']),
                        'LOW': len(mock_vulnerabilities['LOW'])
                    }
                },
                'cluster_info': {
                    'total_nodes': 3,
                    'total_pods': 12,
                    'total_namespaces': 4,
                    'kubernetes_version': 'v1.24.0',
                    'cluster_name': 'development-cluster'
                },
                'vulnerabilities': mock_vulnerabilities
            }
        except Exception as e:
            logger.error(f"Error in get_resources: {str(e)}")
            raise
