import boto3
import csv
import os
import argparse
from deprecated import deprecated

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


@deprecated(version="0.0.2", reason="Consider using the asset_tags_report function.")
def ec2_tags_report():
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


@deprecated(version="0.0.2", reason="Consider using the asset_tags_report function.")
def rds_tags_report():
    response = restag.get_resources(ResourcesPerPage=50, ResourceTypeFilters=["rds:db"])
    resources_list = []
    if len(response["ResourceTagMappingList"]) > 0:
        resources_list += resource_tag_map_values(response)
        while 'PaginationToken' in response and response['PaginationToken']:
            token = response['PaginationToken']
            response = restag.get_resources(ResourcesPerPage=50, ResourceTypeFilters=["rds:db"], PaginationToken=token)
            resources_list += resource_tag_map_values(response)
    return resources_list


@deprecated(version="0.0.2", reason="Consider using the asset_tags_report function.")
def lambda_tags_report():
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


def resource_tag_map_values(response):
    """
    Get the required values of each object in a list of resources provided by the AWS API.

    Params:
        - response (dict) : The response obtained from the API call that contains AWS resources.
    Returns:
        list
    """
    resources_list = []
    for resource in response["ResourceTagMappingList"]:
        resources_list.append(
            {
                "account": resource["ResourceARN"].split(":")[4],
                "region": resource["ResourceARN"].split(":")[3],
                "instanceid": get_instance_id(resource["ResourceARN"]),
                "name": get_tag_value(resource["Tags"], "Name"),
                "uptime": get_tag_value(resource["Tags"], "uptime"),
                "owner": get_tag_value(resource["Tags"], "owner")
            }
        )
    return resources_list


def get_instance_id(resource_arn):
    """
    Given an object ARN, retrieves the instance_id of the object.
    For example, if the ARN of a lambda function is "arn:aws:lambda:eu-central-1:733412096037:function:iotsync-dev-lambdaFunctionName", the value returned is "iotsync-dev-lambdaFunctionName".
    If the ARN of a EC2 instance is "arn:aws:ec2:eu-central-1:733412096037:instance/i-0db20aa016c4c7956", the value returned is "i-0db20aa016c4c7956".

    Params:
        - resource_arn (String) : The ARN of the resource retrieved by the AWS API
    Returns:
        String
    """
    if "aws:ec2" in resource_arn:
        return resource_arn.split(":")[5].split("/")[1]
    return resource_arn.split(":")[6]


def asset_tags_report(resource_type):
    """
    Get the value of tags for all objects of a specific type.

    Params:
        - resource_type (String) : The object type that is accepted by the API. 
    Returns:
        list
    """
    response = restag.get_resources(ResourcesPerPage=50, ResourceTypeFilters=[resource_type])
    resources_list = []
    if len(response["ResourceTagMappingList"]) > 0:
        resources_list += resource_tag_map_values(response)
        while 'PaginationToken' in response and response['PaginationToken']:
            token = response['PaginationToken']
            response = restag.get_resources(ResourcesPerPage=50, ResourceTypeFilters=[resource_type], PaginationToken=token)
            resources_list += resource_tag_map_values(response)
    return resources_list


def main(asset, filename):
    print("Getting tags for " + asset)

    # If user did not specify the report name then use a default value.
    if not filename:
        print("Filename not defined, using default.")
        filename += asset + "_tags_report.csv"
        print("The new filename is: " + filename)

    # Verify the type of object. If the user did not specify a value, the default value is ec2.
    if asset == "ec2":
        resource_type = "ec2:instance"
    elif asset == "rds":
        resource_type = ("rds:db")
    elif asset == "lambda":
        resource_type = "lambda:function"
    else:
        print("Service was not found...")

    # Verify whether the resource_type has been filled properly. If so, get the tag information.
    if resource_type:
        resources_list = asset_tags_report(resource_type)
        # Print the information to a CSV file
        write_to_csv(filename, header, resources_list, True, False)


parser = argparse.ArgumentParser(description="Generates a CSV report of tags for AWS assets.")
parser.add_argument("-a", "--asset", help="The AWS asset type.", choices=["ec2", "rds", "lambda"], default="ec2")
parser.add_argument("-f", "--filename", help="The name of the CSV file.", default="")
args = parser.parse_args()
if not args.asset:
    print("Please specify the source of the report. Use -h option to obtain a list of available sources.")
else:
    main(args.asset, args.filename)
