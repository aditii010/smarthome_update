# smart_home_api.py

device_states = {
    "bedroom_light": {"status": "off", "brightness": 100},
    "kitchen_light": {"status": "off", "brightness": 100},
    "livingroom_light": {"status": "off", "brightness": 100}
}

def control_device(device, location, action):
    location = location.lower().replace(" ", "_")
    if location in ["all", "all_rooms", "everywhere"]:
        keys = [key for key in device_states if key.endswith(f"_{device}")]
    else:
        key = f"{location}_{device}"
        keys = [key]

    responses = []
    for key in keys:
        if key not in device_states:
            responses.append(f"No such device found: {key.replace('_', ' ')}")
            continue

        if action == "turn_on":
            device_states[key]["status"] = "on"
            device_states[key]["brightness"] = 100
            responses.append(f"Turned on the {key.replace('_', ' ')}.")
        elif action == "turn_off":
            device_states[key]["status"] = "off"
            responses.append(f"Turned off the {key.replace('_', ' ')}.")
        elif action == "dim":
            device_states[key]["status"] = "on"
            device_states[key]["brightness"] = 30
            responses.append(f"Dimmed the {key.replace('_', ' ')} to 30% brightness.")
        elif action in ["get_status", "check_status", "status_check"]:
            state = device_states[key]["status"]
            brightness = device_states[key]["brightness"]
            responses.append(f"The {key.replace('_', ' ')} is {state} at {brightness}% brightness.")
        else:
            responses.append(f"Unknown action '{action}' for {key.replace('_', ' ')}.")

    return "\n".join(responses)
