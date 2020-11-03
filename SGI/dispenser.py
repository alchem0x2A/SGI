"""Provide a simple method to connect to 
the dispenser via serial port
"""
import serial
import time

# Initialization required!


def make_droplet(port="COM3", baud=9600, timeout=0.5, parity="even"):
    if parity == "even":
        par = serial.PARITY_EVEN
    elif parity == "odd":
        par = serial.PARITY_ODD
    elif parity == "":
        par = serial.PARITY_NONE

    with serial.Serial(port, baud, timeout=timeout, parity=par) as ser:
        if not ser.is_open:
            result = False
        else:
            # Sequence for initializing COM
            ser.write(b"CR\r\n")
            b = ser.readline()
            print("Read", b)
            # TODO: error handling
            # b should be "CC"
            if "CC" not in b.decode("ascii"):
                return False
            # Start communication
            ser.write(b"ST 7100\r\n")
            b = ser.readline()
            print("Read", b)
            if "OK" in b.decode("ascii"):
                time.sleep(0.2)
                result = True
            else:
                result = False
    return result


def main():
    print(make_droplet())


if __name__ == "__main__":
    main()
