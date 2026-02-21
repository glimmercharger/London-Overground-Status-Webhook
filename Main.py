import requests
import time

# --- CONFIGURATION ---
WEBHOOK_URL = "https://discord.com/api/webhooks/1474807586942488717/VzP1B-2mllRCPqxCAmphj6OFACAS4zCxEvDwynj-VzAmAL9azgnesBQWa5PkBkG5Szv5"
# Paste your key here exactly as it appears in your TfL profile
API_KEY = "59bac6339fc0412580dee3e1e8f3c643" 
DISCORD_ROLE_ID = "1473804781943390379"

# Clean the key and prepare the URL
CLEAN_KEY = API_KEY.strip()
# Using 'overground' as the mode ID for better compatibility
TFL_API_URL = f"https://api.tfl.gov.uk/line/mode/overground/status?app_key={CLEAN_KEY}"

line_status_memory = {}
last_heartbeat = time.time()
HEARTBEAT_INTERVAL = 10800 

def get_data():
    try:
        # We print the URL once to the console so you can copy-paste it into a browser to test
        r = requests.get(TFL_API_URL, timeout=15)
        if r.status_code != 200:
            print(f"[{time.strftime('%H:%M:%S')}] Error {r.status_code}: {r.text}")
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] Connection Error: {e}")
        return None

def send_to_discord(message, should_ping=False):
    content = f"<@&{DISCORD_ROLE_ID}>\n{message}" if (should_ping and DISCORD_ROLE_ID) else message
    try:
        requests.post(WEBHOOK_URL, json={"content": content})
    except Exception as e:
        print(f"Error sending to Discord: {e}")

if __name__ == "__main__":
    print(f"Testing URL: {TFL_API_URL}")
    print("London Overground Monitor Active...")

    while True:
        data = get_data()
        current_time = time.time()
        
        if data:
            disrupted_messages = []
            good_branches = []
            new_disruption_found = False
            state_changed = False

            for line in data:
                name = line['name']
                # Overground often returns multiple line statuses for different branches
                for status_obj in line['lineStatuses']:
                    status_desc = status_obj['statusSeverityDescription']
                    severity = status_obj['statusSeverity']
                    reason = status_obj.get('reason', "No specific reason provided.")

                    # Change detection
                    if name not in line_status_memory or line_status_memory[name] != status_desc:
                        state_changed = True
                        if severity <= 6:
                            new_disruption_found = True
                        line_status_memory[name] = status_desc

                    if severity < 10:
                        disrupted_messages.append(f"🧡 **{name}**: {status_desc}\n*{reason}*")
                    else:
                        good_branches.append(name)
                    
                    # We only care about the top-level status for the summary
                    break 

            if state_changed:
                if disrupted_messages:
                    msg = "\n\n".join(disrupted_messages)
                    if good_branches:
                        msg += f"\n\n✅ **Good service on other branches:** ({', '.join(good_branches)})"
                else:
                    msg = "✅ **All London Overground branches are now reporting a Good Service.**"

                send_to_discord(msg, should_ping=new_disruption_found)
                last_heartbeat = current_time
            
            elif (current_time - last_heartbeat) >= HEARTBEAT_INTERVAL:
                send_to_discord("🕒 *3-Hour Heartbeat: Overground monitor is active.*")
                last_heartbeat = current_time

        time.sleep(300)
