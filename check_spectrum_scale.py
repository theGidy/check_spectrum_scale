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
# # Imports
################################################################################
import argparse
import sys
import os
import subprocess


################################################################################
# # Variable definition
################################################################################
STATE_OK = 0
STATE_WARNING = 1
STATE_CRITICAL = 2
STATE_UNKNOWN = 3


################################################################################
# # Function definition
################################################################################
def getValueFromList(list, header, row):
    """
    Args:
        list     -     list with first line header and following lines data
        header   -     the header name (col) to search
        row      -     the specific row to return
    Return:
        Value from the given list
    """
    print()
    col = list.index(header)
    
    return list[col][row]

def executeBashCommand(command):
    """
    Args:
        command    -    command to execute in bash
        
    Return:
        Returned string from command
    """
    
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    return process.communicate()[0]

def checkRequirments():
    """
    Check if following tools are installed on the system:
        -IBM Spectrum Scale
    """

    if not (os.path.isdir("/usr/lpp/mmfs/bin/") or os.path.isfile("/usr/lpp/mmfs/bin/mmgetstate")):
        checkResult = {}
        checkResult["returnCode"] = STATE_CRITICAL
        checkResult["returnMessage"] = "CRITICAL - No IBM Spectrum Scale Installation detected."
        checkResult["performanceData"] = ""
        printMonitoringOutput(checkResult)       
    

def checkStatus(args):
    """
    Check depending on the arguments following settings:
        - gpfs status
        - quorum status
        - how many nodes are online
    """
    checkResult = {}
    dir = executeBashCommand("pwd");
    executeBashCommand("cd " + args.status.mount);
    output = executeBashCommand("mmgetstate -LY");
    executeBashCommand("cd " + dir);
   
    lines = output.split("\n")
    list = []
    for line in lines:
        list.append(line.split(":"))     
    
    state = getValueFromList(list, "state", 1)
    quorum = getValueFromList(list, "quorum", 1)
    nodeName = getValueFromList(list, "nodeName", 1)
    nodeNumber = getValueFromList(list, "nodeNumber", 1)
    nodesUp = getValueFromList(list, "nodesUp", 1)
    totalNodes = getValueFromList(list, "totalNodes", 1)
       
       
    if args.quorum: 
        if quorum < (totalNodes / 2) + 1:   
            checkResult["returnCode"] = STATE_CRITICAL
            checkResult["returnMessage"] = "Critical - GPFS is ReadOnly because not enougth quorum (" + quorum + "/" + ((totalNodes / 2) + 1) + ") nodes are online!"
       
        else:
            checkResult["returnCode"] = STATE_OK
            checkResult["returnMessage"] = "OK - (" + quorum + "/" + ((totalNodes / 2) + 1) + ") nodes are online!"
    
    if args.node:   
        if args.warning > nodesUp:
            checkResult["returnCode"] = STATE_WARNING
            checkResult["returnMessage"] = "Warning - Less than" + nodeUp + " Nodes are up."
        elif args.critical > nodesUp:
            checkResult["returnCode"] = STATE_CRITICAL
            checkResult["returnMessage"] = "Critical - Less than" + nodeUp + " Nodes are up."
        else:
            checkResult["returnCode"] = STATE_OK
            checkResult["returnMessage"] = "OK - " + nodeName + " "
                
    if not(args.node) and not(quorum):                
        if not(sate == "active"):
            checkResult["returnCode"] = STATE_CRITICAL
            checkResult["returnMessage"] = "Critical - Node" + nodeName + " is in state:" + state
        else:
            checkResult["returnCode"] = STATE_OK
            checkResult["returnMessage"] = "OK - Node" + nodeName + " is in state:" + state
        
    checkResult["performanceData"] = "nodesUp=" + nodeUp + ";" + args.warning + ";" + args.critical + ";; totalNodes=" + totalNodes + " nodesDown=" + (totalNodes - nodesUp) + " quorumUp=" + quorum + ";" + ((totalNodes / 2) + 1) + ";;;"
    printMonitoringOutput(checkResult)
        

    
def checkFileSystems(args):
    """
    
    """
    
def checkFileSets(args):
    """
    
    """
    
def checkPools(args):
    """
    
    """
    
def checkQuota(args):
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
    
    statusParser = subParser.add_parser('status', help='Check the gpfs status on this node');
    statusParser.set_defaults(func=checkStatus) 
    # maybe not neccesarry
    statusParser.add_argument('-m', '--mount', dest='mount', action='store', help='Mount location of the gpfs', required=True)
    statusParser.add_argument('-w', '--warning', dest='warning', action='store', help='Warning if online nodes below this value (default=5)', default=5)
    statusParser.add_argument('-c', '--critical', dest='critical', action='store', help='Critical if online nodes below this value (default=3)', default=3)
    statusGroup = statusParser.add_mutually_exclusive_group(required=True)
    # TODO: Disk quorum
    statusGroup.add_argument('-q', '--quorum', dest='quorum', action='store_true', help='Check the quorum status, will critical if it is less than totalNodes/2+1')
    statusGroup.add_argument('-n', '--nodes', dest='nodes', action='store_true', help='Check state of the nodes')
    
    fileSystemParser = subParser.add_parser('filesystems', help='Check filesystems')
    fileSystemParser.set_defaults(func=checkFileSystems) 
     
    filesetParser = subParser.add_parser('filesets', help='Check the filesets')
    filesetParser.set_defaults(func=checkFileSets) 
     
    poolsParser = subParser.add_parser('pools', help='Check the pools');
    poolsParser.set_defaults(func=checkPools) 
     
    quotaParser = subParser.add_parser('quota', help='Check the quota');
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
# # Main 
################################################################################
if __name__ == '__main__':
   # checkRequirments()
    parser = argumentParser()
    args = parser.parse_args()
    # print parser.parse_args()
    args.func(args)
    
    checkResult = {}
    checkResult["returnCode"] = STATE_UNKNOWN
    checkResult["returnMessage"] = "UNKNOWN - No parameters are passed!"
    checkResult["performanceData"] = ""
    printMonitoringOutput(checkResult)

