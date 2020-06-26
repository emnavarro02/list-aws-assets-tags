import boto3
import csv
import os
import argparse

# Name, uptime, owner
restag = boto3.client('resourcegroupstaggingapi')
header = ['account',  "region", "instanceid", "name", "uptime", "owner"]


def get_tag_value(obj, element):
    for tag in obj:
        if tag.get("Key") == element:
            return tag.get("Value")


def write_to_csv(filename, header, results, write_header=False, append_data=True):
    """
        filename     (string) : the full path and filename
        results      (list)   : a list with the results
        write_header (bool)   : write the header to the csv file (defaul=False)
        append_data  (bool)   : true = append data to the report / false = overwrite the report (default=true)
    """
    if append_data:
        report_mode = "a"
    else:
        report_mode = "w"
    try:
        if os.path.exists(filename):
            print("Filename {filename} already exists. Setting the write_header as FALSE.".format(filename=filename))
            write_header = False
        else:
            print("Filename {filename} doesn't exist yet. Setting the write_header as TRUE.".format(filename=filename))
            write_header = True
        with open(filename, mode=report_mode) as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=header, lineterminator="\n")
            if write_header:
                print("Writing Header...")
                writer.writeheader()
            else:
                print("Appendind data to the file...")
            for row in results:
                writer.writerow(row)
        print("Finished. The report has been saved on {location}".format(location=filename))
    except TypeError as e:
        print(e)


def ec2_tags_report(report):
    response = restag.get_resources(ResourcesPerPage=50)
    resources_list = []
    while 'PaginationToken' in response and response['PaginationToken']:
        token = response['PaginationToken']
        response = restag.get_resources(ResourcesPerPage=50, PaginationToken=token)
        for resource in response["ResourceTagMappingList"]:
            # print(resource["ResourceARN"])
            if "instance" in resource["ResourceARN"]:
                resources_list.append(
                    {
                        "account": resource["ResourceARN"].split(":")[4],
                        "region": resource["ResourceARN"].split(":")[3],
                        "instanceid": resource["ResourceARN"].split(":")[5].split("/")[1],
                        "name": get_tag_value(resource["Tags"], "Name"),
                        "uptime": get_tag_value(resource["Tags"], "uptime"),
                        "owner": get_tag_value(resource["Tags"], "owner")
                    }
                )
    return resources_list
    # write_to_csv("ec2_tags_report.csv", header, resources_list, True, False)


def rds_tags_report(response):
    response = restag.get_resources(ResourcesPerPage=50)
    resources_list = []
    while 'PaginationToken' in response and response['PaginationToken']:
        token = response['PaginationToken']
        response = restag.get_resources(ResourcesPerPage=50, PaginationToken=token)
        for resource in response["ResourceTagMappingList"]:
            # print(resource["ResourceARN"])
            if "rds" == resource["ResourceARN"].split(":")[2] and "db" == resource["ResourceARN"].split(":")[5]:
                resources_list.append(
                    {
                        "account": resource["ResourceARN"].split(":")[4],
                        "region": resource["ResourceARN"].split(":")[3],
                        "instanceid": resource["ResourceARN"].split(":")[6],
                        "name": get_tag_value(resource["Tags"], "Name"),
                        "uptime": get_tag_value(resource["Tags"], "uptime"),
                        "owner": get_tag_value(resource["Tags"], "owner")
                    }
                )
    return resources_list
    # write_to_csv("rds_tags_report.csv", header, resources_list, True, False)


def lambda_tags_report(response):
    response = restag.get_resources(ResourcesPerPage=50)
    resources_list = []
    while 'PaginationToken' in response and response['PaginationToken']:
        token = response['PaginationToken']
        response = restag.get_resources(ResourcesPerPage=50, PaginationToken=token)
        for resource in response["ResourceTagMappingList"]:
            # print(resource["ResourceARN"])
            if "lambda" == resource["ResourceARN"].split(":")[2] and "function" == resource["ResourceARN"].split(":")[5]:
                resources_list.append(
                    {
                        "account": resource["ResourceARN"].split(":")[4],
                        "region": resource["ResourceARN"].split(":")[3],
                        "instanceid": resource["ResourceARN"].split(":")[6],
                        "name": get_tag_value(resource["Tags"], "Name"),
                        "uptime": get_tag_value(resource["Tags"], "uptime"),
                        "owner": get_tag_value(resource["Tags"], "owner")
                    }
                )
    return resources_list
    # write_to_csv("lambda_tags_report.csv", header, resources_list, True, False)


def main(asset, filename):
    print("Asset: " + asset)
    response = restag.get_resources(ResourcesPerPage=50)

    if asset == "ec2":
        resources_list = ec2_tags_report(response)
    elif asset == "rds":
        resources_list = rds_tags_report(response)
    elif asset == "lambda":
        resources_list = lambda_tags_report(response)
    else:
        print("Service was not found...")

    if not filename:
        print("Filename not defined, using default.")
        filename += asset + "_tags_report.csv"
        print("The new filename is: " + filename)
    write_to_csv(filename, header, resources_list, True, False)


parser = argparse.ArgumentParser(description="Generates a CSV report of tags for AWS assets.")
parser.add_argument("-a", "--asset", help="The AWS asset type.", choices=["ec2", "rds", "lambda"], default="ec2")
parser.add_argument("-f", "--filename", help="The name of the CSV file.", default="")
args = parser.parse_args()
if not args.asset:
    print("Please specify the source of the report. Use -h option to obtain a list of available sources.")
else:
    main(args.asset, args.filename)
