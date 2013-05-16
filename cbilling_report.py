#!/usr/bin/env python
# encoding: utf-8
'''
cbilling_report -- AWS consolidated billing reporting tool

cbilling_report is a tool to split the AWS costs by a specific AWS tag
by using the consolidated billing facility

@author:     Juan Fernandez-Rebollos
        
@copyright:  2013 TheLastMonkeys. All rights reserved.
        
@license:    GNU General Public License version 3

@contact:    juan.fernandez@thelastmonkeys.com
@deffield    updated: 2013-05-16
'''

import boto
from boto.s3.key import Key
import csv
import ConfigParser as configparser
import json
import os
import sys
from datetime import date

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

__all__ = []
__version__ = 0.1
__date__ = '2013-05-16'
__updated__ = '2013-05-16'

DEBUG = 1
TESTRUN = 0
PROFILE = 0

class CLIError(Exception):
    '''Generic exception to raise and log different fatal errors.'''
    def __init__(self, msg):
        super(CLIError).__init__(type(self))
        self.msg = "E: %s" % msg
    def __str__(self):
        return self.msg
    def __unicode__(self):
        return self.msg

def main(argv=None): # IGNORE:C0111
    '''Command line options.'''
    
    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)

    program_name = os.path.basename(sys.argv[0])
    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    program_version_message = '%%(prog)s %s (%s)' % (program_version, program_build_date)
    program_shortdesc = __import__('__main__').__doc__.split("\n")[1]
    program_license = '''%s

  Created by Juan Fernandez-Rebollos on %s.
  Copyright 2013 TheLastMonkeys. All rights reserved.
  
  Licensed under the GNU General Public License version 3
  http://www.gnu.org/licenses/gpl-3.0
  
  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.

USAGE
''' % (program_shortdesc, str(__date__))

    try:
        # Setup argument parser
        parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument("-c", "--config", dest="config_file", metavar="config_file", help="configuration file [default: %(default)s]", default="awsbilling.cfg")
        parser.add_argument('-V', '--version', action='version', version=program_version_message)
        parser.add_argument('year_month', metavar="YYYY-MM", nargs='?', help="year and month of the report [default: current month]", default="%04d-%02d" % (date.today().year, date.today().month))
        
        # Process arguments
        args = parser.parse_args()
        
        config_file = args.config_file
        year_month = args.year_month
        
        # Parameters check
        if not os.path.exists(config_file):
            raise CLIError("the configuration file %s does not exist" % config_file)

        # Load the configuration file and its values
        config = configparser.SafeConfigParser();
        config.read(config_file)
        aws_access_key_id = config.get('Credentials', 'aws_access_key_id')
        aws_secret_access_key = config.get('Credentials', 'aws_secret_access_key')
        reports_dir = config.get('ConsolidatedBilling', 'reports_dir')
        account_id = config.get('ConsolidatedBilling', 'account_id')
        bucket = config.get('ConsolidatedBilling', 'bucket')
        tag = config.get('ConsolidatedBilling', 'tag')

        # Create the reports directory if it does not exist
        if not os.path.exists(reports_dir):
            os.mkdir(reports_dir)
        
        # Download the reports
        # XXX - Check if already there for previous months and date > lastday
        download_reports(reports_dir, aws_access_key_id, aws_secret_access_key, bucket, account_id, year_month)
        
        # Process the cost allocation reports
        report = process_cost_allocation_report(reports_dir, account_id, tag, year_month)
        
        # Dump the report as a JSON data
        print "Report for account %s on %s" % (account_id, year_month)
        json.encoder.FLOAT_REPR = lambda f: ("%.2f" % f)
        print json.dumps(report, indent=4, sort_keys=True)
        
        return 0
    
    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 0
    except Exception as e:
        if DEBUG or TESTRUN:
            raise(e)
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        return 2


def download_reports(reports_dir, access_key, secret, bucket_name, account_id, year_month):

    billing_filename = "%s-aws-billing-csv-%s.csv" % (account_id, year_month)
    cost_alloc_filename = "%s-aws-cost-allocation-%s.csv" % (account_id, year_month)

    s3 = boto.connect_s3(access_key, secret)
    bucket = s3.get_bucket(bucket_name)
    key = Key(bucket, billing_filename)
    key.get_contents_to_filename("%s/%s" % (reports_dir, billing_filename))
    key = Key(bucket, cost_alloc_filename)
    key.get_contents_to_filename("%s/%s" % (reports_dir, cost_alloc_filename))


def process_cost_allocation_report(reports_dir, account_id, tag, year_month):

    # Parse the CSV into a data structure
    filename = "%s/%s-aws-cost-allocation-%s.csv" % (reports_dir, account_id, year_month)
    with open(filename, 'r') as csvfile:
        csvreport = csv.reader(csvfile)
        headers = []
        data = []
        for row in csvreport:
            if len(row) == 1:
                continue
            if len(headers) == 0:
                headers = row
                continue
            rowobj = {}
            for i in range(len(row)):
                rowobj[headers[i]] = row[i]
            data.append(rowobj)

    # Check that the billing tag does exist
    btag = "user:%s" % tag
    if btag not in headers:
        raise CLIError("the billing tag %s does not appear in the report" % btag)
        return

    # Traverse the data and compose the report
    report = {}
    for line in data:

        client = line[btag]

        # Btag structure
        if btag not in report:
            report[btag] = {}
            report['TotalCost'] = 0.0

        # New client entry
        if client not in report[btag]:
            report[btag][client] = {}
            report[btag][client]['Products'] = {}
            report[btag][client]['TotalCost'] = 0.0

        # Fill values
        try:
            product = line['ProductName']
            if product == "":
                continue
        #    product = line['ProductName'] + " - " + line['ItemDescription']
            if product not in report[btag][client]['Products']:
                #report[btag][client]['Products'][product] = {}
                #report[btag][client]['Products'][product]['TotalCost'] = 0.0
                report[btag][client]['Products'][product] = 0.0
            TotalCost = round(float(line['TotalCost']), 3)
            #UsageQuantity = float(line['UsageQuantity'])
            report[btag][client]['TotalCost'] += TotalCost
            #report[btag][client]['Products'][product]['TotalCost'] += TotalCost
            report[btag][client]['Products'][product] += TotalCost
            report['TotalCost'] += TotalCost
        except ValueError:
            pass
        except:
            print "Unexpected error:", sys.exc_info()[0]

    # Return the composed report
    return report


if __name__ == "__main__":
    #if DEBUG:
        #sys.argv.append("-h")
        #sys.argv.append("-v")
        #sys.argv.append("-r")
    if TESTRUN:
        import doctest
        doctest.testmod()
    if PROFILE:
        import cProfile
        import pstats
        profile_filename = 'cbilling_report_profile.txt'
        cProfile.run('main()', profile_filename)
        statsfile = open("profile_stats.txt", "wb")
        p = pstats.Stats(profile_filename, stream=statsfile)
        stats = p.strip_dirs().sort_stats('cumulative')
        stats.print_stats()
        statsfile.close()
        sys.exit(0)
    sys.exit(main())