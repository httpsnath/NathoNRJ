import subprocess
import threading
import datetime
import time
import json
import sys
import os
import httpx

#su -c 'cd sdcard/nathrj && export PATH=\$PATH:/data/data/com.termux/files/usr/bin && python ./main.py'


class Main:
    def __init__(self):
        self.client = httpx.Client(headers={"Content-Type": "application/json"})
        self.init_time = datetime.datetime.now()
        self.total_rj = -1
        self.load_config()
        self.recheck = False

        # Start the webhook thread
        self.webhook_thread = threading.Thread(target=self.webhook, daemon=True)
        self.webhook_thread.start()

        # Run the main loop
        self.main_loop()

    def load_config(self):
        """Load configuration from CNFG.json"""
        try:
            with open("./CNFG.json", "r") as cnfg:
                self.config = json.load(cnfg)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading configuration: {e}")
            sys.exit(1)

    def launch_roblox(self):
        """Force stop Roblox and restart it with the configured Place ID"""
        self.total_rj += 1
        commands = [
            ["/system/bin/am", "force-stop", "com.roblox.client"],
            ["/system/bin/am", "start", "-n", "com.roblox.client/com.roblox.client.startup.ActivitySplash"],
            ["/system/bin/am", "start", "-a", "android.intent.action.VIEW", "-d", f"roblox://placeId={self.config['PlaceId']}"],
        ]

        for cmd in commands:
            subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(3)

    def fetch_account(self):
        """Check if the user is offline or inactive, indicating Roblox needs to restart"""

        # Check if Roblox is running
        pid = subprocess.run(["/data/data/com.termux/files/usr/bin/pidof", "com.roblox.client"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if not (pid.stdout).decode():
            return True  # Roblox is not running, needs restart

        # Check Roblox presence API
        response = self.client.post(
            "https://presence.roblox.com/v1/presence/users",
            json={"userIds": [self.config["UserID"]]},
        )
        if response.status_code == 200:
            presences = response.json().get("userPresences", [])
            for presence in presences:
                if presence["userPresenceType"] == 0:  # Offline
                    self.recheck = False
                    return True
                elif presence["userPresenceType"] == 1:  # Online, wait and check again
                    if self.recheck:
                        self.recheck = False
                        return True
                    self.recheck = True
                    
        return False

    def getElapsed(self):
        _time_diff = (datetime.datetime.now() - self.init_time)
        h, r = divmod(_time_diff.seconds, 3600)
        m, s = divmod(r, 60)
        p = []
        if h:
            p.append(f'{h} hour{'s' if h > 1 else ''}')
        if m:
            p.append(f'{m} minutes{'s' if m > 1 else ''}')
        return ' and '.join(p)

    def webhook(self):
        """Capture and send a screenshot via webhook"""
        time.sleep(5)  # Initial delay
        while True:
            
            subprocess.run(["/system/bin/screencap", "-p", "/sdcard/nathrj/atong.png"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            

            with open('/sdcard/nathrj/atong.png', 'rb') as fuq:
                payload = {
                    "embeds": [
                        {
                            "description": f"Update: {datetime.datetime.now().strftime('%m/%d/%Y | %H:%M')}",
                            "color": 2140814,
                            "thumbnail": {
                                "url": "https://camo.githubusercontent.com/2010b43276c01b2112c9374b23c408e867cb10ee4f690733364e67d973c908b5/68747470733a2f2f63646e2e646973636f72646170702e636f6d2f6174746163686d656e74732f313333393536383731353031313835303333332f313333393536383735313034353235313136322f707265766965772e69636f3f65783d36376166333231652669733d363761646530396526686d3d3737373438613562386164666539633037393439336430363334396233393439353362386533643163646633336334303439656163303931343537303130346626"
                            },
                            "image": {"url": "attachment://atong.png"},

                            "fields": [
                                {
                                "name": "Operation uptime:",
                                "value": f"{self.getElapsed()}",
                                "inline": True
                                },
                                {
                                "name": "Total rejoin since operation:",
                                "value": f"{self.total_rj}",
                                "inline": True
                                }
                            ]
                        }
                    ],
                    "username": "NathRJ Webhook",
                    "avatar_url": "https://camo.githubusercontent.com/2010b43276c01b2112c9374b23c408e867cb10ee4f690733364e67d973c908b5/68747470733a2f2f63646e2e646973636f72646170702e636f6d2f6174746163686d656e74732f313333393536383731353031313835303333332f313333393536383735313034353235313136322f707265766965772e69636f3f65783d36376166333231652669733d363761646530396526686d3d3737373438613562386164666539633037393439336430363334396233393439353362386533643163646633336334303439656163303931343537303130346626"
                }
                httpx.post(self.config["WebhookURL"], files={"file": ('atong.png', fuq, "image/png"), "payload_json": (None, json.dumps(payload), "application/json")})
                
            os.remove('/sdcard/nathrj/atong.png')
            # Sleep 60 seconds before sending the next screenshot
            try:
                time.sleep(60)
            except:
                pass


    def main_loop(self):
        """Main loop to monitor Roblox status and restart if needed"""
        while True:  # Check stop event
            if self.fetch_account():
                self.launch_roblox()

            if not self.recheck:
                try:
                    print("3 minutes before fetching...")
                    time.sleep(180)  # Replaces `time.sleep(180)`
                except:
                    pass
            else:
                try:
                    print("30 seconds before rechecking...")
                    time.sleep(30)  # Replaces `time.sleep(30)`
                except:
                    pass
    


if __name__ == "__main__":
    try:
        Main()
    except KeyboardInterrupt:
        sys.exit(0)

