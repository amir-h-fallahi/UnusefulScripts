#!/usr/bin/env python3

import ssl
import os
import time
import requests
from urllib.parse import urlparse, urlunparse
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import urllib3
urllib3.disable_warnings(category=urllib3.exceptions.InsecureRequestWarning)

ESXI = "ESXI_IP"
USERNAME = "ADMIN_USER"
PASSWORD = "ADMIN_PASSWORD"
VM_NAME = "VM_NAME"

GUEST_USER = "GUEST_MACHINE_USERNAME"
GUEST_PASS = "GUEST_MACHINE_PASSWORD"

context = ssl._create_unverified_context()

si = SmartConnect(
    host=ESXI,
    user=USERNAME,
    pwd=PASSWORD,
    port=443,
    sslContext=context
)

try:
    content = si.RetrieveContent()
    container = content.viewManager.CreateContainerView(
        content.rootFolder, [vim.VirtualMachine], True
    )
    vm = next((obj for obj in container.view if obj.name == VM_NAME), None)
    container.Destroy()

    if vm is None:
        raise RuntimeError(f"VM '{VM_NAME}' not found")

    print("VM:", vm.name)
    print("Power state:", vm.runtime.powerState)
    print("VMware Tools:", vm.guest.toolsStatus)

    if vm.runtime.powerState != "poweredOn":
        raise RuntimeError("VM is not powered on")

    guest_ops = content.guestOperationsManager
    file_manager = guest_ops.fileManager
    process_manager = guest_ops.processManager

    auth = vim.vm.guest.NamePasswordAuthentication(
        username=GUEST_USER,
        password=GUEST_PASS
    )

    def fix_url(url):
        parsed = urlparse(url)
        return urlunparse((
            parsed.scheme or "https",
            f"{ESXI}:443",
            parsed.path,
            parsed.params,
            parsed.query,
            parsed.fragment
        ))

    def download_file(guest_path, local_path):
        transfer = file_manager.InitiateFileTransferFromGuest(vm, auth, guest_path)
        url = fix_url(transfer.url)
        r = requests.get(url, verify=False, stream=True, timeout=60)
        r.raise_for_status()
        with open(local_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=64 * 1024):
                if chunk:
                    f.write(chunk)
        return os.path.getsize(local_path)

    def run_bash(command: str, timeout=15):
        tmp_out = f"/tmp/pyvmomi_out_{int(time.time()*1000)}.txt"

        full_cmd = f"{command} > {tmp_out} 2>&1 ; echo EXITCODE:$? >> {tmp_out}"

        spec = vim.vm.guest.ProcessManager.ProgramSpec(
            programPath="/bin/bash",
            arguments=f'-c "{full_cmd}"'
        )

        pid = process_manager.StartProgramInGuest(vm, auth, spec)

        start = time.time()
        while time.time() - start < timeout:
            procs = process_manager.ListProcessesInGuest(vm, auth, [pid])
            if not procs or procs[0].endTime is not None:
                break
            time.sleep(0.4)
        else:
            return f"[Timeout after {timeout}s]"

        local_tmp = f"/tmp/guest_out_{os.getpid()}.txt"
        try:
            download_file(tmp_out, local_tmp)
            with open(local_tmp, "r", errors="replace") as f:
                output = f.read()
            os.remove(local_tmp)
        except Exception as e:
            output = f"[Failed to retrieve output: {e}]"

        try:
            file_manager.DeleteFileInGuest(vm, auth, tmp_out)
        except Exception:
            pass

        return output

    print("\n" + "="*65)
    print("Interactive Guest Shell (via VMware Tools)")
    print("="*65)
    print("Just type any command, it will be executed with /bin/bash -c")
    print("Special commands:")
    print("  get <guest_file> [local_file]   → download a file")
    print("  exit / quit                     → leave")
    print("="*65 + "\n")

    while True:
        try:
            cmd = input(f"{GUEST_USER}@guest> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        if not cmd:
            continue

        if cmd.lower() in ("exit", "quit", "q"):
            print("Bye.")
            break

        if cmd.lower().startswith("get "):
            parts = cmd.split(maxsplit=2)
            if len(parts) < 2:
                print("Usage: get <guest_path> [local_path]")
                continue
            guest_path = parts[1]
            local_path = parts[2] if len(parts) > 2 else os.path.basename(guest_path)
            try:
                print(f"Downloading {guest_path} → {local_path} ...")
                size = download_file(guest_path, local_path)
                print(f"Done ({size} bytes)\n")
            except Exception as e:
                print(f"ERROR: {e}\n")
            continue

        try:
            output = run_bash(cmd)
            print(output)
            if not output.endswith("\n"):
                print()
        except Exception as e:
            print(f"ERROR: {e}\n")

finally:
    Disconnect(si)
