from ctypes import Structure, c_int, c_uint8, c_long, c_size_t, POINTER

c_time_t = c_long

class MBusFrame(Structure):
    def __str__(self):
        return "MBusFrame: XXX"

MBusFrame._fields_ = [
        ("start1",   c_uint8),
        ("length1",  c_uint8),
        ("length2",  c_uint8),
        ("start2",   c_uint8),
        ("control",  c_uint8),
        ("address",  c_uint8),
        ("control_infomation",  c_uint8),
        ("checksum", c_uint8),
        ("stop",     c_uint8),
        ("data",     c_uint8 * 252),
        ("data_size", c_size_t),
        ("type",      c_int),
        ("timestamp", c_time_t),
        ("next",      POINTER(MBusFrame))
]
