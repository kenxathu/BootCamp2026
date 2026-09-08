import os
import time

TEAM_ID = os.environ.get("TEAM_ID", "01")
print(f"[CI-Runner-Team{TEAM_ID}] CI Build Agent initialized on SCB_VLAN201 (172.16.201.104)")

while True:
    time.sleep(30)
