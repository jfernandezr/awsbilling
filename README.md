AWSBILLING
==========

This is a set of tools for managing the Amazon Web Services billing.

cbilling_report.py
--------------------

This is a tool used to split the AWS costs by a specific AWS tag
by using the consolidated billing facility. It downloads the reports from the
S3 bucket and generates a report sharing the costs by specified tag.

### Usage

<pre>
usage: cbilling_report.py [-h] [-c config_file] [-V] [YYYY-MM]

positional arguments:
  YYYY-MM               year and month of the report [default: current month]

optional arguments:
  -h, --help            show this help message and exit
  -c config_file, --config config_file
                        configuration file [default: awsbilling.cfg]
  -V, --version         show program's version number and exit
</pre>

This script expects a `awsbilling.cfg` file located on the working directory or
supplied via the `--config` parameter. This configuration file is a INI-style
file with the following data

<pre>
[Credentials]
aws_access_key_id = 7GLPAPPAYOMXUTA3IAJY
aws_secret_access_key = IHGKWPpmu8nMrjjIFSTiCSudAIhAy00NDsFNhstC

[ConsolidatedBilling]
reports_dir = reports
account_id = 297300232729
bucket = billing-bucket
tag = Client
</pre>

The script will download the reports from S3 into the `reports_dir` directory and
parses them, generating a JSON output.

NOTE: Usually, in the generated reports, there is a `Amazon CloudFront` cost that
shows up in the undefined billing group. As of the current date, there is no way
of tagging CloudFront. The recommendation is to discard that value and use the
`cloudfront_report.py` tool to split the costs by resource.


cloudfront_report.py
--------------------

This is a tool used to split the AWS CloudFront costs used by different resources.
It parses an AWS CloudFront monthly usage report XML file, gets each resource usages
and calculates the costs against an external pricing JSON file.

### Usage

<pre>
cloudfront_report.py [-h] [-V] [-v] [-p pricing_file] report_file

positional arguments:
  report_file      CloudFront XML Usage Report file

optional arguments:
  -h, --help       show this help message and exit
  -V, --version    show program's version number and exit
  -v, --verbose    set verbose output (include undefined costs)
  -p pricing_file  CloudFront JSON pricing file [default: pricing.json]
</pre>

The report file is the AWS CloudFront monthly usage report XML downloaded
from the AWS Console. It expects the monthly report for the desired billing period.

The pricing file is a JSON file with the following structure

<pre>
{
  "GET.EU-DataTransfer-Out-Bytes": [1073741824, 0.120],
  "GET.EU-Requests-Tier1": [10000, 0.009],
  "GET.EU-Requests-Tier2-HTTPS": [10000, 0.012],
  ...
}
</pre>

where the dataset is a dictionary where the keys are created by dot-concatenating
the OperationName and UsageType. The value of each dictionary entry is an array of two
elements

* The divider (example: 10.000 requests)
* The cost per divider units (example: 12cts each 10.000 requests)

Please be careful to correctly identify the pricing elements because the XML
files contain detailed data that adds up in other report elements.

The tool returns a JSON dump with the report data.

If the -v flag is used, all entries with no defined price in the pricing file
will show as `UNDEFINED`. This is useful for checking missing price entries in the
pricing file.


License
-------
This software is distributed under the GNU General Public License version 3.

Copyright
---------

Copyright (C) 2013 Juan Fernandez-Rebollos