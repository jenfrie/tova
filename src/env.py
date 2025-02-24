import os

try:
    CIRCUIT_TTL = int(os.environ["CIRCUIT_TTL"])
    REQUEST_TIMEOUT = int(os.environ["REQUEST_TIMEOUT"])
    VAL_K = int(os.environ["VAL_K"])
    VAL_N = int(os.environ["VAL_N"])
    N_CIRCUITS = int(os.environ["N_CIRCUITS"])
    PREFIX_LEN = int(os.environ["PREFIX_LEN"])
    BUILD_INTERVAL = int(os.environ["BUILD_INTERVAL"])

except KeyError as e:
    print(f"missing env var: {e.args[0]}")

except ValueError as e:
    print(f"invalid env var: {e.args[0]}")
