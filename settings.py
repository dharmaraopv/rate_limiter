import os
from dotenv import load_dotenv

ENV = os.getenv("ENV", "in_mem")
load_dotenv(f"./env/{ENV}")

print (f"ENV: {ENV}")

STORAGE_TYPE = os.getenv("STORAGE_TYPE", "in_memory")  # redis or in_memory
REDIS_URL = os.getenv("REDIS_URL", "redis://default:redispw@localhost:55000")
IN_MEM_CAPACITY = int(os.getenv("IN_MEM_CAPACITY", 1000))  # Number of keys to store in memory
NUM_SLOTS = int(os.getenv("NUM_SLOTS", 10))  # Number of slots to divide the interval into
DO_UPDATES_IN_BACKGROUND = os.getenv("DO_UPDATES_IN_BACKGROUND", "YES") == "YES"

print(f"STORAGE_TYPE: {STORAGE_TYPE}")
print(f"REDIS_URL: {REDIS_URL}")
print(f"IN_MEM_CAPACITY: {IN_MEM_CAPACITY}")
print(f"NUM_SLOTS: {NUM_SLOTS}")
print(f"DO_UPDATES_IN_BACKGROUND: {DO_UPDATES_IN_BACKGROUND}")
