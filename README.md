# check_spectrum_scale
This python script checks various aspects of an IBM Spectrum Scale (a.k.a GPFS) cluster. It verifies the node state, filesystem mount state, capacity and inode utilization, and physical disk state of IBM Spectrum Sclae systems.

# Note
This script is in the development process! We don't have implemented the full functionality. Please report bugs to Ph.Posovszky@gmail.com

# Example

##Status
### Status of the gpfs system
This check will be result in warning/critical it are less than warning/critical nodes are online.
<code>
./check_spectrum_scale.py status -n -w 2 -c 1
OK - 3 Nodes are up.|nodesUp=3;5;3;; totalNodes=3 nodesDown=0
</code>

###Check Quorum nodes
This check will be result in a critical if less thans n/2+1 quorum nodes are online
<code>
./check_spectrum_scale.py status -q
OK - (2/2) nodes are online!|quorumUp=2;2;2;;
</code>

###Check node gpfs status
This check will be result in a critical if the node is in another state than "active"
<code>
./check_spectrum_scale.py status -s
OK - Node gpfs-node1.test.de is in state:active|nodesUp=3;5;3;; totalNodes=3 nodesDown=0 quorumUp=2;2;;;
</code>

##Filesystem

##FileSet

##Pools

##Quota


