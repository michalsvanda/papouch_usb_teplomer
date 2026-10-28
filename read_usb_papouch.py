import re
import serial
import serial.tools.list_ports

# seriove cislo teplomeru, ktery se ma vycist
SERIAL_NO = 'PP69K2U2'
MSG_RE = re.compile(rb'\*B1E1([+-]\d{3}\.\d|Err)\r$')

def read_tmu(serial_no, max_msgs=4):
    # prochazi se vsechna zarizeni, hleda se to s udanym seriovym cislem
    port_name = next((p.device for p in serial.tools.list_ports.comports()
                      if p.serial_number == serial_no), None)
    if port_name is None:
        raise RuntimeError(f'Teploměr {serial_no} nenalezen')

    # timeout delší než perioda vysílání (~10 s)
    with serial.Serial(port_name, 9600, timeout=15) as port:
        port.dtr = True
        port.reset_input_buffer()          # zahodit staré/neúplné bajty
        for i in range(max_msgs):
            raw = port.read_until(b'\r')   # konec zprávy je CR, ne LF
            m = MSG_RE.search(raw)
            if not m:
                continue                   # neúplná zpráva (typicky ta první) nebo timeout
            if m.group(1) == b'Err':
                raise RuntimeError('Err: vadné čidlo nebo kabel')
            return float(m.group(1))
    raise RuntimeError('Nepřišla platná zpráva')

print(read_tmu(SERIAL_NO))
# zmerena teplota na stdout jako string s jednou desetinnou pozici, napr. "21.8"
