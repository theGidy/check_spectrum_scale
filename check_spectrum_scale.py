#!/usr/bin/python
################################################################################
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
################################################################################

################################################################################
# Name:    Check IBM Spectrum Scale / GPFS
# Author:  Philipp Posovszky, DLR - philipp.posovszky@gmail.com
# Version: 0.0.1
# Date: 30/08/2016
# Dependencies:
#   - IBM Spectrum Scale
################################################################################


# The actual code is managed in the following Git rebository - please use the
# Issue Tracker to ask questions, report problems or request enhancements. The
# repository also contains an extensive README.
#   https://github.com/theGidy/check_spectrum_scale.git


################################################################################
# Disclaimer: This sample is provided 'as is', without any warranty or support.
# It is provided solely for demonstrative purposes - the end user must test and
# modify this sample to suit his or her particular environment. This code is
# provided for your convenience, only - though being tested, there's no
# guarantee that it doesn't seriously break things in your environment! If you
# decide to run it, you do so on your own risk!
################################################################################


################################################################################
## Imports
################################################################################
import argparse
import sys


################################################################################
## Variable definition
################################################################################


################################################################################
## Function definition
################################################################################
def checkStatus():
    """
    
    """
    
def checkFileSystems():
    """
    
    """
    
def checkFileSets():
    """
    
    """
    
def checkPools():
    """
    
    """
    
def checkQuota():
    """
    
    """


def argumentParser():
    """
    Parse the arguments from the command line
    """
    parser = argparse.ArgumentParser(description='Check status of the gpfs filesystem')
    group = parser.add_argument_group();
    group.add_argument('-v', '--version', action='version', version='%(prog)s 1.0.0')
    
    subParser = parser.add_subparsers()
    
    statusParser = subParser.add_parser('status', help='Check the health status on the gpfs');
    jobGroup = statusParser.add_mutually_exclusive_group(required=True)
    statusParser.set_defaults(func=checkStatus) 
    
    fileSystemParser = subParser.add_parser('filesystems', help='Check filesystems');
    jobGroup = statusParser.add_mutually_exclusive_group(required=True)
    fileSystemParser.set_defaults(func=checkFileSystems) 
    
    filesetParser = subParser.add_parser('filesets', help='Check the filesets');
    jobGroup = statusParser.add_mutually_exclusive_group(required=True)
    filesetParser.set_defaults(func=checkFileSets) 
    
    poolsParser = subParser.add_parser('pools', help='Check the pools');
    jobGroup = statusParser.add_mutually_exclusive_group(required=True)
    poolsParser.set_defaults(func=checkPools) 
    
    quotaParser = subParser.add_parser('quota', help='Check the quota');
    jobGroup = statusParser.add_mutually_exclusive_group(required=True)
    quotaParser.set_defaults(func=checkQuota)    

    return parser

def printMonitoringOutput(checkResult):
    """
    Print the result message with the performanceData for the monitoring tool with the given returnCode state.
    
    Args:
        checkResult: HashArray with returnMessage, perfomranceData and returnCode
    
    Error:
        Prints critical state if the parsed checkResult argument is empty.
    """
    if checkResult != None:
        print(checkResult["returnMessage"] + "|" + checkResult["performanceData"])
        sys.exit(checkResult["returnCode"])
    else:
        print("Critical - Error in Script")
        sys.exit(2)
        
################################################################################
## Main 
################################################################################
if __name__ == '__main__':
    parser = argumentParser()
    args = parser.parse_args()
    # print parser.parse_args()


