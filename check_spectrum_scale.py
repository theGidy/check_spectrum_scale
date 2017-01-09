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
# https://github.com/theGidy/check_spectrum_scale.git


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
import re



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
        
class PoolObject:
    """
    Simple class whtich holds informations about pools 
    """
    
    def __init__(self, name, id, data, meta, dataTotal, dataFree, metaTotal, metaFree):
        self.name = name
        self.id = int(id)
        self.data = (data == 'yes')
        self.meta = (meta == 'yes')
        self.dataTotal = int(dataTotal)
        self.dataFree = int(dataFree)
        self.metaTotal = int(metaTotal)
        self.metaFree = int(metaFree)
        self.criticalMeta = False;
        self.criticalData = False;
        self.warningMeta = False;
        self.warningData = False;
        
    def __str__(self):
        """
        Returns: the string of the class"""
        text = "[name: " + self.name + ", id: " + str(self.id) + ", data: " + str(self.data) + ", meta: " + str(self.meta) + ", dataTotal: " + str(self.dataTotal)
        text += ", dataFree: " + str(self.dataFree) + ", metaTotal: " + str(self.metaTotal) + ", metaFree: " + str(self.metaFree) + ", warningData: " + str(self.warningData) 
        text += ", ciritcalData: " + str(self.criticalData) + ", warningMeta: " + str(self.warningMeta) + ", criticalMeta: " + str(self.criticalMeta) + "]"
        return text
    
class FileSetObject:
    """
    Simple class whtich holds informations about filesets
    """
    
    def __init__(self, filesystemName, filesetName, id, status, maxInodes, allocInodes, dataSize=0):
        self.filesystemName = filesystemName
        self.filesetName = filesetName
        self.id = id
        self.status = status
        self.maxInodes = int(maxInodes)
        self.allocInodes = int(allocInodes)
        self.freeInodes = self.maxInodes - self.allocInodes
        self.dataSize = dataSize
        self.warningInodes = False
        self.criticalInodes = False

    def __str__(self):
        """
        Returns: the string of the class""" 
        text = "[filesetName: " + self.filesetName + ", id: " + str(self.id) + ", filesystemName: " + self.filesystemName + ", status: " + self.status + ", maxInodes: " + str(self.maxInodes)
        text += ", allocInodes: " + str(self.allocInodes) + ", freeInodes: " + str(self.freeInodes) + ", dataSize: " + str(self.dataSize) + ", warningInodes: " + str(self.warningInodes) + ", criticalInodes: " + str(self.criticalInodes) + "]"
        return text
    

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

    if not (os.path.isdir("/usr/lpp/mmfs/bin/") and os.path.isfile("/usr/lpp/mmfs/bin/mmgetstate") and os.path.isfile("/usr/lpp/mmfs/bin/mmlsfileset") and os.path.isfile("/usr/lpp/mmfs/bin/mmrepquota") and os.path.isfile("/usr/lpp/mmfs/bin/mmfs")):
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
	- nodes
    """
    checkResult = CheckResult()
    output = executeBashCommand("sudo /usr/lpp/mmfs/bin/mmgetstate -LY")
    
    lines = output.split("\n")
    list = []
    for line in lines:
        list.append(line.split(":"))     
    
    state = getValueFromList(list, "state", 1)
    quorumNeeded = getValueFromList(list, "quorum", 1)
    nodeName = getValueFromList(list, "nodeName", 1)
    quorumsUp = getValueFromList(list, "nodesUp", 1)
    totalNodes = getValueFromList(list, "totalNodes", 1)

    if args.quorum: 
        if quorumsUp < quorumNeeded :   
            checkResult.returnCode = STATE_CRITICAL
            checkResult.returnMessage = "Critical - GPFS is ReadOnly because not enougth quorum " + str(quorumsUp) + " are online and " + str(quorumNeeded) + " are required!"  
        else:
            checkResult.returnCode = STATE_OK
            checkResult.returnMessage = "OK - " + str(quorumsUp) + " are up and " + str(quorumNeeded) + " quroums are required!"
        checkResult.performanceData = "qourumUp=" + str(quorumsUp) + ";" + str(quorumNeeded) + ";;; quorumNeeded=" + str(quorumNeeded) + ";;; totalNodes=" + str(totalNodes)
                
    if args.status:                
        if not(state == "active"):
            checkResult.returnCode = STATE_CRITICAL
            checkResult.returnMessage = "Critical - Node" + str(nodeName) + " is in state:" + str(state)
        else:
            checkResult.returnCode = STATE_OK
            checkResult.returnMessage = "OK - Node " + str(nodeName) + " is in state:" + str(state)
        checkResult.performanceData = "quorumUp=" + str(quorumsUp) + ";" + str(quorumNeeded) + ";;; quorumNeeded=" + str(quorumNeeded) + ";;; totalNodes=" + str(totalNodes)
    if args.nodes:
        if totalNodes < args.critical :   
            checkResult.returnCode = STATE_CRITICAL
            checkResult.returnMessage = "Critical - Only" + str(totalNodes) + " are up"
        elif totalNodes < args.warning :
            checkResult.returnCode = STATE_WARNING
            checkResult.returnMessage = "WARNING - Only" + str(totalNodes) + " are up"
        else:
            checkResult.returnCode = STATE_OK
            checkResult.returnMessage = "OK - " + str(totalNodes) + " are up"
        checkResult.performanceData = "quorumsUp=" + str(quorumsUp) + ";" + str(quorumNeeded) + ";;; quorumNeeded=" + str(quorumNeeded) + ";;; totalNodes=" + str(totalNodes)
   
    checkResult.printMonitoringOutput()
        
    
def checkFileSystems(args):
    """
    
    """
    
def checkFileSets(args):
    """
        Check depending on the arguments following settings:
        - inode utilization on filesets
        - mount status
        - blocksize utilization
    """
    checkResult = CheckResult()
    command = "sudo /usr/lpp/mmfs/bin/mmlsfileset " + args.device
    if args.filesets:
        command += " " + args.filesets
    if args.size:
        command += " -d"
    command += " -Y"
   
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
            if args.size:
                filesetObject = FileSetObject(filesystemName=list[idx][6], filesetName=list[idx][7], id=list[idx][7], status=list[idx][10], maxInodes=list[idx][32], allocInodes=list[idx][33], dataSize=list[idx][15])
            else:
                filesetObject = FileSetObject(filesystemName=list[idx][6], filesetName=list[idx][7], id=list[idx][7], status=list[idx][10], maxInodes=list[idx][32], allocInodes=list[idx][33])
            if filesetObject.freeInodes < calculatePercentageOfValue(args.warning, filesetObject.maxInodes):
                     filesetObject.warningInodes = True   
            if filesetObject.freeInodes < calculatePercentageOfValue(args.warning, filesetObject.maxInodes):
                     filesetObject.criticalInodes = True      
            resultList.append(filesetObject)
    checkResult = CheckResult()   

    if args.inodes:
        criticalNodeUtilization= [x.filesetName for x in resultList if x.criticalInodes== True]
        warningNodeUtilization= [x.filesetName for x in resultList if x.warningInodes == True and x.criticalInodes == False]
    
        if len(criticalNodeUtilization)>0:
            checkResult.returnCode = STATE_CRITICAL
            checkResult.returnMessage = "Critical  - On "+str(len(criticalNodeUtilization))+" filesets the inode utilization is to high!"
        elif len(warningNodeUtilization)>0:
            checkResult.returnCode = STATE_WARNING
            checkResult.returnMessage = "Warning - On "+str(len(warningNodeUtilization))+"  filesets the inode utilization is to high!"
        else:
            checkResult.returnCode = STATE_OK
            checkResult.returnMessage = "OK - Inode utilization is normal"
            
        if args.longOutput:       
            checkResult.longOutput = "Critical FileSets: " + ", ".join(criticalNodeUtilization) + "\n"   
            checkResult.longOutput += "Warning FileSets: " + ", ".join(warningNodeUtilization) + "\n"
        checkResult.performanceData = ""
        for x in resultList:
            checkResult.performanceData += x.filesetName + "=" + str(x.freeInodes) + ";" + str(calculatePercentageOfValue(args.warning, x.maxInodes)) + ";" + str(calculatePercentageOfValue(args.critical, x.maxInodes)) + ";0;" + str(x.maxInodes) + " "+x.filesetName+"_blockSiz="+str(x.dataSize)+"KB;;;; ";
            
    elif args.link:
        linkedList=[x.filesetName for x in resultList if x.status == 'Linked']
        unlinkedList=[x.filesetName  for x in resultList if x.status == 'Unlinked']
        deletedList=[x.filesetName  for x in resultList if x.status == 'Deleted']
        if args.longOutput:       
            checkResult.longOutput = "Linked FileSets: " + ", ".join(linkedList) + "\n"   
            checkResult.longOutput += "Unlinked FileSets: " + ", ".join(unlinkedList) + "\n"
            checkResult.longOutput += "Deleted FileSets: " + ", ".join(unlinkedList) + "\n"
        if len(unlinkedList)>int(args.critical):
            checkResult.returnCode = STATE_CRITICAL
            checkResult.returnMessage = "Critical  - "+str(len(unlinkedList))+" filesets are unlinked!"
        elif len(unlinkedList)>int(args.warning):
            checkResult.returnCode = STATE_WARNING
            checkResult.returnMessage = "Warning - "+str(len(unlinkedList))+" filesets are unlinked!"
        else:
            checkResult.returnCode = STATE_OK
            checkResult.returnMessage = "OK - "+str(len(linkedList))+"/"+str(len(resultList))+" filesets are linked"
        
        checkResult.performanceData = "Linked=" + str(len(linkedList)) + ";" + str(args.warning) + ";" + str(args.critical) + ";0;" + str(len(resultList)) + " Unlinked=" + str(len(unlinkedList)) + ";" + str(args.warning) + ";" + str(args.critical) + ";0;" + str(len(resultList)) 
        checkResult.performanceData +=" Deleted=" + str(len(deletedList)) + ";" + str(args.warning) + ";" + str(args.critical) + ";0;" + str(len(resultList)) + " ";
          
    checkResult.printMonitoringOutput()
        
  
def checkPools(args):
    """
        Check depending on the arguments following settings:
        - disk usage all pools
        - disk usage meta/data pools
        - disk usage single pool
    """
    checkResult = CheckResult()
    command = "sudo /usr/lpp/mmfs/bin/mmlspool"
    command += " " + args.device
    
    output = executeBashCommand(command)
    output = re.sub(' {1,}', ';', output)
    # print(output)
    lines = output.split("\n")
    list = []
    for line in lines:
        list.append(line.split(";"))
    # Clear uneccesary last line 
    # print(list)
    list.remove(list[-1])
    list.remove(list[0])
    # print(list)

    resultList = []
    
    for i in list:
        idx = list.index(i)
        # Skipp header
        if idx > 0:
            poolObject = PoolObject(name=list[idx][0], id=list[idx][1], data=list[idx][4], meta=list[idx][5], dataTotal=list[idx][6], dataFree=list[idx][7], metaTotal=list[idx][10], metaFree=list[idx][11])
            if poolObject.dataFree < calculatePercentageOfValue(args.critical, poolObject.dataTotal):
                     poolObject.criticalData = True
            if poolObject.metaFree < calculatePercentageOfValue(args.critical, poolObject.metaTotal):
                     poolObject.criticalMeta = True
            if poolObject.dataFree < calculatePercentageOfValue(args.warning, poolObject.dataTotal):
                     poolObject.warningData = True
            if poolObject.metaFree < calculatePercentageOfValue(args.warning, poolObject.metaTotal):
                     poolObject.warningMeta = True
            resultList.append(poolObject)
            
    if args.pools:
        resultList = [x for x in resultList if x.name in args.pools.split(',')]
        
    if args.type == "m":
        resultList = [x for x in resultList if x.meta == True]
    elif args.type == "d":
        resultList = [x for x in resultList if x.data == True]

    criticalData = [x for x in resultList if x.criticalData == True]
    warningData = [x for x in resultList if x.warningData == True and x.criticalData == False]
    criticalMeta = [x for x in resultList if x.criticalMeta == True]
    warningMeta = [x for x in resultList if x.warningMeta == True and x.ciriticalMeta == False]
    
    checkResult = CheckResult()

    checkResult.performanceData = ""
    for x in [x for x in resultList if x.data == True]:
        checkResult.performanceData += "Data_" + x.name + "=" + str(x.dataFree) + ";" + str(calculatePercentageOfValue(args.warning, x.dataTotal)) + ";" + str(calculatePercentageOfValue(args.critical, x.dataTotal)) + ";;" + str(x.dataTotal) + " ";
    for x in [x for x in resultList if x.meta == True]:
        checkResult.performanceData += "Meta_" + x.name + "=" + str(x.metaFree) + ";" + str(calculatePercentageOfValue(args.warning, x.metaTotal)) + ";" + str(calculatePercentageOfValue(args.critical, x.metaTotal)) + ";;" + str(x.metaTotal) + " ";
            
    if len(criticalData) > 0 or len(criticalMeta) > 0 :
        checkResult.returnCode = STATE_CRITICAL
        checkResult.returnMessage = "Critical - Data Pool: " + str(len(criticalData)) + " Meta Pool: " + str(len(criticalMeta))
        
    elif len(warningData) > 0 or len(warningMeta) > 0 :
        checkResult.returnCode = STATE_WARNING
        checkResult.returnMessage = "Warning - Data Pool: " + str(len(warningData)) + " Meta Pool: " + str(len(warningMeta))
    else:
        checkResult.returnCode = STATE_OK
        checkResult.returnMessage = "OK - All " + str(len(resultList)) + " pools in range"

    if args.longOutput:       
            criticalData = [x.name for x in resultList if x.criticalData == True]
            warningData = [x.name for x in resultList if x.warningData == True and x.criticalData == False]
            criticalMeta = [x.name for x in resultList if x.criticalMeta == True]
            warningMeta = [x.name for x in resultList if x.warningMeta == True and x.ciriticalMeta == False] 
            checkResult.longOutput = "Critical Data Pool: " + ", ".join(criticalData) + "\n"   
            checkResult.longOutput += "Warning Data Pool: " + ", ".join(warningData) + "\n"
            checkResult.longOutput += "Critical Meta Pool: " + ", ".join(criticalMeta) + "\n"   
            checkResult.longOutput += "Warning Meta Pool: " + ", ".join(warningMeta) 
    checkResult.printMonitoringOutput()
        
        
def calculatePercentageOfValue(percent, value):
    """
    Return - (100.0-percent*value)/100.0
    """
    return ((100.0 - float(percent)) * float(value)) / 100.0

    
def checkQuota(args):
    """
        Check depending on the arguments following settings:
        - quota on filesets
        - quota on cluster
        - quota per users
    """
    checkResult = CheckResult()
    command = "sudo /usr/lpp/mmfs/bin/mmrepquota -Y " 
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
    # Filter for single user/grp request
    if args.name != None:   
        resultList = [x for x in resultList if x.name == args.name]
        
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
        checkResult.returnMessage = "Critical - Block Critical: " + str(blockCritical) + " File Critical: " + str(fileCritical)
        
    elif blockViolation > 0 or fileViolation > 0:
        checkResult.returnCode = STATE_WARNING
        checkResult.returnMessage = "WARNING - Block: " + str(blockViolation) + " File: " + str(fileViolation)
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
    filesetParser.add_argument('-w', '--warning', dest='warning', action='store', help='Warning if inode utilization is over this value (default=90 percent)', default=90)
    filesetParser.add_argument('-c', '--critical', dest='critical', action='store', help='Critical if inode utilization is over this value (default=95 percent)', default=96)
    filesetParser.add_argument('-d', '--device', dest='device', action='store', help='Device to check the inode utilization', required=True) 
    filesetParser.add_argument('-f', '--filesets', dest='filesets', action='store', help='Name of the filesets to check (delimiter is ,)')
    filesetParser.add_argument('-s', '--size', dest='size', action='store_true', help='Additional outputs the blocksize. Needs more than 5 minutes to respond!')
    filesetGroup = filesetParser.add_mutually_exclusive_group(required=True)
    filesetGroup.add_argument('-l', '--link', dest='link', action='store_true', help='Check the link status of given filesets')
    filesetGroup.add_argument('-i', '--inodes', dest='inodes', action='store_true', help='Check thei node utilization')
    
    filesetParser.add_argument('-L', '--Long', dest='longOutput', action='store_true', help='Display additional informations in the long output', default=False)
     
    poolsParser = subParser.add_parser('pools', help='Check the pools');
    poolsParser.set_defaults(func=checkPools) 
    poolsParser.add_argument('-w', '--warning', dest='warning', action='store', help='Warning if pool usage is over this value (default=90 percent)', default=90)
    poolsParser.add_argument('-c', '--critical', dest='critical', action='store', help='Critical if pool usage is over this value (default=95 percent)', default=96)
    poolsParser.add_argument('-t', '--type', dest='type', choices=['m', 'd'], help='Check only meta-pool (m),data-pool (d)')
    poolsParser.add_argument('-d', '--device', dest='device', action='store', help='Device to check the pool usage', required=True) 
    poolsParser.add_argument('-p', '--pools', dest='pools', action='store', help='Name of the pool to check (delimiter is ,)')
    poolsParser.add_argument('-L', '--Long', dest='longOutput', action='store_true', help='Display additional informations in the long output', default=False)
      
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

