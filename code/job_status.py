from argparse import ArgumentParser
import http.client
import json
import config_utilities as cf

def main_parse_args():
    """Processes command line arguments.

    Expects a number of pipeline specific and global optional arguments.
    If argument is missing, supplies default value.

    Returns: args as populated namespace
    """
    parser = ArgumentParser()
    parser = cf.add_config_args(parser)
    args = parser.parse_args()
    return args


def main():
    """Prints information on chronos jobs.
    """
    args = main_parse_args()

    connection = http.client.HTTPConnection(args.chronos)
    connection.request("GET", "/scheduler/jobs")
    response = connection.getresponse().read()
    response_str = response.decode("utf-8")
    jobs = json.loads(response_str)

    print("\t".join(['name', 'last_succ', 'last_err', 'pending', 'succeeded', 'threw_error',
                     'recovered']))
    for job in jobs:
        jname = -1
        jsucc = -1
        jerr = -1
        threw_error = 0
        recovered = 0
        pending = 0
        succeeded = 0
        jname = job["name"]
        if job["lastSuccess"] != '':
            jsucc = job["lastSuccess"]
        if job["lastError"] != '':
            jerr = job["lastError"]
        if jsucc == -1 and jerr == -1:
            pending = 1
        if jsucc != -1:
            succeeded = 1
        if jerr != -1:
            threw_error = 1
        if jsucc != -1 and jerr != -1 and jsucc > jerr:
            recovered = 0
        print("\t".join([str(jname), str(jsucc), str(jerr), str(pending), str(succeeded),
                         str(threw_error), str(recovered)]))

if __name__ == "__main__":
    main()
