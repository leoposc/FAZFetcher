
from pathlib import Path
import time
import os 

KINDLE_PATH = "/Volumes/Kindle/documents/Downloads/"
DAYS = 30
cutoff = time.time() - DAYS * 24 * 3600

extensions = [".azw", ".azw4", ".mobi", ".pdf", ".epub", ".sdr"]

for file in Path(KINDLE_PATH).rglob("*"):
	
	if not file.is_file():
		continue

	if file.suffix.lower() not in extensions: 
		continue

	if not file.name.startswith("FAZ"):
		continue


	mtime = file.stat().st_mtime

	if mtime < cutoff: 
		print("Deleting: ", file)
		os.remove(file)
		
           
