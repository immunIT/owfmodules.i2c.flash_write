# -*- coding:utf-8 -*-

# Octowire Framework
# Copyright (c) Jordan Ovrè / Paul Duncan
# License: GPLv3
# Paul Duncan / Eresse <eresse@dooba.io>
# Jordan Ovrè / Ghecko <ghecko78@gmail.com

import shutil

from octowire_framework.module.AModule import AModule
from octowire.i2c import I2C


class FlashWrite(AModule):
    def __init__(self, owf_config):
        super(FlashWrite, self).__init__(owf_config)
        self.meta.update({
            'name': 'I2C write flash',
            'version': '1.0.0',
            'description': 'Write into I2C flash memory',
            'author': 'Jordan Ovrè <ghecko78@gmail.com> / Paul Duncan <eresse@dooba.io>'
        })
        self.options = {
            "i2c_bus": {"Value": "", "Required": True, "Type": "int",
                        "Description": "The octowire I2C device (0=I2C0 or 1=I2C1)", "Default": 0},
            "slave_address": {"Value": "", "Required": True, "Type": "hex",
                              "Description": "The I2C target chip address", "Default": ""},
            "int_addr_length": {"Value": "", "Required": True, "Type": "int",
                                "Description": "The internal chip address length (byte)", "Default": 2},
            "firmware": {"Value": "", "Required": True, "Type": "file_r",
                         "Description": "The firmware to write to the I2C flash memory", "Default": ""},
            "start_chunk": {"Value": "", "Required": True, "Type": "hex",
                            "Description": "The starting chunk address (1 chunk = 128 bytes)", "Default": 0x0000},
            "i2c_baudrate": {"Value": "", "Required": True, "Type": "int",
                             "Description": "set I2C baudrate in Hz (supported value: 100000 or 400000)",
                             "Default": 400000},
        }
        self.advanced_options.append({
            "chunk_size": {"Value": "", "Required": True, "Type": "hex",
                           "Description": "Flash chunk size", "Default": 0x80}
        })

    def writing_process(self):
        bus_id = self.get_option_value("i2c_bus")
        i2c_baudrate = self.get_option_value("i2c_baudrate")
        firmware = self.get_option_value("firmware")
        current_chunk_addr = self.get_option_value("start_chunk")
        chunk_size = self.get_advanced_option_value("chunk_size")
        slave_addr = self.get_option_value("slave_address")
        int_addr_length = self.get_option_value("int_addr_length")

        # Get the size width of the terminal for dynamic printing
        t_width, _ = shutil.get_terminal_size()

        # Set and configure I2C interface
        i2c_interface = I2C(serial_instance=self.owf_serial, bus_id=bus_id)
        i2c_interface.configure(baudrate=i2c_baudrate)

        # Writing data to the I2C flash
        with open(firmware, "rb") as f:
            while data := f.read(chunk_size):
                print(" " * t_width, end="\r", flush=True)
                print("[*] Writing to address: {}".format(hex(current_chunk_addr)), end="\r", flush=True)
                # Write to the I2C chip
                i2c_interface.transmit(data=data, i2c_addr=slave_addr, int_addr=current_chunk_addr,
                                       int_addr_length=int_addr_length)
                current_chunk_addr += chunk_size
            # Empty printing to avoid ugly output
            print()
            self.logger.handle("Done!", self.logger.SUCCESS)

    def run(self):
        """
        Main function.
        Write a firmware into an I2C flash.
        :return: Nothing
        """
        # Detect and connect to the octowire hardware. Set the self.owf_serial variable if found.
        self.connect()
        if not self.owf_serial:
            return
        try:
            self.writing_process()
        except (Exception, ValueError) as err:
            self.logger.handle(err, self.logger.ERROR)
