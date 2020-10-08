# -*- coding: utf-8 -*-

# Octowire Framework
# Copyright (c) ImmunIT - Jordan Ovrè / Paul Duncan
# License: Apache 2.0
# Paul Duncan / Eresse <pduncan@immunit.ch>
# Jordan Ovrè / Ghecko <jovre@immunit.ch>

import math
import os

from tqdm import tqdm

from octowire_framework.module.AModule import AModule
from octowire.i2c import I2C


class FlashWrite(AModule):
    def __init__(self, owf_config):
        super(FlashWrite, self).__init__(owf_config)
        self.meta.update({
            'name': 'I2C flash write',
            'version': '1.1.0',
            'description': 'Program generic I2C flash memories',
            'author': 'Jordan Ovrè / Ghecko <jovre@immunit.ch>, Paul Duncan / Eresse <pduncan@immunit.ch>'
        })
        self.options = {
            "i2c_bus": {"Value": "", "Required": True, "Type": "int",
                        "Description": "I2C bus (0=I2C0 or 1=I2C1)", "Default": 0},
            "slave_address": {"Value": "", "Required": True, "Type": "hex",
                              "Description": "I2C target chip address", "Default": ""},
            "int_addr_length": {"Value": "", "Required": True, "Type": "int",
                                "Description": "Target chip internal address length (bytes)", "Default": 2},
            "firmware": {"Value": "", "Required": True, "Type": "file_r",
                         "Description": "Firmware to write into the I2C flash memory", "Default": ""},
            "start_chunk": {"Value": "", "Required": True, "Type": "int",
                            "Description": "Starting chunk address (1 chunk = 128 bytes)", "Default": 0},
            "i2c_baudrate": {"Value": "", "Required": True, "Type": "int",
                             "Description": "I2C frequency in Hz (supported values: 100000 or 400000)",
                             "Default": 400000},
        }
        self.advanced_options.update({
            "chunk_size": {"Value": "", "Required": True, "Type": "int",
                           "Description": "Flash chunk size", "Default": 128}
        })

    def writing_process(self):
        bus_id = self.options["i2c_bus"]["Value"]
        i2c_baudrate = self.options["i2c_baudrate"]["Value"]
        firmware = self.options["firmware"]["Value"]
        start_chunk_addr = self.options["start_chunk"]["Value"]
        chunk_size = self.advanced_options["chunk_size"]["Value"]
        slave_addr = self.options["slave_address"]["Value"]
        int_addr_length = self.options["int_addr_length"]["Value"]

        firmware_size = os.stat(firmware).st_size
        nb_of_chunks = math.ceil(firmware_size / chunk_size)

        # Setup and configure I2C interface
        i2c_interface = I2C(serial_instance=self.owf_serial, bus_id=bus_id)
        i2c_interface.configure(baudrate=i2c_baudrate)

        # Write data to the I2C flash
        with open(firmware, "rb") as f:
            for sector_nb in tqdm(range(start_chunk_addr, nb_of_chunks), desc="Writing",
                                  unit_scale=False, ascii=" #", unit_divisor=1,
                                  bar_format="{desc} : {percentage:3.0f}%[{bar}] {n_fmt}/{total_fmt} "
                                             "pages (" + str(chunk_size) + " bytes) "
                                             "[elapsed: {elapsed} left: {remaining}]"):
                chunk_addr = sector_nb * chunk_size
                data = f.read(chunk_size)
                # Write to the I2C chip
                i2c_interface.transmit(data=data, i2c_addr=slave_addr, int_addr=chunk_addr,
                                       int_addr_length=int_addr_length)
            self.logger.handle("Done!", self.logger.SUCCESS)

    def run(self):
        """
        Main function.
        Program generic I2C flash memories.
        :return: Nothing
        """
        # Detect and connect to the Octowire hardware. Set the self.owf_serial variable if found.
        self.connect()
        if not self.owf_serial:
            return
        try:
            self.writing_process()
        except (Exception, ValueError) as err:
            self.logger.handle(err, self.logger.ERROR)
