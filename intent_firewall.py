import datetime
import pytz
import re

LOCAL_TZ = pytz.timezone("Asia/Kolkata")

def intent_firewall(command, system_state=None, raw_text=""):
    """
    Enhanced firewall with safety rules for all smart home devices.
    Returns (allowed:bool, message:str, requires_confirmation:bool)
    """
    now = datetime.datetime.now(LOCAL_TZ)

    device = command.get("device", "").lower()
    location = command.get("location", "").lower()
    action = command.get("action", "").lower()
    text_check = raw_text.lower()

    # ====== LIGHTING SAFETY RULES ======
    if "light" in device or device in ["lamp", "chandelier", "led strip", "bulb"]:
        if action == "turn_off":
            # All lights off at night check
            if any(word in location for word in ["all", "entire", "whole"]) or \
               any(word in text_check for word in ["all lights", "entire house lights", "whole house lights"]):
                if now.hour >= 22 or now.hour < 6:
                    return (False, "Are you sure you want to turn off all lights after 10PM? Please confirm.", True)

            # Kids room occupied check
            if "kids" in location or "kids room" in text_check:
                if system_state and system_state.get("kids_room_occupied"):
                    return (False, "Cannot turn off lights in the kids' room while occupied.", False)

            # Stair lights safety at night
            if "stair" in location or "stairs" in text_check:
                if now.hour >= 22 or now.hour < 6:
                    return (False, "Stair lights should remain on for safety during night hours.", True)

        # Brightness safety
        if action == "set_brightness":
            brightness = re.findall(r"\b(\d+)%?\b", text_check)
            if brightness and int(brightness[0]) > 90:
                if now.hour >= 22 or now.hour < 6:
                    return (False, "High brightness levels may disturb sleep. Continue?", True)

    # ====== DOOR & SECURITY SAFETY RULES ======
    if device in ["door", "lock", "garage door", "smart lock"]:
        if action in ["open", "unlock"]:
            # Stranger detection
            if "stranger" in text_check or "unknown person" in text_check:
                return (False, "Opening doors for strangers is not allowed for safety reasons.", False)
            if device in ["door", "lock", "garage door", "smart lock"]:
             if action == "turn_off":
              action = "unlock"  # Normalize

            if device in ["door", "lock", "garage door", "smart lock"]:
             if action == "turn_off":
              return (False, "Unlock command detected. Using 'turn_off' is ambiguous. Action blocked.", True)

            
            # Night time restrictions
            if now.hour >= 23 or now.hour < 6:
                return (False, "Door opening is restricted during night hours (11PM–6AM).", True)
            
            # Multiple doors at once
            if "all doors" in text_check or "every door" in text_check:
                return (False, "Opening all doors simultaneously is not recommended for security.", True)

        if action == "lock" and "all" in text_check:
            # Allow locking all doors (security positive)
            pass

    # ====== KITCHEN APPLIANCE SAFETY RULES ======
    kitchen_appliances = ["oven", "stove", "microwave", "pressure cooker", "blender", "food processor"]
    if device in kitchen_appliances:
        if action in ["turn_on", "start", "preheat"]:
            # Night cooking restrictions
            if now.hour >= 23 or now.hour < 6:
                return (False, f"Using {device} during night hours may be unsafe. Continue?", True)
            
            # High temperature check for oven
            if device == "oven":
                temps = re.findall(r"\b(\d{3})\b", text_check)  # 3-digit temperatures
                if temps and int(temps[0]) > 250:
                    return (False, "High oven temperature detected. Please confirm safe operation.", True)
               
    # ====== CLIMATE CONTROL SAFETY ======
    climate_devices = ["thermostat", "air conditioning", "heater", "humidifier", "dehumidifier"]
    if device in climate_devices:
        temps = re.findall(r"\b(\d{1,2})\b", text_check)
        if temps:
            temp_val = int(temps[0])
            if device in ["thermostat", "air conditioning", "heater"]:
                if temp_val < 10 or temp_val > 32:
                    return (False, "Temperature outside safe range (10°C–32°C). Action blocked.", False)
            
            if device == "humidifier":
                humidity = re.findall(r"\b(\d{2,3})%?\b", text_check)
                if humidity and int(humidity[0]) > 80:
                    return (False, "Humidity above 80% can cause mold. Continue?", True)
     # ====== BATHROOM APPLIANCE SAFETY ======
    bathroom_devices = ["hair dryer", "heated towel rack", "water heater"]
    if device in bathroom_devices:
        if action in ["turn_on", "set_temperature"]:  # <- Added set_temperature
        # Water heater temperature check
            if device == "water heater":
                temps = re.findall(r"\b(\d{1,3})\b", text_check)
                if temps and int(temps[0]) > 60:
                    return (False, "Water temperature above 60°C can cause burns. Action blocked.", False)


    # ====== SECURITY SYSTEM SAFETY ======
    security_devices = ["security camera", "motion sensor", "smoke detector", "co detector", "alarm"]
    if device in security_devices:
        if action in ["turn_off", "disable", "stop"]:
            if now.hour >= 22 or now.hour < 8:
                return (False, f"Disabling {device} during night hours is not recommended.", True)
            
            if "all" in text_check:
                return (False, "Disabling all security devices poses safety risks.", True)

    # ====== POOL & OUTDOOR SAFETY ======
    outdoor_devices = ["pool pump", "pool heater", "hot tub", "sprinkler system", "outdoor grill"]
    if device in outdoor_devices:
        if action == "turn_on":
            # Pool equipment at night
            if device in ["pool pump", "hot tub"] and (now.hour >= 22 or now.hour < 7):
                return (False, f"Operating {device} at night may disturb neighbors. Continue?", True)
            
            # Hot tub temperature
            if device == "hot tub":
                temps = re.findall(r"\b(\d{2})\b", text_check)
                if temps and int(temps[0]) > 40:
                    return (False, "Hot tub temperature above 40°C is unsafe. Action blocked.", False)

    # ====== LAUNDRY SAFETY ======
    if device in ["washing machine", "dryer"]:
        if action == "start":
            # Night operation noise check
            if now.hour >= 22 or now.hour < 7:
                return (False, f"Running {device} at night may disturb others. Continue?", True)

    # ====== GARAGE & TOOLS SAFETY ======
    if device in ["garage door opener", "tool cabinet", "workbench"]:
        if action == "open" and device == "garage door opener":
            if now.hour >= 23 or now.hour < 6:
                return (False, "Opening garage door during late night hours. Continue?", True)

    # ====== SMART SPEAKER & ENTERTAINMENT ======
    entertainment_devices = ["smart speaker", "sound system", "smart tv", "projector"]
    if device in entertainment_devices:
        if action in ["play", "turn_on", "set_volume"]:
            # Volume check
            volume = re.findall(r"\b(\d{1,3})%?\b", text_check)
            if volume and int(volume[0]) > 70:
                if now.hour >= 22 or now.hour < 8:
                    return (False, "High volume during quiet hours may disturb others. Continue?", True)

    # ====== WINDOW & BLINDS SAFETY ======
    if device in ["window blinds", "smart curtains", "window"]:
        if action == "open":
            # Security check at night
            if now.hour >= 23 or now.hour < 6:
                if location in ["ground floor", "first floor", "living room", "bedroom"]:
                    return (False, "Opening ground floor windows/blinds at night may pose security risks.", True)

    # ====== ROBOT DEVICES SAFETY ======
    if device in ["robot vacuum", "robot lawn mower"]:
        if action == "start":
            # Night operation
            if now.hour >= 22 or now.hour < 7:
                return (False, f"Operating {device} at night may disturb sleep. Continue?", True)

    # ====== MEDICAL & PERSONAL DEVICES ======
    if device in ["smart scale", "medicine cabinet", "smart mirror"]:
        if device == "medicine cabinet" and action == "open":
            # Child safety
            if system_state and system_state.get("child_lock_enabled"):
                return (False, "Medicine cabinet requires adult supervision.", True)

    # ====== WATER SYSTEMS SAFETY ======
    water_devices = ["water filter", "sump pump", "sprinkler system", "garden hose"]
    if device in water_devices:
        if action == "start" and device == "sprinkler system":
            # Weather check (if available)
            if system_state and system_state.get("weather_rain"):
                return (False, "Sprinkler system shouldn't run during rain.", True)

    # ====== ENHANCED UNSAFE PHRASES ======
    unsafe_phrases = [
        "open door for stranger", "disable all security", "turn off all alarms",
        "maximum temperature", "disable smoke detector", "turn off all lights",
        "unlock all doors", "disable motion sensors", "stop all security cameras",
        "maximum volume", "hottest setting", "disable child lock"
    ]
    
    if any(phrase in text_check for phrase in unsafe_phrases):
        return (False, "This command may violate safety policies. Action blocked.", False)

    # ====== TIME-BASED RESTRICTIONS ======
    quiet_hours_devices = ["washing machine", "dryer", "robot vacuum", "sound system", "blender"]
    if device in quiet_hours_devices and action in ["start", "turn_on"]:
        if now.hour >= 22 or now.hour < 7:
            return (False, f"Quiet hours restriction: {device} operation may disturb others.", True)

    # ====== ENERGY SAFETY ======
    high_power_devices = ["electric kettle", "microwave", "oven", "dryer", "heater"]
    if device in high_power_devices and "all" in text_check:
        return (False, "Running multiple high-power devices simultaneously may overload circuits.", True)

    # Default allow
    return (True, "", False)