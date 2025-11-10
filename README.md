# **bhyve-tui**

A text-based user interface (TUI) tool for managing **bhyve** virtual machines on FreeBSD.


## **Core bhyve Commands**

- ```vm init <path>``` — Initialize the virtual machine directory  
- ```vm list``` — List all virtual machines  
- ```vm create <name> <iso>``` — Create a new virtual machine  
- ```vm start <name>``` — Start a virtual machine  
- ```vm stop <name>``` — Stop a virtual machine  
- ```vm info <name>``` — Display detailed information about a virtual machine  
- ```vm rename <old> <new>``` — Rename a virtual machine  
- ```vm delete <name>``` — Delete a virtual machine and its associated disks  
- ```vm console <name>``` — Connect to the virtual machine’s console  
- ```vm switch create <name>``` — Create a virtual network switch  
- ```vm switch add <name> <iface>``` — Attach a physical network interface to a switch  

## **Additional Commands**

You may also need commands for **monitoring** the state and performance of virtual machines — this can be done using built-in FreeBSD tools.

To manage **snapshots**, use:

- ```vm snapshot <name> <snap>``` — Create a snapshot of a virtual machine  
- ```vm rollback <name>``` — Restore a virtual machine from a snapshot  


## **Requirements**

- FreeBSD 13.0+  
- `bhyve` and `vm-bhyve` packages installed  
- Properly configured ZFS storage pool  
- Textual (for TUI interface):  
  ```bash
  pip3 install textual
