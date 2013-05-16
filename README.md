AWSBILLING
==========

This is a set of tools for managing the Amazon Web Services billing.

cf_report.py
------------

This is a tool used to split the AWS CloudFront costs used by different resources.
It parses an AWS CloudFront monthly usage report XML file, gets each resource usages
 and calculates the costs against an external pricing JSON file.

### Usage

<pre>
cf_report.py [-h] [-V] [-v] [-p pricing_file] report_file

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