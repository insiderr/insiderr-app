import time


def utc_to_local(t):
    if time.localtime().tm_isdst:
        return t - time.altzone
    return t - time.timezone


