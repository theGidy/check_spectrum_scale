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
# Version: 0.2.0
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
# # Class definition
################################################################################
        

class CheckResult:
    """Simple storage class for return values of the script"""
    
        
    def __init__(self, returnCode=None, returnMessage=None, performanceData=None, longOutput=None):
        
        if returnCode is None:
            self.returnCode = STATE_UNKNOWN
        else:
            self.returnCode = returnCode
            
        if returnMessage is None:
            self.returnMessage = "UNKNOWN"
        else:
            self.returnMessage = returnMessage
            
        if performanceData is None:
            self.performanceData = None
        else:
            self.performanceData = performanceData
         
        if longOutput is None:
            self.longOutput = None
        else:
            self.longOutput = longOutput    

    def printMonitoringOutput(self):
        """
        Print the result message with the performanceData,longOutput for the monitoring tool Nagios/Icinga with the given returnCode state.
    
        Error:
            Prints unknown state if the all variables in the instance are default.
        """
        returnText = self.returnMessage
        if self.performanceData is not None:
            returnText = returnText + "|" + self.performanceData
        if self.longOutput is not None:
            returnText = returnText + "\n" + self.longOutput
            
        print(returnText)
        sys.exit(self.returnCode)

class QuotaObject:
    """
    Simple class whitch holds the name,type of a Violation and the corrosponding boolean values for block/File violation
    """
    
    def __init__(self, name, type):
        self.name = name
        self.type = type
        self.blockViolation = False
        self.fileViolation = False
        self.fileCritical = False
        self.blockCritical = False
        
    def isVioliation(self):
        """
        Returns: true if block or file violation flag is set
        """
        return self.blockViolation or self.fileViolation
    
    def isCritical(self):
        """
        Returns: true if block or file critical flag is set
        """
        return self.blockCritical or self.fileCritical
    
    def __str__(self):
        """
        Returns: the string of the class"""
        return "[name: " + self.name + ", type: " + self.type + ", blockViolation: " + str(self.blockViolation) + ", blockCritical: " + str(self.blockCritical) + ", fileViolation: " + str(self.fileViolation) + ", fileCritical: " + str(self.fileCritical) + "]"
    
    
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
    col = list[0].index(header)

    return list[row][col]

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
        checkResult = CheckResult()
        checkResult.returnCode = STATE_CRITICAL
        checkResult.returnMessage = "CRITICAL - No IBM Spectrum Scale Installation detected."
        checkResult.performanceData = ""
        checkReuslt.printMonitoringOutput()     
    

def checkStatus(args):
    """
    Check depending on the arguments following settings:
        - gpfs status
        - quorum status
        - how many nodes are online
    """
    checkResult = CheckResult()
    output = executeBashCommand("mmgetstate -LY")
    
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
    nodesDown = eval(totalNodes) - eval(nodesUp)
       
    quorumNeeded = ((eval(totalNodes) / 2) + 1)
    
    if args.quorum: 
        if quorum < quorumNeeded :   
            checkResult.returnCode = STATE_CRITICAL
            checkResult.returnMessage = "Critical - GPFS is ReadOnly because not enougth quorum (" + str(quorum) + "/" + str(quorumNeeded) + ") nodes are online!"  
        else:
            checkResult.returnCode = STATE_OK
            checkResult.returnMessage = "OK - (" + str(quorum) + "/" + str(quorumNeeded) + ") nodes are online!"
        checkResult.performanceData = "quorumUp=" + str(quorum) + ";" + str(quorumNeeded) + ";" + str(quorumNeeded) + ";;"
    
    if args.nodes:   
        if args.critical >= nodesUp:
            checkResult.returnCode = STATE_CRITICAL
            checkResult.returnMessage = "Critical - Only " + str(nodesUp) + "/" + str(totalNodes) + " Nodes are up."
        elif args.warning >= nodesUp:
            checkResult.returnCode = STATE_WARNING
            checkResult.returnMessage = "Warning - Only " + str(nodesUp) + "/" + str(totalNodes) + " Nodes are up."
        else:
            checkResult.returnCode = STATE_OK
            checkResult.returnMessage = "OK - " + str(nodesUp) + " Nodes are up."
        checkResult.performanceData = "nodesUp=" + str(nodesUp) + ";" + str(args.warning) + ";" + str(args.critical) + ";; totalNodes=" + str(totalNodes) + " nodesDown=" + str(nodesDown)
                
    if args.status:                
        if not(state == "active"):
            checkResult.returnCode = STATE_CRITICAL
            checkResult.returnMessage = "Critical - Node" + str(nodeName) + " is in state:" + str(state)
        else:
            checkResult.returnCode = STATE_OK
            checkResult.returnMessage = "OK - Node " + str(nodeName) + " is in state:" + str(state)
        checkResult.performanceData = "nodesUp=" + str(nodesUp) + ";" + str(args.warning) + ";" + str(args.critical) + ";; totalNodes=" + str(totalNodes) + " nodesDown=" + str(nodesDown) + " quorumUp=" + str(quorum) + ";" + str(quorumNeeded) + ";;;"
        
   
    checkResult.printMonitoringOutput()
        
    
def checkFileSystems(args):
    """
    
    """
    
def checkFileSets(args):
    """
    
    """
    
def checkPools(args):
    """
        Check depending on the arguments following settings:
        - disk usage all pools
        - disk usage meta/data pools
        - disk usage single pool
    """
    checkResult = CheckResult()
    command = "mmlspool -Y -L "  
    command += " " + args.device
    
    if args.pool:
        command += " " + args.pool
  
    
    output = executeBashCommand(command)
    lines = output.split("\n")
    list = []
    for line in lines:
        list.append(line.split(":"))
    # Clear uneccesary last line 
    list.remove(list[-1])


    resultList = []
    for i in list:
        idx = list.index(i)
        # Skipp header
        if idx > 0:
            name = getValueFromList(list, "name", idx)
            quota = getValueFromList(list, "quota", idx)
            type = getValueFromList(list, "quotaType", idx)
            filesetname = getValueFromList(list, "filesetname", idx)
            blockUsage = eval(getValueFromList(list, "blockUsage", idx))
            blockQuota = eval(getValueFromList(list, "blockQuota", idx))
            fileUsage = eval(getValueFromList(list, "filesUsage", idx))
            fileQuota = eval(getValueFromList(list, "filesQuota", idx))
    
def checkQuota(args):
    """
        Check depending on the arguments following settings:
        - quota on filesets
        - quota on cluster
        - quota per users
    """
    checkResult = CheckResult()
    command = "mmrepquota -Y " 
    if args.type:
        command += "-" + args.type
  
    command += " " + args.device
    
    if args.fileset:
        command += ":" + args.fileset
  
    
    output = executeBashCommand(command)
    lines = output.split("\n")
    list = []
    for line in lines:
        list.append(line.split(":"))
    # Clear uneccesary last line 
    list.remove(list[-1])


    resultList = []
    for i in list:
        idx = list.index(i)
        # Skipp header
        if idx > 0:
            name = getValueFromList(list, "name", idx)
            quota = getValueFromList(list, "quota", idx)
            type = getValueFromList(list, "quotaType", idx)
            filesetname = getValueFromList(list, "filesetname", idx)
            blockUsage = eval(getValueFromList(list, "blockUsage", idx))
            blockQuota = eval(getValueFromList(list, "blockQuota", idx))
            fileUsage = eval(getValueFromList(list, "filesUsage", idx))
            fileQuota = eval(getValueFromList(list, "filesQuota", idx))
            
            warningValue = blockQuota * (float(args.warning) / 100.0)
            criticalValue = blockQuota * (float(args.critical) / 100.0)
        
            quotaObject = QuotaObject(name, type)

            # Check Block Quota
            if blockUsage > criticalValue and blockQuota != 0:
                quotaObject.blockViolation = True 
                quotaObject.blockCritical = True
              
            if blockUsage > warningValue and blockQuota != 0:
                quotaObject.blockViolation = True
                
            # Check file quota
            warningValue = fileQuota * (float(args.warning) / 100.0)
            criticalValue = fileQuota * (float(args.critical) / 100.0)
            if fileUsage > criticalValue and blockQuota != 0:
                quotaObject.fileCritical = True 
                quotaObject.fileViolation = True 
                
            if fileUsage > warningValue and blockQuota != 0:
                quotaObject.fileViolation = True 
                
            if quotaObject.isVioliation():
                resultList.append(quotaObject)
    #Filter for single user/grp request
    if args.name != None:   
        resultList=[x for x in resultList if x.name==args.name]
        
    blockViolation = len([x for x in resultList if x.blockViolation == True and x.blockCritical == False])
    fileViolation = len([x for x in resultList if x.fileViolation == True and x.fileCritical == False])
    blockCritical = len([x for x in resultList if x.blockCritical == True])
    fileCritical = len([x for x in resultList if x.fileCritical == True])
    
    checkResult = CheckResult()
    
    checkResult.performanceData = "blockViolation=" + str(blockViolation) + " blockCritical=" + str(blockCritical) + " fileViolation=" + str(fileViolation) + " fileCritical=" + str(fileCritical);
    if args.longOutput:
            userListBlockCritical = []
            userListFileCritical = []
            userListBlock = []
            userListFile = []

            for user in  [x for x in resultList if x.type == "USR"]:
                if user.blockViolation and user.blockCritical:
                    userListBlockCritical.append(user.name)
                elif user.blockViolation:
                    userListBlock.append(user.name)
                
                if user.fileViolation and user.fileCritical:
                    userListFileCritical.append(user.name)
                elif user.fileViolation:
                    userListFile.append(user.name)
                    
            groupListBlockCritical = []
            groupListFileCritical = []
            groupListBlock = []
            groupListFile = []
            
            for group in [x for x in resultList if x.type == "GRP"]:
                if group.blockViolation and group.blockCritical:
                    groupListBlockCritical.append(group.name)
                elif group.blockViolation:
                    groupListBlock.append(group.name)
                
                if group.fileViolation and group.fileCritical:
                    groupListFileCritical.append(group.name)
                elif group.fileViolation:
                    groupListFile.append(group.name)
            
            checkResult.longOutput = "User Block: " + ", ".join(userListBlock) + "\n"   
            checkResult.longOutput += "User Block Critical: " + ", ".join(userListBlockCritical) + "\n"
            checkResult.longOutput += "User File: " + ", ".join(userListBlockCritical) + "\n"  
            checkResult.longOutput += "User File Critical: " + ", ".join(userListBlockCritical) + "\n"
            checkResult.longOutput += "Group Block: " + ", ".join(groupListBlock) + "\n"   
            checkResult.longOutput += "Group Block Critical: " + ", ".join(groupListBlockCritical) + "\n"
            checkResult.longOutput += "Group File: " + ", ".join(groupListBlockCritical) + "\n"  
            checkResult.longOutput += "Group File Critical: " + ", ".join(groupListBlockCritical)     
    if blockViolation > 0 and blockCritical > 0 or fileViolation > 0 and fileViolation > 0:
        
        checkResult.returnCode = STATE_CRITICAL
        checkResult.returnMessage = "Critical - Block Critical: "+ str(blockCritical)+" File Critical: "+ str(fileCritical)
        
    elif blockViolation > 0 or fileViolation > 0:
        checkResult.returnCode = STATE_WARNING
        checkResult.returnMessage = "WARNING - Block: "+ str(blockViolation)+" File: "+ str(fileViolation)
    else:
        checkResult.returnCode = STATE_OK
        checkResult.returnMessage = "OK - No Violations detected"


    checkResult.printMonitoringOutput()


def argumentParser():
    """
    Parse the arguments from the command line
    """
    parser = argparse.ArgumentParser(description='Check status of the gpfs cluster system')
    group = parser.add_argument_group();
    group.add_argument('-v', '--version', action='version', version='%(prog)s 1.0.0')
  
    subParser = parser.add_subparsers()
    
    statusParser = subParser.add_parser('status', help='Check the gpfs status on this node');
    statusParser.set_defaults(func=checkStatus) 
    statusParser.add_argument('-w', '--warning', dest='warning', action='store', help='Warning if online nodes below this value (default=5)', default=5)
    statusParser.add_argument('-c', '--critical', dest='critical', action='store', help='Critical if online nodes below this value (default=3)', default=3)
    statusParser.add_argument('-L', '--Long', dest='longOutput', action='store_true', help='Displaies additional informations in the long output', default=False)
    statusGroup = statusParser.add_mutually_exclusive_group(required=True)
    statusGroup.add_argument('-q', '--quorum', dest='quorum', action='store_true', help='Check the quorum status, will critical if it is less than totalNodes/2+1')
    statusGroup.add_argument('-n', '--nodes', dest='nodes', action='store_true', help='Check state of the nodes')
    statusGroup.add_argument('-s', '--status', dest='status', action='store_true', help='Check state of this node')
    # Maybe some paramter check of the filesystem in the future
    #  fileSystemParser = subParser.add_parser('filesystems', help='Check filesystems')
    # fileSystemParser.set_defaults(func=checkFileSystems) 
     
    filesetParser = subParser.add_parser('filesets', help='Check the filesets')
    filesetParser.set_defaults(func=checkFileSets) 
    filesetParser.add_argument('-w', '--warning', dest='warning', action='store', help='Warning if disk usage is over this value (default=90 percent)', default=90)
    filesetParser.add_argument('-c', '--critical', dest='critical', action='store', help='Critical if disk usage is over this value (default=95 percent)', default=96)
    filesetParser.add_argument('-d', '--device', dest='device', action='store', help='Device to check the disk usage', required=True) 
    filesetParser.add_argument('-p', '--pools', dest='pools', action='store', help='Name of the pool to check (delimiter is | )')
     
    poolsParser = subParser.add_parser('pools', help='Check the pools');
    poolsParser.set_defaults(func=checkPools) 
    poolsParser.add_argument('-w', '--warning', dest='warning', action='store', help='Warning if disk usage is over this value (default=90 percent)', default=90)
    poolsParser.add_argument('-c', '--critical', dest='critical', action='store', help='Critical if disk usage is over this value (default=95 percent)', default=96)
    poolsParser.add_argument('-t', '--type', dest='type', choices=['m', 'd'], help='Check only meta-disks (m) or data-disks (d)')
    poolsParser.add_argument('-d', '--device', dest='device', action='store', help='Device to check the disk usage', required=True) 
    poolsParser.add_argument('-p', '--pools', dest='pools', action='store', help='Name of the pool to check (delimiter is | )')
      
    quotaParser = subParser.add_parser('quota', help='Check the quota on a filesystem');
    quotaParser.set_defaults(func=checkQuota)
    quotaParser.add_argument('-w', '--warning', dest='warning', action='store', help='Warning if quota is over this value (default=90 percent)', default=90)
    quotaParser.add_argument('-c', '--critical', dest='critical', action='store', help='Critical if quota is over this value (default=95 percent)', default=96)
    quotaParser.add_argument('-d', '--device', dest='device', action='store', help='Device to Check to quota per fileset', required=True) 
    quotaParser.add_argument('-fs', '--fileset', dest='fileset', action='store', help='Check quota  for a fileset')
    quotaParser.add_argument('-n', '--name', dest='name', action='store', help='Check quota for an user/group')
    quotaParser.add_argument('-t', '--type', dest='type', choices=['u', 'g'], help='Check only user other group quota')
    quotaParser.add_argument('-L', '--Long', dest='longOutput', action='store_true', help='Shows additional informations in a long output', default=False)
   # quotaParser.add_argument('-b', '--blockunit', dest='unit', choices=['MB', 'GB', 'TB', 'PB', 'EB', 'ZB'], default='TB', help='display unit [default=TB]')
    
    return parser

        
################################################################################
# # Main 
################################################################################
if __name__ == '__main__':
    checkRequirments()
    parser = argumentParser()
    args = parser.parse_args()
    # print parser.parse_args()
    args.func(args)
