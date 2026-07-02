import sys, os
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(__file__))
from dotenv import load_dotenv; load_dotenv()
import catalog
client = catalog._get_os_client()
client.indices.refresh(index=catalog._OS_INDEX)
count = client.count(index=catalog._OS_INDEX)["count"]
total = len(catalog.get_catalog())
print(f"Doc count in index: {count}/{total}")
