DOMAIN = "xthings_lock"
PLATFORMS = ["lock", "sensor", "binary_sensor"]

CONF_EMAIL = "email"
CONF_PASSWORD = "password"

APP_ID = "13ca0de1e6054747c44665ae13e36c2c"
CLIENT_ID = "1375ac0809878483ee236497d57f371f"
TOKEN_URL = "https://uemc.u-tec.com/app/token"
LOGIN_URL = "https://cloud.u-tec.com/app/user/login"
ADDRESS_URL = "https://cloud.u-tec.com/app/address"
ROOM_URL = "https://cloud.u-tec.com/app/room"
DEVICE_LIST_URL = "https://cloud.u-tec.com/app/device/list"
DEVICE_GET_URL = "https://cloud.u-tec.com/app/device/get"

USER_AGENT = "U-tec/2.1.14 (iPhone; iOS 15.1; Scale/3.00)"
DEFAULT_SCAN_INTERVAL = 60

# Observed on Bolt SE: 2 == locked while BLE also reported locked.
LOCKED_VALUES = {1, 2}
UNLOCKED_VALUES = {0}

BATTERY_LEVEL = {-1: "Depleted", 0: "Replace", 1: "Low", 2: "Medium", 3: "High"}
