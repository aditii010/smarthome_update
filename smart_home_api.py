from typing import List

# ✅ Full device registry with initial states
device_states = {
    "bedroom_light": {"status": "off", "brightness": 100},
    "kitchen_light": {"status": "off", "brightness": 100},
    "livingroom_light": {"status": "off", "brightness": 100},
    "kids_room_light": {"status": "off", "brightness": 100},
    "front_door": {"status": "closed", "aliases": ["front door", "main door"]},
    "smart_alarm_clock": {"status": "off"},
    "ceiling_fan": {"status": "off", "speed": 0},
    "window_blinds": {"status": "closed"},
    "smart_mirror": {"status": "off"},
    "electric_toothbrush": {"status": "off"},
    "hair_dryer": {"status": "off"},
    "smart_thermostat": {"status": "off", "temperature": 22},
    "smart_kettle": {"status": "off"},
    "air_purifier": {"status": "off"},
    "smart_oven": {"status": "off"},
    "garbage_disposal": {"status": "off"},
    "smart_speaker": {"status": "off", "volume": 50},
    "robot_vacuum": {"status": "docked"},
    "smart_tv": {"status": "off"},
    "sound_system": {"status": "off"},
    "smart_curtains": {"status": "closed"},
    "air_conditioning": {"status": "off"},
    "smart_doorbell": {"status": "idle"},
    "security_camera": {"status": "on", "recording": False},
    "garage_door_opener": {"status": "closed"},
    "car_charger": {"status": "disconnected"},
    "sprinkler_system": {"status": "off"},
    "security_lights": {"status": "off"},
    "water_filter": {"status": "on"},
    "smart_fridge_display": {"status": "on"},
    "wine_cooler": {"status": "off"},
    "fireplace": {"status": "off"},
    "smart_desk_lamp": {"status": "off"},
    "printer": {"status": "idle"},
    "shredder": {"status": "off"},
    "humidifier": {"status": "off"},
    "white_noise_machine": {"status": "off"},
    "heated_towel_rack": {"status": "off"},
    "smart_scale": {"status": "off"},
    "medicine_cabinet": {"status": "closed"},
    "ice_maker": {"status": "off"},
    "spice_rack": {"status": "closed"},
    "cutting_board": {"status": "clean"},
    "blender": {"status": "off"},
    "food_processor": {"status": "off"},
    "pressure_cooker": {"status": "off"},
    "washing_machine": {"status": "off"},
    "dryer": {"status": "off"},
    "iron": {"status": "off"},
    "dehumidifier": {"status": "off"},
    "sump_pump": {"status": "idle"},
    "tool_cabinet": {"status": "closed"},
    "workbench": {"status": "unused"},
    "pool_heater": {"status": "off"},
    "pool_pump": {"status": "off"},
    "hot_tub": {"status": "off"},
    "garden_hose": {"status": "off"},
    "outdoor_speakers": {"status": "off"},
    "patio_heater": {"status": "off"},
    "outdoor_grill": {"status": "off"},
    "package_box": {"status": "locked"},
    "mailbox": {"status": "empty"},
    "motion_sensors": {"status": "active"},
    "smart_lock": {"status": "locked"},
    "intercom": {"status": "idle"},
    "smart_chandelier": {"status": "off"},
    # Safety & monitoring
    "smoke_detector": {"status": "on"},
    "co_detector": {"status": "on"},
    "baby_monitor": {"status": "on"},
    "water_heater": {"status": "off", "temperature": 45},
    "garage_light": {"status": "off", "brightness": 100},
    "doorbell_camera": {"status": "on", "recording": False},
}

# Aliases for easier LLM matching
DEVICE_ALIASES = {
    "security camera": "security_camera",
    "front door": "front_door",
    "garage door": "garage_door_opener",
    "living room light": "livingroom_light",
    "kitchen light": "kitchen_light",
    "bedroom light": "bedroom_light",
    "kids room light": "kids_room_light",
    "water heater": "water_heater",
    "doorbell camera": "doorbell_camera",
    "smoke detector": "smoke_detector",
    "co detector": "co_detector",
    "fan": "ceiling_fan",
    "lights": "*",  # so "all lights" works
}

def list_devices() -> List[str]:
    """Return a sorted list of all device keys."""
    return sorted(device_states.keys())

def control_device(device: str, location: str, action: str, value=None) -> str:
    responses = []

    # normalize input
    device = DEVICE_ALIASES.get(device.lower(), device.lower()).replace("_", " ").strip()
    location = location.lower().replace("_", " ").strip()

    matched_devices = []
    for dev_name, dev_info in device_states.items():
        dev_name_norm = dev_name.lower().replace("_", " ")
        aliases = [a.lower() for a in dev_info.get("aliases", [])]
        if device in dev_name_norm or device in aliases or device in ["*", "all"]:
            if location in dev_name_norm or location in aliases or location in ["*", "all", "any"]:
                matched_devices.append(dev_name)

    if not matched_devices:
        return f"No such device found: {device} ({location})"

    for dev_name in matched_devices:
        dev = device_states[dev_name]

        # Map common brightness fields
        if isinstance(value, dict):
            value = value.get("brightness") or value.get("level") or value.get("percentage")

        # --- Lights ---
        if "brightness" in dev:
            if action in ["turn_on", "on"]:
                dev["status"] = "on"
                responses.append(f"Turned on the {dev_name.replace('_',' ')}.")
            elif action in ["turn_off", "off"]:
                dev["status"] = "off"
                responses.append(f"Turned off the {dev_name.replace('_',' ')}.")
            elif action in ["dim", "set_brightness"] and value is not None:
                try:
                    val = int(value)
                    val = max(0, min(100, val))
                    dev["brightness"] = val
                    dev["status"] = "on" if val > 0 else "off"
                    responses.append(f"Set brightness of {dev_name.replace('_',' ')} to {val}%.")
                except ValueError:
                    responses.append(f"Invalid brightness value '{value}' for {dev_name.replace('_',' ')}.")
            elif action in ["get_status", "status", "check_status"]:
                state_str = ", ".join(f"{k}={v}" for k, v in dev.items())
                responses.append(f"{dev_name.replace('_',' ')}: {state_str}")
            else:
                responses.append(f"Unknown action '{action}' for {dev_name.replace('_',' ')}.")

        # --- Fans ---
        elif "fan" in dev_name:
            if action in ["turn_on", "on"]:
                dev["status"] = "on"
                if value is not None:
                    try:
                        spd = int(value)
                        dev["speed"] = max(0, min(5, spd))
                    except ValueError:
                        pass
                responses.append(f"Turned on the {dev_name.replace('_',' ')} at speed {dev['speed']}.")
            elif action in ["turn_off", "off"]:
                dev["status"] = "off"
                dev["speed"] = 0
                responses.append(f"Turned off the {dev_name.replace('_',' ')}.")
            elif action in ["set_speed"] and value is not None:
                try:
                    spd = int(value)
                    dev["speed"] = max(0, min(5, spd))
                    dev["status"] = "on" if spd > 0 else "off"
                    responses.append(f"Set speed of {dev_name.replace('_',' ')} to {dev['speed']}.")
                except ValueError:
                    responses.append(f"Invalid speed '{value}' for {dev_name.replace('_',' ')}.")
            elif action in ["get_status", "status"]:
                state_str = ", ".join(f"{k}={v}" for k, v in dev.items())
                responses.append(f"{dev_name.replace('_',' ')}: {state_str}")
            else:
                responses.append(f"Unknown action '{action}' for {dev_name.replace('_',' ')}.")

        # --- Printer ---
        elif "printer" in dev_name:
            if action in ["turn_on", "on"]:
                dev["status"] = "idle"
                responses.append(f"Turned on {dev_name.replace('_',' ')} (ready to print).")
            elif action in ["turn_off", "off"]:
                dev["status"] = "off"
                responses.append(f"Turned off {dev_name.replace('_',' ')}.")
            elif action in ["get_status", "status"]:
                responses.append(f"{dev_name.replace('_',' ')}: status={dev['status']}")
            else:
                responses.append(f"Unknown action '{action}' for {dev_name.replace('_',' ')}.")

        # --- Doors / Locks ---
        elif "door" in dev_name or "lock" in dev_name:
            if action in ["open"]:
                dev["status"] = "open"
                responses.append(f"Opened {dev_name.replace('_',' ')}.")
            elif action in ["close", "lock"]:
                dev["status"] = "closed" if "door" in dev_name else "locked"
                responses.append(f"Closed/locked {dev_name.replace('_',' ')}.")
            elif action in ["unlock"]:
                dev["status"] = "unlocked"
                responses.append(f"Unlocked {dev_name.replace('_',' ')}.")
            elif action in ["get_status", "status"]:
                responses.append(f"{dev_name.replace('_',' ')}: status={dev['status']}")
            else:
                responses.append(f"Unknown action '{action}' for {dev_name.replace('_',' ')}.")

        # --- Thermostats / Water Heater ---
        elif "thermostat" in dev_name or "water_heater" in dev_name:
            if action in ["set_temperature", "temperature"] and value is not None:
                try:
                    temp = int(value)
                    dev["temperature"] = temp
                    dev["status"] = "on"
                    responses.append(f"Set temperature of {dev_name.replace('_',' ')} to {temp}°C.")
                except ValueError:
                    responses.append(f"Invalid temperature '{value}' for {dev_name.replace('_',' ')}.")
            elif action in ["turn_on", "on"]:
                dev["status"] = "on"
                responses.append(f"Turned on {dev_name.replace('_',' ')}.")
            elif action in ["turn_off", "off"]:
                dev["status"] = "off"
                responses.append(f"Turned off {dev_name.replace('_',' ')}.")
            elif action in ["get_status", "status"]:
                state_str = ", ".join(f"{k}={v}" for k, v in dev.items())
                responses.append(f"{dev_name.replace('_',' ')}: {state_str}")
            else:
                responses.append(f"Unknown action '{action}' for {dev_name.replace('_',' ')}.")

        # --- Speakers / Volume ---
        elif "speaker" in dev_name or "sound_system" in dev_name:
            if action in ["turn_on", "on"]:
                dev["status"] = "on"
                responses.append(f"Turned on {dev_name.replace('_',' ')}.")
            elif action in ["turn_off", "off"]:
                dev["status"] = "off"
                responses.append(f"Turned off {dev_name.replace('_',' ')}.")
            elif action in ["set_volume", "volume"] and value is not None:
                try:
                    vol = int(value)
                    dev["volume"] = max(0, min(100, vol))
                    responses.append(f"Set volume of {dev_name.replace('_',' ')} to {vol}%.")
                except ValueError:
                    responses.append(f"Invalid volume '{value}' for {dev_name.replace('_',' ')}.")
            elif action in ["get_status", "status"]:
                state_str = ", ".join(f"{k}={v}" for k, v in dev.items())
                responses.append(f"{dev_name.replace('_',' ')}: {state_str}")
            else:
                responses.append(f"Unknown action '{action}' for {dev_name.replace('_',' ')}.")

        # --- Generic / fallback ---
        else:
            if action in ["get_status", "status"]:
                state_str = ", ".join(f"{k}={v}" for k, v in dev.items())
                responses.append(f"{dev_name.replace('_',' ')}: {state_str}")
            else:
                responses.append(f"Action '{action}' not implemented for {dev_name.replace('_',' ')}.")

    return "\n".join(responses)
