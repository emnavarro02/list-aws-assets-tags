## Overview

This script will create a CSV report with tags of a specfic AWS asset type (e.g. EC2, RDS, Lambda)

### Requirements 

The user that will execute the script must have at least the following permissions:

    ```
    {
    "Version": "2012-10-17",
    "Statement": [
            {
                "Sid": "VisualEditor0",
                "Effect": "Allow",
                "Action": [
                    "tag:GetResources",
                    "tag:GetTagValues",
                    "tag:DescribeReportCreation",
                    "tag:GetTagKeys",
                    "tag:GetComplianceSummary"
                ],
                "Resource": "*"
            }
        ]
    }
    ```


### Usage:

The following arguments can be specified when running the script: 

    -a --asset    : (Required) Aseet type, which can be ec2, rds or lambda
    -f --filename : (Optional) The filename. If no value is provided, a default name will be used. 

To execute the script use: 

```bash
    python main.py -a rds -f reportname.csv
```

## Changelog

- 0.0.2:
    - Optimized code to retrieve information with a single method
    - Fixed bugs where some objects were missing when calling AWS API

- 0.0.1:
    - First release
