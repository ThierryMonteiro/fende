import logging
import random
import string

# Tacker REST API status codes
STATUS = {
    200: 'OK.',
    201: 'Created.',
    202: 'Accepted',
    204: 'No Content.',
    400: 'Bad Request.',
    401: 'Unauthorized.',
    404: 'Not Found.',
    409: 'Conflict.',
    500: 'Internal Server Error.'
}

# common used status
OK = 'OK'
ERROR = 'ERROR'
TIMEOUT = 'TIMEOUT'
ACTIVE = 'ACTIVE'

def init_log(filename):
    logging.basicConfig(
        filename = filename,
        level    = logging.INFO,
        format   = '%(asctime)s [%(levelname)s] %(message)s',
        datefmt  = '%d-%m-%Y %H:%M:%S'
    )

    return logging

def unique_id():
    """Create a unique string"""

    return random.choice(string.ascii_uppercase) + \
           ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(16))

def unique_id_lower():
    """Create a unique string"""

    return random.choice(string.ascii_lowercase) + \
           ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(16))

def create_url(vnf_ip, task):
    return ''.join(['http://', vnf_ip, ':8000/click_plugin/', task])

def vnffgd_template(name, classifier, path,
                    connection_point, constituent_vnfs,
                    dependent_virtual_link):

    path_name = unique_id()
    group_name = unique_id()
    forwarder_name = unique_id()

    return {
        "vnffgd": {
            "name": name,
            "template": {
                "vnffgd": {
                    "tosca_definitions_version": "tosca_simple_profile_for_nfv_1_0_0",
                    "topology_template": {
                        "node_templates": {
                            path_name: {
                                "type": "tosca.nodes.nfv.FP.TackerV2",
                                "properties": {
                                    "policy": {
                                        "type": "ACL",
                                        "criteria": [{
                                            "name": forwarder_name,
                                            "classifier": classifier
                                        }]
                                    },
                                    "path": path,
                                    "id": random.sample(range(1,65535), 1)[0]
                                }
                            }
                        },
                        "groups": {
                            group_name: {
                                "type": "tosca.groups.nfv.VNFFG",
                                "members": [
                                    path_name
                                ],
                                "properties": {
                                    "vendor": "tacker",
                                    "connection_point": connection_point,
                                    "version": "1.0",
                                    "constituent_vnfs": constituent_vnfs,
                                    "number_of_endpoints": len(connection_point),
                                    "dependent_virtual_link": dependent_virtual_link
                                }
                            }
                        }
                    }
                }
            }
        }
    }
