""" Module that contains script for deploying HA cluster """
import sys
import json
import getopt
from os import system
from time import sleep
from os import makedirs
from subprocess import call
from subprocess import check_output

hosts_content = ''' 
[OSEv3:vars]

###########################################################################
### Ansible Vars
###########################################################################
timeout=60
ansible_user=ec2-user
ansible_become=yes

openshift_deployment_type=openshift-enterprise

containerized=false

###########################################################################
### OpenShift Basic Vars
###########################################################################

openshift_disable_check="disk_availability,memory_availability,docker_image_availability"

oreg_url=registry.access.redhat.com/openshift3/ose-${component}:${version}
openshift_examples_modify_imagestreams=true

penshift_enable_unsupported_configurations=True

openshift_node_groups=[{'name': 'node-config-master', 'labels': ['node-role.kubernetes.io/master=true','runtime=docker']}, {'name': 'node-config-infra', 'labels': ['node-role.kubernetes.io/infra=true','runtime=docker']}, {'name': 'node-config-glusterfs', 'labels': ['runtime=docker']}, {'name': 'node-config-compute', 'labels': ['node-role.kubernetes.io/compute=true','runtime=docker'], 'edits': [{ 'key': 'kubeletArguments.pods-per-core','value': ['20']}]}]
# Configure node kubelet arguments. pods-per-core is valid in OpenShift Origin 1.3 or OpenShift Container Platform 3.3 and later. -> These  need to go into the above
# openshift_node_kubelet_args={'pods-per-core': ['10'], 'max-pods': ['250'], 'image-gc-high-threshold': ['85'], 'image-gc-low-threshold': ['75']}

# Configure logrotate scripts
# See: https://github.com/nickhammond/ansible-logrotate
logrotate_scripts=[{"name": "syslog", "path": "/var/log/cron\\n/var/log/maillog\\n/var/log/messages\\n/var/log/secure\\n/var/log/spooler\\n", "options": ["daily", "rotate 7","size 500M", "compress", "sharedscripts", "missingok"], "scripts": {"postrotate": "/bin/kill -HUP `cat /var/run/syslogd.pid 2> /dev/null` 2> /dev/null || true"}}]

###########################################################################
### OpenShift Master Vars
###########################################################################

openshift_master_api_port=443
openshift_master_console_port=443

openshift_master_cluster_method=native
openshift_master_cluster_hostname=loadbalancer1.5414.internal
openshift_master_cluster_public_hostname=loadbalancer1.5414.example.opentlc.com
openshift_master_default_subdomain=apps.5414.example.opentlc.com
openshift_master_overwrite_named_certificates=True

openshift_enable_unsupported_configurations=True
os_sdn_network_plugin_name='redhat/openshift-ovs-multitenant'


##########################################################################
### OpenShift Authentication Vars
###########################################################################

# htpasswd Authentication
openshift_master_identity_providers=[{'name': 'htpasswd_auth', 'login': 'true', 'challenge': 'true', 'kind': 'HTPasswdPasswordIdentityProvider'}]
openshift_master_htpasswd_file=/root/htpasswd.openshift


###########################################################################
### OpenShift Router and Registry Vars
###########################################################################

openshift_hosted_router_replicas=2

openshift_hosted_registry_replicas=1
openshift_hosted_registry_storage_kind=nfs
openshift_hosted_registry_storage_access_modes=['ReadWriteMany']
openshift_hosted_registry_storage_nfs_directory=/srv/nfs
openshift_hosted_registry_storage_nfs_options='*(rw,root_squash)'
openshift_hosted_registry_storage_volume_name=registry
openshift_hosted_registry_storage_volume_size=20Gi
openshift_hosted_registry_pullthrough=true
openshift_hosted_registry_acceptschema2=true
openshift_hosted_registry_enforcequota=true

###########################################################################
#### OpenShift Service Catalog Vars
############################################################################

openshift_enable_service_catalog=true

template_service_broker_install=true
openshift_template_service_broker_namespaces=['openshift']

ansible_service_broker_install=true
ansible_service_broker_local_registry_whitelist=['.*-apb$']

openshift_hosted_etcd_storage_kind=nfs
openshift_hosted_etcd_storage_nfs_options="*(rw,root_squash,sync,no_wdelay)"
openshift_hosted_etcd_storage_nfs_directory=/srv/nfs
openshift_hosted_etcd_storage_labels={'storage': 'etcd-asb'}
openshift_hosted_etcd_storage_volume_name=etcd-asb
openshift_hosted_etcd_storage_access_modes=['ReadWriteOnce']
openshift_hosted_etcd_storage_volume_size=10G

############################################################################
#### OpenShift Metrics and Logging Vars
############################################################################

#Enable cluster metrics
openshift_metrics_install_metrics=true

openshift_metrics_storage_kind=nfs
openshift_metrics_storage_access_modes=['ReadWriteOnce']
openshift_metrics_storage_nfs_directory=/srv/nfs
openshift_metrics_storage_nfs_options='*(rw,root_squash)'
openshift_metrics_storage_volume_name=metrics
openshift_metrics_storage_volume_size=10Gi
openshift_metrics_storage_labels={'storage': 'metrics'}

openshift_metrics_heapster_nodeselector={"node-role.kubernetes.io/infra":"true"}
openshift_metrics_cassandra_nodeselector={"node-role.kubernetes.io/infra":"true"}
openshift_metrics_hawkular_nodeselector={"node-role.kubernetes.io/infra":"true"}

# Enable cluster logging
openshift_logging_install_logging=True

openshift_logging_storage_kind=nfs
openshift_logging_storage_access_modes=['ReadWriteOnce']
openshift_logging_storage_nfs_directory=/srv/nfs
openshift_logging_storage_nfs_options='*(rw,root_squash)'
openshift_logging_storage_volume_name=logging
openshift_logging_storage_volume_size=10Gi
openshift_logging_storage_labels={'storage': 'logging'}

# openshift_logging_kibana_hostname=kibana.apps.5414.example.opentlc.com
openshift_logging_es_cluster_size=1
openshift_logging_es_number_of_replicas=1

openshift_logging_es_nodeselector={"node-role.kubernetes.io/infra":"true"}
openshift_logging_kibana_nodeselector={"node-role.kubernetes.io/infra":"true"}
openshift_logging_curator_nodeselector={"node-role.kubernetes.io/infra":"true"}

#########################
# Add Prometheus Metrics:
#########################
openshift_hosted_prometheus_deploy=true
openshift_prometheus_namespace=openshift-metrics
openshift_prometheus_node_selector={"node-role.kubernetes.io/infra":"true"}

# Prometheus
openshift_prometheus_storage_type='pvc'
openshift_prometheus_storage_kind=dynamic
openshift_prometheus_storage_class='glusterfs-storage-block'
openshift_prometheus_storage_volume_size=20Gi
openshift_prometheus_storage_access_modes=['ReadWriteOnce']
openshift_prometheus_storage_volume_name=prometheus

# For prometheus-alertmanager
openshift_prometheus_alertmanager_storage_type='pvc'
openshift_prometheus_alertmanager_storage_kind=dynamic
openshift_prometheus_alertmanager_storage_class='glusterfs-storage-block'
openshift_prometheus_alertmanager_storage_access_modes=['ReadWriteOnce']
openshift_prometheus_alertmanager_storage_volume_size=10Gi
openshift_prometheus_alertmanager_storage_volume_name=prometheus-alertmanager

# For prometheus-alertbuffer
openshift_prometheus_alertbuffer_storage_type='pvc'
openshift_prometheus_alertbuffer_storage_kind=dynamic
openshift_prometheus_alertbuffer_storage_class='glusterfs-storage-block'
openshift_prometheus_alertbuffer_storage_access_modes=['ReadWriteOnce']
openshift_prometheus_alertbuffer_storage_volume_name=prometheus-alertbuffer
openshift_prometheus_alertbuffer_storage_volume_size=10Gi

# Suggested Quotas and limits for Prometheus components:
openshift_prometheus_memory_requests=2Gi
openshift_prometheus_cpu_requests=750m
openshift_prometheus_memory_limit=2Gi
openshift_prometheus_cpu_limit=750m
openshift_prometheus_alertmanager_memory_requests=300Mi
openshift_prometheus_alertmanager_cpu_requests=200m
openshift_prometheus_alertmanager_memory_limit=300Mi
openshift_prometheus_alertmanager_cpu_limit=200m
openshift_prometheus_alertbuffer_memory_requests=300Mi
openshift_prometheus_alertbuffer_cpu_requests=200m
openshift_prometheus_alertbuffer_memory_limit=300Mi
openshift_prometheus_alertbuffer_cpu_limit=200m

##########################################################################
### OpenShift Hosts
###########################################################################
[OSEv3:children]
lb
masters
etcd
nodes
nfs

[lb]
loadbalancer1.5414.internal

[masters]
master1.5414.internal
master2.5414.internal
master3.5414.internal

[etcd]
master1.5414.internal
master2.5414.internal
master3.5414.internal

[nodes]
## These are the masters
master1.5414.internal openshift_node_group_name='node-config-master'
master2.5414.internal openshift_node_group_name='node-config-master'
master3.5414.internal openshift_node_group_name='node-config-master'

## These are infranodes
infranode1.5414.internal openshift_node_group_name='node-config-infra'
infranode2.5414.internal openshift_node_group_name='node-config-infra'

## These are regular nodes
node1.5414.internal openshift_node_group_name='node-config-compute'
node2.5414.internal openshift_node_group_name='node-config-compute'
node3.5414.internal openshift_node_group_name='node-config-compute'
node4.5414.internal openshift_node_group_name='node-config-compute'

## These are OCS nodes
# support1.5414.internal openshift_node_group_name='node-config-compute'

[nfs]
support1.5414.internal
'''

project_template = '''
apiVersion: v1
kind: Template
metadata:
  creationTimestamp: null
  name: project-request
objects:
- apiVersion: "v1"
  kind: "LimitRange"
  metadata:
    name: "${PROJECT_NAME}-core-resource-limits"
  spec:
    limits:
        - type: "Container"
          max:
            memory: 6Gi
          min:
            memory: 10Mi
          default:
            cpu: 500m
            memory: 1.5Gi
          defaultRequest:
            cpu: 50m
            memory: 256Mi
        - type: "Pod"
          max:
            memory: 12Gi
          min:
            memory: 6Mi

- apiVersion: v1
  kind: Project
  metadata:
    annotations:
      openshift.io/description: ${PROJECT_DESCRIPTION}
      openshift.io/display-name: ${PROJECT_DISPLAYNAME}
      openshift.io/requester: ${PROJECT_REQUESTING_USER}
    creationTimestamp: null
    name: ${PROJECT_NAME}
  spec: {}
  status: {}
- apiVersion: v1
  groupNames:
  - system:serviceaccounts:${PROJECT_NAME}
  kind: RoleBinding
  metadata:
    creationTimestamp: null
    name: system:image-pullers
    namespace: ${PROJECT_NAME}
  roleRef:
    name: system:image-puller
  subjects:
  - kind: SystemGroup
    name: system:serviceaccounts:${PROJECT_NAME}
  userNames: null
- apiVersion: v1
  groupNames: null
  kind: RoleBinding
  metadata:
    creationTimestamp: null
    name: system:image-builders
    namespace: ${PROJECT_NAME}
  roleRef:
    name: system:image-builder
  subjects:
  - kind: ServiceAccount
    name: builder
  userNames:
  - system:serviceaccount:${PROJECT_NAME}:builder
- apiVersion: v1
  groupNames: null
  kind: RoleBinding
  metadata:
    creationTimestamp: null
    name: system:deployers
    namespace: ${PROJECT_NAME}
  roleRef:
    name: system:deployer
  subjects:
  - kind: ServiceAccount
    name: deployer
  userNames:
  - system:serviceaccount:${PROJECT_NAME}:deployer
- apiVersion: v1
  groupNames: null
  kind: RoleBinding
  metadata:
    creationTimestamp: null
    name: admin
    namespace: ${PROJECT_NAME}
  roleRef:
    name: admin
  subjects:
  - kind: User
    name: ${PROJECT_ADMIN_USER}
  userNames:
  - ${PROJECT_ADMIN_USER}
parameters:
- name: PROJECT_NAME
- name: PROJECT_DISPLAYNAME
- name: PROJECT_DESCRIPTION
- name: PROJECT_ADMIN_USER
- name: PROJECT_REQUESTING_USER
'''

jenkins_build_config = '''
apiVersion: v1
items:
- kind: "BuildConfig"
  apiVersion: "v1"
  metadata:
    name: "cicd-bc"
  spec:
    strategy:
      type: "JenkinsPipeline"
      jenkinsPipelineStrategy:
        jenkinsfile: |-
          def version, mvnCmd = "mvn -s configuration/cicd-settings-nexus3.xml"
          pipeline {
            agent {
              label 'maven'
            }
            stages {
              stage('Checkout Source') {
                steps {
                  git branch: 'eap-7', url: 'https://github.com/spjkdevoteam/openshift-tasks.git'
                }
              }
              stage('Build App') {
                steps {
                  sh "mvn clean install -DskipTests"
                }
              }
              stage('Test App') {
                steps {
                  sh "mvn test"
                }
              }
              stage('Create Image Builder') {
                when {
                  expression {
                    openshift.withCluster() {
                      openshift.withProject("cicd") {
                        return !openshift.selector("bc", "tasks-bc").exists();
                      }
                    }
                  }
                }
                steps {
                  script {
                    openshift.withCluster() {
                      openshift.withProject("cicd") {
                        openshift.newBuild("--name=tasks-bc", "--image-stream=jboss-eap70-openshift:1.5", "--binary")
                      }
                    }
                  }
                }
              }
              stage('Build Image') {
                steps {
                  sh "rm -rf oc-build && mkdir -p oc-build/deployments && mkdir -p oc-build/configuration"
                  sh "cp target/openshift-tasks.war oc-build/deployments/ROOT.war"
                  sh "cp configuration/*.properties oc-build/configuration"
                  script {
                    openshift.withCluster() {
                      openshift.withProject("cicd") {
                        openshift.selector("bc", "tasks-bc").startBuild("--from-file=oc-build", "--wait")
                      }
                    }
                  }
                }
              }
              stage('Create DEV') {
                when {
                  expression {
                    openshift.withCluster() {
                      openshift.withProject("cicd-dev") {
                        return !openshift.selector('dc', 'tasks-dev').exists()
                      }
                    }
                  }
                }
                steps {
                  script {
                    openshift.withCluster() {
                      openshift.withProject("cicd-dev") {
                        openshift.newApp("tasks-bc:dev", "--name=tasks-dev").narrow('svc').expose()
                        openshift.set("probe dc/tasks-dev --readiness --get-url=http://:8080/ws/demo/healthcheck --initial-delay-seconds=30 --failure-threshold=10 --period-seconds=10")
                        openshift.set("probe dc/tasks-dev --liveness --get-url=http://:8080/ws/demo/healthcheck --initial-delay-seconds=30 --failure-threshold=10 --period-seconds=10")
                      }
                    }
                  }
                }
              }
            
            
            
            
            
            
            
              stage('Promote to TEST') {
                steps {
                  openshiftTag (srcStream: 'tasks-bc', srcTag: 'latest',  namespace: "cicd", destinationNamespace: "cicd-test", destStream: 'tasks-bc', destTag: 'test')
                }
              }
              stage('Create TEST') {
                when {
                  expression {
                    openshift.withCluster() {
                      openshift.withProject("cicd-test") {
                        return !openshift.selector('dc', 'tasks-test').exists()
                      }
                    }
                  }
                }
                steps {
                  script {
                    openshift.withCluster() {
                      openshift.withProject("cicd-test") {
                        openshift.newApp("tasks-bc:test", "--name=tasks-test").narrow('svc').expose()
                        openshift.set("probe dc/tasks-test --readiness --get-url=http://:8080/ws/demo/healthcheck --initial-delay-seconds=30 --failure-threshold=10 --period-seconds=10")
                        openshift.set("probe dc/tasks-test --liveness --get-url=http://:8080/ws/demo/healthcheck --initial-delay-seconds=30 --failure-threshold=10 --period-seconds=10")
                      }
                    }
                  }
                }
              }
            
            
            
            
            
            
              stage('Promote PROD') {
                steps {
                  openshiftTag (srcStream: 'tasks-bc', srcTag: 'latest',  namespace: "cicd", destinationNamespace: "cicd-prod", destStream: 'tasks-bc', destTag: 'prod')
                }
              }
              stage('Create PROD') {
                when {
                  expression {
                    openshift.withCluster() {
                      openshift.withProject("cicd-prod") {
                        return !openshift.selector('dc', 'tasks-prod').exists()
                      }
                    }
                  }
                }
                steps {
                  script {
                    openshift.withCluster() {
                      openshift.withProject("cicd-prod") {
                        openshift.newApp("tasks-bc:prod", "--name=tasks-prod").narrow('svc').expose()
                        openshift.set("probe dc/tasks-prod --readiness --get-url=http://:8080/ws/demo/healthcheck --initial-delay-seconds=30 --failure-threshold=10 --period-seconds=10")
                        openshift.set("probe dc/tasks-prod --liveness --get-url=http://:8080/ws/demo/healthcheck --initial-delay-seconds=30 --failure-threshold=10 --period-seconds=10")
                        openshift.set("resources dc tasks-prod --limits=cpu=300m,memory=512Mi --requests=cpu=100m,memory=256Mi")
                        openshift.selector("dc", "tasks-prod").autoscale("--min 1 --max 10 --cpu-percent=80 --name='tasks-hpa'")
                      }
                    }
                  }
                }
              }
            }
          }

kind: List
metadata: {}
'''


def write_file(content=None, path=None):
    """ Method that writes content to hosts file"""
    if None not in [content, path]:
        with open(path, 'w') as file:
            file.write(content)
            file.close()


def copy_file_to_location(origin=None, destination=None):
    """ Method that copies file """
    if origin is not None and destination is not None:
        print('Copying file {} to {}'.format(origin, destination))
        system('cp {} {}'.format(origin, destination))


def create_directory(path=None):
    """ Method that creates directories for selected path"""
    if path is not None:
        print('Creating directory {}'.format(path))
        makedirs(path)


def get_guid():
    """ Method that returns GUID value"""
    guid = check_output('echo `hostname | cut -d"." -f2`', shell=True)[0:4]
    if guid == '':
        return None
    else:
        return guid


def set_guid_on_all_nodes(guid=None):
    """ Method that sets GUID on all nodes"""
    if guid is not None:
        check = check_output("ansible all -m shell -a 'echo $GUID'", shell=True)
        checks = check.split('\n\n')
        exists = True
        for c in checks:
            if c.split('>>')[0] != '' and c.split('>>')[1] == '' and exists:
                exists = False
        if not exists:
            print('Setting GUID on all nodes! ')
            export = 'echo "export GUID={}" >> $HOME/.bashrc'.format(guid)
            call(export, shell=True)
            call("ansible all -m shell -a '{}'".format(export), shell=True)
        else:
            print('GUID already set on all nodes! ')
    else:
        print('GUID is None! Exit! ')


def commands(fil=None, guid=None):
    """ Method that executes single commands that do not require input """

    def create_users(prefix='', suffix=''):
        """ Method that creates users"""
        for u in ['amy', 'andrew', 'brian', 'betty']:
            call("{}htpasswd -b /etc/origin/master/htpasswd {} p@ss1!{}".format(
                prefix, u, suffix),
                shell=True)

    def create_cluster_resource_quota():
        """ Method that creates cluster resource quota for each user"""

        for u in ['amy', 'andrew', 'brian', 'betty']:
            content = 'oc create clusterquota clusterquota-{} ' \
                      '--project-annotation-selector=openshift.io/requester={} ' \
                      '--hard pods=25 ' \
                      '--hard requests.memory=6Gi ' \
                      '--hard requests.cpu=5 ' \
                      '--hard limits.cpu=25 ' \
                      '--hard limits.memory=40Gi ' \
                      '--hard configmaps=25 ' \
                      '--hard persistentvolumeclaims=25 ' \
                      '--hard services=25'.format(u, u)
            call(content, shell=True)

    installation = [
        'yum -y install atomic-openshift-utils atomic-openshift-clients',
        'ansible-playbook -f 40 /usr/share/ansible/openshift-ansible/playbooks/prerequisites.yml',
        'ansible-playbook -f 40 /usr/share/ansible/openshift-ansible/playbooks/deploy_cluster.yml',
        'ansible masters[0] -b -m fetch -a "src=/root/.kube/config dest=/root/.kube/config flat=yes"'
    ]

    recycler = [
        'ansible nodes -m shell -a "docker pull registry.access.redhat.com/openshift3/ose-recycler:latest"',
        'ansible nodes -m shell -a "docker tag registry.access.redhat.com/openshift3/ose-recycler:latest registry.access.redhat.com/openshift3/ose-recycler:v3.10.34"'
    ]

    multitenancy = [
        "oc new-project common-project --display-name='Common project'",
        "oc new-project alpha-project --display-name='Alpha Corp'",
        # --node-selector='client=alpha'",
        "oc new-project beta-project --display-name='Beta Corp'",
        # --node-selector='client=beta'",
        "oc adm groups new alpha Amy Andrew",
        "oc adm groups new beta Brian Betty",
        "oc adm policy add-role-to-group admin alpha -n alpha-project",
        "oc adm policy add-role-to-group admin beta -n beta-project",
        "oc label namespace default name=default",
        "oc create -f project_template.yml -n default",
        '''ansible masters -m shell -a "sed -i 's/projectRequestTemplate.*/projectRequestTemplate\: \\"default\\/project-request\\"/g' /etc/origin/master/master-config.yaml"''',
        "ansible masters -m shell -a'systemctl restart atomic-openshift-node'"
    ]

    smoke_test = [
        'oc new-project smoke-test',
        'oc new-app nodejs-mongo-persistent'
    ]

    jenkins = [
        "oc new-project cicd --description='CI/CD Tools Environment' --display-name='CICD - Jenkins'",
        "oc new-project cicd-dev --description='Openshift tasks Development' --display-name='Tasks - Development'",
        "oc new-project cicd-test --description='Openshift tasks Testing' --display-name='Tasks - Testing'",
        "oc new-project cicd-prod --description='Openshift tasks Production' --display-name='Tasks - Production'",
        "oc new-app jenkins-persistent --param MEMORY_LIMIT=2Gi --param VOLUME_CAPACITY=4Gi -p ENABLE_OAUTH=false -e JENKINS_PASSWORD=homework -n cicd",
        "oc policy add-role-to-user edit system:serviceaccount:cicd:jenkins -n cicd-dev",
        "oc policy add-role-to-user edit system:serviceaccount:cicd:jenkins -n cicd-test",
        "oc policy add-role-to-user edit system:serviceaccount:cicd:jenkins -n cicd-prod",
        "oc policy add-role-to-group system:image-puller system:serviceaccounts:cicd-dev -n cicd",
        "oc policy add-role-to-group system:image-puller system:serviceaccounts:cicd-test -n cicd",
        "oc policy add-role-to-group system:image-puller system:serviceaccounts:cicd-prod -n cicd",
        "oc create -f jenkins_build_config.yaml -n cicd",
        "oc start-build cicd-bc -n cicd"
    ]

    if fil is not None:
        if fil == 'installation':
            for i, c in enumerate(installation):
                if i == 0:
                    print('Check that atomic-openshift-utils and '
                          'atomic-openshift-clients are installed! ')
                elif i == 1:
                    print('Executing ansible-playbook prerequisites.yml \n '
                          'This might take couple of minutes to complete!')
                elif i == 2:
                    print('Executing ansible-playbook deploy_cluster.yml \n '
                          'This might take half an hour to complete!')
                elif i == 3:
                    print(
                        'Copy the .kube directory to the bastion host so we '
                        'can run oc commands from host!')
                call(c, shell=True)
        elif fil == 'recycle':
            for i, r in enumerate(recycler):
                if i == 0:
                    print('Installing ose-recycler image on all of the nodes!')
                elif i == 1:
                    print('Tagging ose-recycler image on all of the nodes!')
                call(r, shell=True)
        elif fil == 'smoke':
            for i, s in enumerate(smoke_test):
                if i == 0:
                    print('Creating smoke test application!')
                elif i == 1:
                    print('Creating nodejs_mongoDB application \n'
                          'Please wait 5 minutes until application boots '
                          'and access it via link in Your browser!\n'
                          'http://nodejs-mongo-persistent-smoke-test.apps.{}.'
                          'example.opentlc.com'.format(guid))
                call(s, shell=True)
        elif fil == 'multitenancy':
            for i, s in enumerate(multitenancy):
                if i == 0:
                    print('Creating projects!')
                elif i == 2:
                    print('Creating users on masters!')
                    create_users(prefix="ansible masters -m shell -a '",
                                 suffix="'")
                elif i == 7:
                    create_cluster_resource_quota()
                call(s, shell=True)
        elif fil == 'jenkins':
            for i, s in enumerate(jenkins):
                if i == 0:
                    print('Creating projects!')
                elif i == 11:
                    print('deploy Jenkins Pipeline!')
                call(s, shell=True)
            print('Verify on following link that Jenkins have successfully '
                  'started \n '
                  'https://jenkins-cicd.apps.5414.example.opentlc.com \n'
                  'make sure to use following credentials: \n '
                  'admin/homework\n')


def create_nfs_export():
    """ Method that creates nfs exports on support1"""
    print('Creating folder on NFS node!')
    call('ansible nfs -m shell -a "mkdir -p /srv/nfs/user-vols/pv{0..50}"',
         shell=True)
    print('Creating NFS user volumes!')
    for pv in range(0, 50, 1):
        call(
            '''ansible nfs -m shell -a "echo '/srv/nfs/user-vols/pv{} *(rw,root_squash)' >> /etc/exports.d/openshift-uservols.exports"'''.format(
                pv), shell=True)
    call(
        'ansible nfs -m shell -a "chown -R nfsnobody.nfsnobody  /srv/nfs; chmod -R 777 /srv/nfs; systemctl restart nfs-server"',
        shell=True)


def create_pv_def_file(volume=None,
                       size=None,
                       guid=None,
                       mode=None,
                       reclaim=None,
                       folder=None):
    """Module that created PV definition file"""
    if None not in (volume, size, guid, mode, reclaim, folder):
        content = {"apiVersion": "v1",
                   "kind": "PersistentVolume",
                   "metadata": {
                       "name": volume
                   },
                   "spec": {
                       "capacity": {
                           "storage": size
                       },
                       "accessModes": [mode],
                       "nfs": {
                           "path": "/srv/nfs/user-vols/{}".format(volume),
                           "server": "support1.{}.internal".format(guid)
                       },
                       "persistentVolumeReclaimPolicy": reclaim}
                   }
        with open('{}/{}'.format(folder, volume), 'w') as outfile:
            json.dump(content, outfile)
        print('Created def file for volume: {}'.format(volume))


def deploy():
    """ Method for deploying cluster"""
    pvs_folder = '/root/pvs'

    write_file(content=hosts_content, path='/etc/ansible/hosts')
    write_file(content=project_template, path='project_template.yml')
    write_file(content=jenkins_build_config, path='jenkins_build_config.yaml')

    guid = get_guid()
    set_guid_on_all_nodes(guid=guid)
    commands(fil='installation')
    create_nfs_export()
    create_directory(path=pvs_folder)

    for p in range(0, 24, 1):
        create_pv_def_file(volume='pv{}'.format(p),
                           size='5Gi',
                           guid=guid,
                           mode='ReadWriteOnce',
                           reclaim='Recycle',
                           folder=pvs_folder)

    for p in range(25, 50, 1):
        create_pv_def_file(volume='pv{}'.format(p),
                           size='10Gi',
                           guid=guid,
                           mode='ReadWriteMany',
                           reclaim='Retain',
                           folder=pvs_folder)

    call('cat /root/pvs/* | oc create -f -', shell=True)

    commands(fil='recycle')

    commands(fil='smoke', guid=guid)

    commands(fil='multitenancy')

    commands(fil='jenkins')


def remove():
    """ Method for removing cluster"""
    scripts = [
        'ansible-playbook /usr/share/ansible/openshift-ansible/playbooks/adhoc/uninstall.yml'
        # , 'cat /root/pvs/* | oc delete -f -'
        , 'ansible nodes -a "rm -rf /etc/origin"'
        , 'ansible nfs -a "rm -rf /srv/nfs/*"'
        , 'rm -rf /root/pvs'
    ]
    print('Running uninstall scripts!')
    for s in scripts:
        call(s, shell=True)


if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'o:', ['option='])
    except getopt.GetoptError:
        print(
            'Usage: python one_script_to_control_them_all.py -o [deploy / remove] ')
        sys.exit(2)
    if len(sys.argv[1:]) < 2:
        print(
            'Usage: python one_script_to_control_them_all.py -o [deploy / remove] ')
        sys.exit(2)
    e = ''
    p = ''
    print("Let's start!")
    for o, a in opts:
        if o in ('-o', '--option'):
            if a == 'deploy':
                deploy()
            elif a == 'remove':
                remove()
            else:
                print('Please provide correct option!')
                sys.exit(2)
