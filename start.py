from tqdm import tqdm
import os,sys
import requests
import gnupg
import hashlib
import subprocess
gpg = gnupg.GPG()
variant = ["Workstation","Spin","Lab"]
spins = ["KDE", "Xfce", "LXQt", "MATE_Compiz", "Cinnamon", "LXDE", "SoaS"]
labs = ["Design Suite","Astronomy","Python Classroom","Robotics Suite","Security Lab"]
version = "31"
minor = "1.9"

workstation_download = "https://download.fedoraproject.org/pub/fedora/linux/releases/31/Workstation/x86_64/iso/Fedora-Workstation-Live-x86_64-31-1.9.iso"
workstation_checksum = "https://getfedora.org/static/checksums/Fedora-Workstation-31-1.9-x86_64-CHECKSUM"

spins_url = "https://download.fedoraproject.org/pub/fedora/linux/releases/31/Spins/x86_64/iso/Fedora-FLAVOUR-Live-x86_64-31-1.9.iso"
spins_download = dict()
for spin in spins:
	spins_download[spin] = spins_url.replace("FLAVOUR", spin)
spins_checksum = "https://spins.fedoraproject.org/static/checksums/Fedora-Spins-31-1.9-x86_64-CHECKSUM"

labs_url = "https://download.fedoraproject.org/pub/alt/releases/31/Labs/x86_64/iso/Fedora-FLAVOUR-Live-x86_64-31-1.9.iso"
labs_download = {
	labs[0]: labs_url.replace("FLAVOUR", "Design_suite"),
	labs[1]: labs_url.replace("FLAVOUR", "Astronomy_KDE"),
	labs[2]: labs_url.replace("FLAVOUR", "Python-Classroom"),
	labs[3]: labs_url.replace("FLAVOUR", "Robotics"),
	labs[4]: labs_url.replace("FLAVOUR", "Security"),
}

labs_checksum = "https://labs.fedoraproject.org/static/checksums/Fedora-Labs-31-1.9-x86_64-CHECKSUM"

gpg_download = "https://getfedora.org/static/fedora.gpg"

def file_exists(path):
	return os.path.isfile(path)
def download(url):
	x = url
	buffer_size = 1024
	down = requests.get(x,stream = True)
	file_size = int(down.headers.get("Content-Length",0))
	filename = x.split("/")[-1]
	progress = tqdm(down.iter_content(buffer_size), f"Downloading {filename}", total=file_size, unit="B", unit_scale=True, unit_divisor=1024)
	with open(filename,'wb') as f:
		for data in progress:
			f.write(data)
			progress.update(len(data))
	print()
	return x
def file_delete(path):
	return os.unlink(path)

def gpg_import(key):
	with open(key, "r") as f:
		r = gpg.import_keys(f.read())
	return r

def gpg_verify(fname):
	with open(fname, "rb") as f:
		r = gpg.verify_file(f)
	return r

def hash_verify(iso, checksum):
	with open(checksum, "r") as f:
		c = f.read().replace(" ", "").split()
		s = [x for x in c if x.find(iso) != -1 and x.find("#") == -1]
	if not s: return False
	s = s[0].split("=")[-1]
	with open(iso, "rb") as f:
		x = hashlib.sha256(f.read()).hexdigest()
	return (s == x)

def removable_devices():
	r = []
	for x in os.listdir("/sys/block"):
		with open("/sys/block/"+x+"/removable", "r") as f:
			if int(f.read()) == 1:
				r.append(x)
	r = ["/dev/"+x for x in r]
	return r

def device_vendor(device):
	x = device.split("/")[-1]
	with open("/sys/block/"+x+"/device/vendor", "r") as f:
		r = f.read().strip()
	return r

def burn(iso, drive):
	return subprocess.run(["sudo", "dd", "if="+iso, "of="+drive, "status=progress"])

if not os.geteuid() == 0:
    sys.exit("Run as root!")
for i, var in enumerate(variant):
    print(i+1,'.',var)
var = input("Choose The Fedora Variant = ")
if not var:
	var = 0
else:
	try:
		var = int(var.strip())-1
		assert var < len(variant)
	except:
		exit("invalid choice")
if var == 0:
    downloads = workstation_download
    cheksum = workstation_checksum
elif var == 1:
    for i,flavour in enumerate(spins):
        print(i+1,'.',flavour)
    print("Choose the Fedora Spin flavour: ")
    flavour = input('>')
    try:
        flavour = int(flavour.strip())-1
        assert flavour >=0
        assert flavour < len(spins)
    except:
        print("Invalid Choice!")
    downloads = spins_download[spins[flavour]]
    cheksum = spins_checksum
elif var == 2:
	for i, flavour in enumerate(labs):
		print(i+1,'.',flavour)
	print("choose fedora lab flavour: ")
	flavour = input("> ")
	try:
		flavour = int(flavour.strip())-1
		assert flavour >= 0
		assert flavour < len(labs)
	except:
		print("invalid choice")
	downloads = labs_download[labs[flavour]]
	cheksum = labs_checksum
print("Download the ISO now? (y/n)")
choice = input("> ")
if choice == 'y' or choice == 'yes':
    iso = download(downloads)
else:
    print("If you already have the iso, please input the path to iso.")
    iso = input("> ").strip()
    if not file_exists(iso):
        exit("File doesn't exist")
print("download fedora gpg keys...")
keyfile = download(gpg_download)
print("import fedora gpg keys...")
gpg_import(keyfile)
print("deleting gpg keyfile...")
file_delete(keyfile)
print("downloading a CHECKSUM file...")
checksum_file = download(cheksum)
print("verifying...")
if not gpg_verify(checksum_file):
	print("couldn't verify checksum file")
	print("do you want to continue?(y/n)")
	choice = input("> ")
	if choice != 'y' and choice != 'yes':
		print("invalid checksum file")
	else:
		print("success")
print("veryfing iso file...")
if not hash_verify(iso, checksum_file):
	print("failed, the files maybe corrupted")
	print("do you want to continue?")
	choice = input("(y/n)> ").lower()
	if choice != 'y' and choice != 'yes':
		print("file corrupt")
	else:
		print("Success")
print("deletiing checksum file")
file_delete(checksum_file)
print("choose removable disk")
drives = removable_devices
for i, drive in enumerate(drives):
	print(i+1,'-',drive,'('+device_vendor(drive)+')')
print(len(drives)+1, '- custom')
drive = input("> ")
try:
	drive = int(drive.strip())-1
	assert drive < len(drives)+1
except:
	print("wrong choice")
if drive == len(drives) or drive < 0:
	print("please specify the drive to your drive")
	drive = input("> ").split()
else:
	drive = drives[drive]
print("data on that device will be overwritten!")
print("are you sure to continue?")
choice = input("(y/n) > ")
if choice != 'y' or choice != 'yes':
	print("aborted")
print("burning the iso...")
proc = burn(iso,drive)
if proc.returncode == 0:
	print("success")
else:
	print("dd proccess returned",proc.returncode)
print("Finish.")