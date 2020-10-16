import serial
import time

def main():
    with serial.Serial("COM3", 9600, timeout=0.5, parity=serial.PARITY_EVEN) as ser:
        for i in range(20):
            print(ser.is_open)
            ser.write(b"ST 7100\r\n")
            b = ser.readline()
            print("Read", b)
            time.sleep(1)
    pass

if __name__ == "__main__":
    main()