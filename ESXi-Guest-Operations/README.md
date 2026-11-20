# Challenge

After gaining access to the ESXi shell, I needed to list and retrieve files from an ESXi guest VM.

# Solution

Abuse of VMware vSphere Guest Operations APIs on ESXi.

The `ListFilesInGuest` and `StartProgramInGuest` APIs can be used to list files and execute commands inside a guest VM, respectively.

# References

- [MITRE ATT&CK – T1675: ESXi Administration Command](https://attack.mitre.org/techniques/T1675/)

# Proof of Concept

Both my attacker machine and the target were Linux-based, so I utilized the `vim.vm.guest.ProcessManager.ProgramSpec` class to specify `/bin/bash` and obtain a shell.

If your target is a Windows machine, you may need to use a different program, such as `C:\Windows\System32\cmd.exe`.

Also, output files are saved under paths such as `/tmp/*`, so this implementation won't work as-is on Windows. You can modify the paths accordingly.

The purpose of this script is to demonstrate the main idea rather than provide a universal implementation.

## Installation

(If you've made it this far, you probably know how to do this, but I should satisfy my perfectionism.)

```bash
git clone https://github.com/amir-h-fallahi/UnusefulScripts/
cd ESXi-Guest-Operations
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Configure the required host and guest connection settings.
python guest_browser.py
```
<img width="962" height="416" alt="image" src="https://github.com/user-attachments/assets/307948f0-e40e-4382-be51-5b2d83fe3bc2" />

As you can also see, the script provides a `get <path>` command to download files locally.
