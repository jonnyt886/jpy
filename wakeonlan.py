#!/usr/bin/env python2
import struct, socket

def wakeonlan(ethernet_address):
	# construct a six-byte hardware address
	addr_byte = ethernet_address.split(':')
	hw_addr = struct.pack('BBBBBB', 
	 int('0x' + addr_byte[0], 16),
	 int('0x' + addr_byte[1], 16),
	 int('0x' + addr_byte[2], 16),
	 int('0x' + addr_byte[3], 16),
	 int('0x' + addr_byte[4], 16),
	 int('0x' + addr_byte[5], 16)
	)

	# build the wake-on-lan "magic packet"...
	msg = '\xff' * 6 + hw_addr * 16

	# ...and send it to the broadcast address using udp
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
	s.sendto(msg, ('<broadcast>', 7))
	s.close()

#wakeonlan('d0:27:88:61:39:b8')
