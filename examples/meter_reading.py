#!/usr/bin/env python3
# ------------------------------------------------------------------------------
# Copyright (C) 2012, Robert Johansson <rob@raditex.nu>, Raditex Control AB
# All rights reserved.
# ------------------------------------------------------------------------------

"""
meter reading: collect data from a meter device and write it to a CSV file
"""

import argparse
import csv
import ctypes
import datetime

from collections import defaultdict
from mbus.MBus import MBus
from mbus import MBusLowLevel

parser = argparse.ArgumentParser(description="Collect data from a meter device and write it to a CSV file")
parser.add_argument('device', help="Serial port device (e.g. /dev/ttyUSB0")
parser.add_argument('speed', help="Serial baud rate (e.g. 2400)", type=int)
parser.add_argument('address', help="MBus address (primary or secondary, e.g. 15, 10264864496A8804)")
parser.add_argument('output_file', help="CSV file to write with the output")
parser.add_argument('--units_code', type=int,
                    help="Output only meter readings with the specified units code, in abbreviated collated format")
args = parser.parse_args()

debug = True

mbus = MBus(device=args.device)
mbus._libmbus.serial_set_baudrate(mbus.handle, args.speed)

if debug:
    print("mbus = " + str(mbus))

mbus.connect()

if debug:
    print("mbus = " + str(mbus))

if mbus._libmbus.is_secondary_address(args.address.encode('ascii')):
    address = mbus.MBUS_ADDRESS_NETWORK_LAYER
    mbus.select_secondary_address(args.address)
else:
    address = int(args.address)

# mbus.send_request_frame(mbus.MBUS_ADDRESS_NETWORK_LAYER)
# reply = mbus.recv_frame()

frame = MBusLowLevel.MBusFrame()
assert mbus._libmbus.sendrecv_request(mbus.handle, address, ctypes.byref(frame), 32) == 0

if debug:
    print("frame =", frame)

i = 0
all_records_rows = []
meter_readings = defaultdict(lambda: [None, None])
units_name = None

while bool(frame):
    frame_data = mbus.frame_data_parse(frame)
    if debug:
        print("frame_data =", frame_data)

    assert frame_data.type == MBusLowLevel.MBUS_DATA_TYPE_VARIABLE
    record = frame_data.data_var.record.contents

    while record is not None:
        i += 1

        if not bool(record.next):
            break

        if record.drh.dib.dif in (MBusLowLevel.MBUS_DIB_DIF_MANUFACTURER_SPECIFIC,
                                  MBusLowLevel.MBUS_DIB_DIF_MORE_RECORDS_FOLLOW):
            continue

        record_number = mbus._libmbus.data_record_storage_number(record)
        tariff = mbus._libmbus.data_record_tariff(record)
        units = (record.drh.vib.vif & MBusLowLevel.MBUS_DIB_VIF_WITHOUT_EXTENSION)
        value = mbus._libmbus.data_record_value(record).decode('ascii')
        device_or_tariff_str = tariff if tariff >= 0 else mbus._libmbus.data_record_device(record)

        all_records_rows.append([address, i,
            mbus._libmbus.data_record_function(record).decode('ascii'),
            record_number,
            device_or_tariff_str,
            mbus._libmbus.data_record_unit(record).decode('ascii'),
            units,
            value,
            datetime.datetime.fromtimestamp(record.timestamp).isoformat() if record.timestamp > 0 else ""])
        
        if args.units_code is not None and units == args.units_code:
            units_name = mbus._libmbus.data_record_unit(record)
            meter_readings[record_number][1] = value  # raw, as a string
        elif units >= 0x6c and units <= 0x6d:
            meter_readings[record_number][0] = value

        record = record.next.contents

    # xml_buff = mbus.frame_data_xml(frame_data)
    # print("xml_buff =", xml_buff)
    with open(args.output_file, 'w') as output_handle:
        writer = csv.writer(output_handle)
        if args.units_code is None:
            writer.writerow(['address', 'record index', 'function', 'record number', 'device',
                             'units', 'units code', 'value', 'timestamp'])
            writer.writerows(all_records_rows)
        else:
            writer.writerow(['address', 'record number', 'time point', units_name])
            for record_number, (time_point, selected_value) in meter_readings.items():
                writer.writerow([address, record_number, time_point, selected_value])

    mbus.frame_data_free(frame_data)

    # import pdb; pdb.set_trace()
    if not bool(frame.next):
        break

    frame = frame.next.contents

mbus.disconnect()
