#!/usr/bin/env python
# encoding: utf-8
'''
cloudfront_report -- AWS CloudFront cost reporting tool

cloudfront_report is a tool used to split the AWS CloudFront costs used by different resources

@author:     Juan Fernandez-Rebollos
        
@copyright:  2013 TheLastMonkeys. All rights reserved.
        
@license:    GNU General Public License version 3

@contact:    juan.fernandez@thelastmonkeys.com
@deffield    updated: 2013-05-15
'''

import json
import os
import sys
from xml.dom import minidom

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

__all__ = []
__version__ = 0.1
__date__ = '2013-05-15'
__updated__ = '2013-05-15'

DEBUG = 0
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

def main(argv=None):  # IGNORE:C0111
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
        parser.add_argument('-V', '--version', action='version', version=program_version_message)
        parser.add_argument("-v", "--verbose", dest="verbose", action="count", help="set verbose output (include undefined costs)", default=0)
        parser.add_argument("-p", metavar="pricing_file", dest="pricing_file", help="CloudFront JSON pricing file [default: %(default)s]", default="pricing.json")
        parser.add_argument(dest="report_file", help="CloudFront XML Usage Report file")
        
        # Process arguments
        args = parser.parse_args()

        # Set the argument variables and check them
        verbose = args.verbose
        pricing_file = args.pricing_file
        report_file = args.report_file
        
        if verbose > 0:
            print("Verbose mode on")
        
        if not os.path.exists(pricing_file):
            raise CLIError("the pricing file %s does not exist" % pricing_file)
        
        if not os.path.exists(report_file):
            raise CLIError("the report file %s does not exist" % report_file)

        # Load the pricing file
        with open(pricing_file, 'r') as pricingfp:
            pricing = json.load(pricingfp)
        
        # Process the report file along with the pricing
        report = process_report_file(report_file, pricing, (verbose > 0))
        json.encoder.FLOAT_REPR = lambda f: ("%.2f" % f)
        print (json.dumps(report, indent=4))

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


# Script functions
def process_report_file(xmlFile, pricing, showUndefined=True):

    report = {}

    dom = minidom.parse(xmlFile)
    usages = dom.getElementsByTagName('OperationUsage')
    for usage in usages:
    
        service_name = get_childnode_text(usage, 'ServiceName')
        operation_name = get_childnode_text(usage, 'OperationName')
        usage_type = get_childnode_text(usage, 'UsageType')
        resource = get_childnode_text(usage, 'Resource')
        start_time = get_childnode_text(usage, 'StartTime')
        end_time = get_childnode_text(usage, 'EndTime')
        usage_value = get_childnode_text(usage, 'UsageValue')
        
        if 'ServiceName' not in report:
            report['ServiceName'] = service_name
        
        if 'Period' not in report:
            report['Period'] = "" + start_time + " to " + end_time
        
        if 'Total' not in report:
            report['Total'] = 0.0
        
        if 'Resources' not in report:
            report['Resources'] = {}
        
        if resource not in report['Resources']:
            report['Resources'][resource] = {}
            report['Resources'][resource]['Total'] = 0.0
            report['Resources'][resource]['Usages'] = {}
        
        usage_name = operation_name + '.' + usage_type
        if usage_name in pricing:
            usage_cost = pricing[usage_name][1] * int(usage_value) / pricing[usage_name][0]
            report['Resources'][resource]['Total'] += usage_cost
            report['Total'] += usage_cost
        else:
            usage_cost = "UNDEFINED"
        
        operation_usage = {
            'UsageValue': int(usage_value),
            'Cost': usage_cost
        }
        
        if usage_name in pricing or showUndefined:
            report['Resources'][resource]['Usages'][usage_name] = operation_usage 
    
    # Return the report
    return report
    


# Helper function
def get_childnode_text(node, tagName):

    texts = []

    childNode = node.getElementsByTagName(tagName)[0];
    for node in childNode.childNodes:
        if node.nodeType == node.TEXT_NODE:
            texts.append(node.data)
    return ''.join(texts)



# Main function
if __name__ == "__main__":
    if DEBUG:
        # sys.argv.append("-h")
        sys.argv.append("-v")
        # sys.argv.append("-r")
    if TESTRUN:
        import doctest
        doctest.testmod()
    if PROFILE:
        import cProfile
        import pstats
        profile_filename = 'cloudfront_report_profile.txt'
        cProfile.run('main()', profile_filename)
        statsfile = open("profile_stats.txt", "wb")
        p = pstats.Stats(profile_filename, stream=statsfile)
        stats = p.strip_dirs().sort_stats('cumulative')
        stats.print_stats()
        statsfile.close()
        sys.exit(0)
    sys.exit(main())
