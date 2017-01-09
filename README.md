# check_spectrum_scale
This python script checks various aspects of an IBM Spectrum Scale (a.k.a GPFS) cluster. It verifies the node state, filesystem mount state, capacity and inode utilization of IBM Spectrum Sclae systems.

# Note
This script is in the development process! We don't have implemented the full functionality. Please report bugs to Ph.Posovszky@gmail.com or on GitHub in the Issus tracker.

# Open Soruce Release
https://github.com/theGidy/check_spectrum_scale

# Permissions for Nagios/Icinga
Change the execution permissions in visudo 

``` bash
icinga  ALL=(ALL) NOPASSWD: /usr/lpp/mmfs/bin/mmgetstate
icinga  ALL=(ALL) NOPASSWD: /usr/lpp/mmfs/bin/mmrepquota
icinga  ALL=(ALL) NOPASSWD: /usr/lpp/mmfs/bin/mmlsquota
```

# NRPE.cfg Example
``` bash
command[check_quota_user]=/usr/lib/nagios/plugins/check_spectrum_scale.py quota -w 95 -c 97 -d Processing_1 -t u -L
command[check_fileset_linked]=/usr/lib/nagios/plugins/check_spectrum_scale.py filesets -d Processing_1 -l  -L -w 0 -c 2
command[check_fileset_inode]=/usr/lib/nagios/plugins/check_spectrum_scale.py filesets -d Processing_1 -i  -L -w 90 -c 96
command[check_status_quorum]=/usr/lib/nagios/plugins/check_spectrum_scale.py status -q
command[check_status_nodes]=/usr/lib/nagios/plugins/check_spectrum_scale.py status -n -w 2 -c 1
command[check_status_node]=/usr/lib/nagios/plugins/check_spectrum_scale.py status -s
```

# Example

## Status
### Status of the gpfs system
This check will be result in warning/critical it are less than warning/critical nodes are online.


``` bash
./check_spectrum_scale.py status -n -w 2 -c 1
OK - 3 Nodes are up.|nodesUp=3;5;3;; totalNodes=3 nodesDown=0
```


### Check Quorum nodes
This check will be result in a critical if less thans n/2+1 quorum nodes are online


``` bash
./check_spectrum_scale.py status -q
OK - (2/2) nodes are online!|quorumUp=2;2;2;;
```


###  Check node gpfs status
This check will be result in a critical if the node is in another state than "active"


``` bash
./check_spectrum_scale.py status -s
OK - Node gpfs-node1.test.de is in state:active|nodesUp=3;5;3;; totalNodes=3 nodesDown=0 quorumUp=2;2;;;
```

## Filesystem

## FileSet

### Check link status
Check the link status of all filesets, if more than 4/6 are unlinked its in warning/critical state

``` bash
./check_spectrum_scale.py filesets -d Processing_1 -l  -L -w 4 -c 6
OK - 9/9 filesets are linked|Linked=14;4;6;0;14 Unlinked=0;4;6;0;14 Deleted=0;4;6;0;14 
Linked FileSets: root, largeHome, set1, set2, set3, set4, set5, set6, temp
Unlinked FileSets: 
Deleted FileSets: 
```

### Check link status specific fileset
Check the link status of the largeHome filesets, if more than 1/1 are unlinked its in warning/critical state

``` bash
./check_spectrum_scale.py filesets -d Processing_1 -f largeHome -l  -L -w 1 -c1
OK - 1/1 filesets are linked|Linked=1;4;6;0;1 Unlinked=0;4;6;0;1 Deleted=0;4;6;0;1
Linked FileSets: largeHome
Unlinked FileSets: 
Deleted FileSets: 
```

### Check inode utilization 
Check the inode utilization of all sfilesets, if more than 90/97 percent are occupied its in warnig/critical state

``` bash
./check_spectrum_scale.py filesets -d Processing_1 -i  -L -w 90 -c 96
OK - Inode utilization is normal|root=64266752;6476697.6;2590679.04;;64766976 blockSiz:0KB;;;;largeHome=10014720;2000025.6;800010.24;;20000256 blockSiz:0KB;;;;Geo_Data=19499520;2000025.6;800010.24;;20000256 blockSiz:0KB;;;;Cal_Sentinel=19499520;2000025.6;800010.24;;20000256 blockSiz:0KB;;;;Pol-InSAR_InfoRetrieval=19899904;2000025.6;800010.24;;20000256 blockSiz:0KB;;;;TSM_TDM_SARData=24161792;3000012.8;1200005.12;;30000128 blockSiz:0KB;;;;TDL_Workspace=1939968;209715.2;83886.08;;2097152 blockSiz:0KB;;;;TAXI=1996800;209715.2;83886.08;;2097152 blockSiz:0KB;;;;Software_Linux=1971712;209715.2;83886.08;;2097152 blockSiz:0KB;;;;Processing_Server_Access=0;0.0;0.0;;0 blockSiz:0KB;;;;TDM_SEC_Cal=19693056;2000025.6;800010.24;;20000256 blockSiz:0KB;;;;TDM_SEC=10277376;2000025.6;800010.24;;20000256 blockSiz:0KB;;;;HR_Projekte=630272;100044.8;40017.92;;1000448 blockSiz:0KB;;;;temp=1789952;209715.2;83886.08;;2097152 blockSiz:0KB;;;;
Critical FileSets: 
Warning FileSets: 
 
```

## Pools

### Check all pools
This check will test if some pool are above 95/97% percent of saturation for the data/meta space on the device Processing_1 with a long output


``` bash
./check_spectrum_scale.py pool -d Processing_1 -w 95 -c 97 -L
Critical - Data Pool: 1 Meta Pool: 0|Data_Pool_2=7261755392;9367607705.6;3747043082.24;;62419992576 Data_Pool_1=2315413504;9367607705.6;3747043082.24;;93676077056 Meta_system=3773308928;0.0;0.0;;3901249536
Critical Data Pool: Pool_1
Warning Data Pool: 
Critical Meta Pool: 
Warning Meta Pool: 
```

### Check one or more specific pools
This check will test if specific pools are above 95/97% percent of saturation for the data/meta space on the device Processing_1 with a long output

``` bash
./check_spectrum_scale.py pool -d Processing_1 -w 95 -c 97 -p Pool_1,Pool_2 -L
Critical - Data Pool: 1 Meta Pool: 0|Data_Pool_2=7261755392;9367607705.6;3747043082.24;;62419992576 Data_Pool_1=2315413504;9367607705.6;3747043082.24;;93676077056 Meta_system=3773308928;0.0;0.0;;3901249536
Critical Data Pool: Pool_1
Warning Data Pool: 
Critical Meta Pool: 
Warning Meta Pool: 
```

## Quota
### Usage
This check will test if some quota is above 95/97% percent of saturation for the fileSystem Processing_1

``` bash
./check_spectrum_scale.py quota -d Processing_1 -w 95 -c 97
WARNING - Block: 1 File: 0|blockViolation=1 blockCritical=0 fileViolation=0 fileCritical=0
```

### Usage only for specific fileset
This check will test if some quota is above 95/97% percent of saturation for the fileSystem Processing_1 and fileset largeHome

``` bash
./check_spectrum_scale.py quota -d Processing_1 -w 95 -c 97 -fs largeHome
WARNING - Block: 1 File: 0|blockViolation=1 blockCritical=0 fileViolation=0 fileCritical=0
```

### Usage only for specific user
This check will test if some quota is above 95/97% percent of saturation for the user "user1"

``` bash
./check_spectrum_scale.py quota -d Processing_1 -w 95 -c 97 -fs largeHome
WARNING - Block: 1 File: 0|blockViolation=1 blockCritical=0 fileViolation=0 fileCritical=0
```

### Usage only for specific group
This check will test if some quota is above 95/97% percent of utilization for the group "admins"

``` bash
./check_spectrum_scale.py quota -w 95 -c 97 -d Processing_1 -n admins -t g
OK - No Violations detected|blockViolation=0 blockCritical=0 fileViolation=0 fileCritical=0
```

