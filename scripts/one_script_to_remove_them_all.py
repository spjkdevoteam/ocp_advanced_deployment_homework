""" Module that contains script for uninstalling HA cluster """
from subprocess import call


def main():
    """ Main script that uninstalls whole cluster"""
    scripts = [
        'ansible-playbook /usr/share/ansible/openshift-ansible/playbooks/adhoc/uninstall.yml'
        , 'cat /root/pvs/* | oc delete -f -'
        , 'ansible nodes -a "rm -rf /etc/origin"'
        , 'ansible nfs -a "rm -rf /srv/nfs/*"'
        , 'rm -rf /root/pvs'
    ]
    print('Running uninstall scripts!')
    for s in scripts:
        call(s, shell=True)


main()
