import subprocess
import requests
import json
import sys

if __name__ == "__main__":
    RESULTS_ADDR = sys.argv[1]

    config = json.loads(open('exec_config.json').read())
    command = config["command"]

    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            shell=True)
    output = proc.communicate()[0].decode('utf-8')
    print("OUTPUT: ", output)

    response = json.loads(output)

    config = json.loads(open('exec_config.json').read())
    response["project_name"] = config["project_name"]
    response["db_ranker_id"] = config["db_ranker_id"]

    requests.post(RESULTS_ADDR, json=response)
