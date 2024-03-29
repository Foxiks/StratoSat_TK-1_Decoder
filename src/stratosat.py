import sys, socket, argparse, time, bitstring
from datetime import datetime

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--port", help="port")
parser.add_argument("-ip", "--ip", help="ip")

def agw_connect(s):
    s.send(b'\x00\x00\x00\x00k\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
    return

def start_socket(ip, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error:
        print('Failed to create socket')
        time.sleep(5)
        sys.exit()
    host = str(ip)
    try:
        remote_ip = socket.gethostbyname( host )
    except socket.gaierror:
        print('Hostname could not be resolved. Exiting')
        time.sleep(5)
        sys.exit()
    s.connect((remote_ip , port))
    print(f'Connected to {remote_ip}:{port}')
    print("")
    return s

def telemetry_decoder(data):
    data=data[32:]
    time_unix=datetime.utcfromtimestamp(int(bitstring.BitStream(hex=data[:8]).read('uintle'))).strftime('%Y-%m-%d %H:%M:%S')
    current=int(bitstring.BitStream(hex=data[8:12]).read('uintle'))*0.0000766
    current_pannels=int(bitstring.BitStream(hex=data[12:16]).read('uintle'))*0.00003076
    v_oneakb=int(bitstring.BitStream(hex=data[16:20]).read('uintle'))*0.00006928
    v_akball=int(bitstring.BitStream(hex=data[20:24]).read('uintle'))*0.00013856
    charge_all=int(bitstring.BitStream(hex=data[24:32]).read('uintle'))*0.00003076
    all_current=int(bitstring.BitStream(hex=data[32:40]).read('uintle'))*0.0000766
    t_x_p=bitstring.BitStream(hex=data[40:42]).read('int')
    t_x_n=bitstring.BitStream(hex=data[42:44]).read('int')
    t_y_p=bitstring.BitStream(hex=data[44:46]).read('int')
    t_y_n=bitstring.BitStream(hex=data[46:48]).read('int')
    t_z_p=bitstring.BitStream(hex=data[48:50]).read('int')
    t_z_n=bitstring.BitStream(hex=data[50:52]).read('int')
    t_bat1=bitstring.BitStream(hex=data[52:54]).read('int')
    t_bat2=bitstring.BitStream(hex=data[54:56]).read('int')
    orientation=bitstring.BitStream(hex=data[56:58]).read('int')
    if(int(orientation)==1):
        orientation='Working'
    elif(int(orientation)==0):
        orientation='Not working'
    else:
        orientation='Err!'
    cpu=bitstring.BitStream(hex=data[58:60]).read('uint')*0.390625
    obc=7476-int(bitstring.BitStream(hex=data[60:64]).read('uintle'))
    commu=1505-int(bitstring.BitStream(hex=data[64:68]).read('uintle'))
    rssi=int(bitstring.BitStream(hex=data[68:70]).read('int'))-99
    all_packets_rx=int(bitstring.BitStream(hex=data[70:74]).read('uintle'))
    all_packets_tx=int(bitstring.BitStream(hex=data[74:78]).read('uintle'))
    with open('tlm.txt', 'w') as out_tlm_file:
        out_tlm_file.write('Time (UTC): '+str(time_unix)+'\n')
        out_tlm_file.write('Total current: '+str(round(float(current), 2))+' A\n')
        out_tlm_file.write('Current from panels: '+str(round(float(current_pannels), 2))+' A\n')
        out_tlm_file.write('Voltage from one battery: '+str(round(float(v_oneakb), 2))+' V\n')
        out_tlm_file.write('Total voltage: '+str(round(float(v_akball), 2))+' V\n')
        out_tlm_file.write('Charging current amount: '+str(round(float(charge_all), 2))+' A\n')
        out_tlm_file.write('Amount of current consumption: '+str(round(float(all_current), 2))+' A\n')
        out_tlm_file.write('Temperature on X+ panel: '+str(t_x_p)+' C\n')
        out_tlm_file.write('Temperature on X- panel: '+str(t_x_n)+' C\n')
        out_tlm_file.write('Temperature on Y+ panel: '+str(t_y_p)+' C\n')
        out_tlm_file.write('Temperature on Y- panel: '+str(t_y_n)+' C\n')
        out_tlm_file.write('Temperature on Z+ panel: '+str(t_z_p)+(' C (NONE)\n'))
        out_tlm_file.write('Temperature on Z- panel: '+str(t_z_n)+' C\n')
        out_tlm_file.write('Temperature on battery 1: '+str(t_bat1)+' C\n')
        out_tlm_file.write('Temperature on battery 2: '+str(t_bat2)+' C\n')
        out_tlm_file.write('Orientation state: '+str(orientation)+'\n')
        out_tlm_file.write('CPU usage: '+str(round(float(cpu), 2))+'%\n')
        out_tlm_file.write('OBC reboots: '+str(obc)+'\n')
        out_tlm_file.write('CommU reboots: '+str(commu)+'\n')
        out_tlm_file.write('RSSI: '+str(rssi)+'\n')
        out_tlm_file.write('Number of received packets: '+str(all_packets_rx)+'\n')
        out_tlm_file.write('Number of transmitted packets: '+str(all_packets_tx)+'\n')

def main(s,name):
    while True:
        frame = s.recv(2048).hex()
        frame = frame[74:]
        reply = [frame[i:i+2] for i in range(0, len(frame), 2)]
        frame = ' '.join(reply)
        img_sync = frame[:11]
        if(str(img_sync) == str('02 00 3e 05')):
            if(int(str(frame.find(' ff d8 ff db '))) >= int(0)):
                first_offset=bitstring.BitStream(hex=str(frame[15:23])).read('uintle')
                name=str(time.strftime("%m-%d_%H-%M-%S"))
                x=int(str(frame[23:].find(' ff d8 ')))
                with open('out_image_'+str(name)+'.jpg', 'wb') as out_file:
                    out_file.write(int(frame[23+x:].replace(' ', ''),16).to_bytes(length=int(len(frame[23+x:].replace(' ', ''))/2), byteorder='big'))
                with open('data.ts', 'w') as o:
                    o.write('out_image_'+str(name)+'.jpg')
            elif(str(img_sync) == str('02 00 3e 05') and int(str(frame[23:].find(' ff d9 '))) <= int(0)):    
                offset=bitstring.BitStream(hex=str(frame[15:23])).read('uintle')
                try:
                    with open('out_image_'+str(name)+'.jpg', 'r+b') as out_file:
                        out_file.seek(offset-first_offset)
                        out_file.write(int(frame[23:].replace(' ', ''),16).to_bytes(length=int(len(frame[23:].replace(' ', ''))/2), byteorder='big'))
                except FileNotFoundError:
                    first_offset=offset
                    with open('out_image_'+str(name)+'.jpg', 'wb') as out_file:
                        out_file.seek(offset-first_offset)
                        out_file.write(int(frame[23:].replace(' ', ''),16).to_bytes(length=int(len(frame[23:].replace(' ', ''))/2), byteorder='big'))
            if(int(str(frame[23:].find(' ff d9 '))) >= int(0)):
                offset=bitstring.BitStream(hex=str(frame[15:23])).read('uintle')
                try:
                    with open('out_image_'+str(name)+'.jpg', 'r+b') as out_file:
                        out_file.seek(offset-first_offset)
                        out_file.write(int(frame[23:].replace(' ', ''),16).to_bytes(length=int(len(frame[23:].replace(' ', ''))/2), byteorder='big'))
                except FileNotFoundError:
                    first_offset=offset
                    with open('out_image_'+str(name)+'.jpg', 'wb') as out_file:
                        out_file.seek(offset-first_offset)
                        out_file.write(int(frame[23:].replace(' ', ''),16).to_bytes(length=int(len(frame[23:].replace(' ', ''))/2), byteorder='big'))
                name=str(time.strftime("%m-%d_%H-%M-%S"))

        elif(str(img_sync) == str('02 00 3e 20')):
            if(int(str(frame.find(' ff d8 ff '))) >= int(0)):
                first_offset=bitstring.BitStream(hex=str(frame[15:23])).read('uintle')
                name=str(time.strftime("%m-%d_%H-%M-%S"))
                x=int(str(frame[23:].find(' ff d8 ')))
                with open('Hout_image_'+str(name)+'.jpg', 'wb') as out_file:
                    out_file.write(int(frame[23+x:].replace(' ', ''),16).to_bytes(length=int(len(frame[23+x:].replace(' ', ''))/2), byteorder='big'))
                with open('data.ts', 'w') as o:
                    o.write('Hout_image_'+str(name)+'.jpg')
            elif(str(img_sync) == str('02 00 3e 20') and int(str(frame[23:].find(' ff d9 '))) <= int(0)):
                offset=bitstring.BitStream(hex=str(frame[15:23])).read('uintle')
                try:
                    with open('Hout_image_'+str(name)+'.jpg', 'r+b') as out_file:
                        out_file.seek(offset-first_offset)
                        out_file.write(int(frame[23:].replace(' ', ''),16).to_bytes(length=int(len(frame[23:].replace(' ', ''))/2), byteorder='big'))
                except FileNotFoundError:
                    first_offset=offset
                    with open('Hout_image_'+str(name)+'.jpg', 'wb') as out_file:
                        out_file.seek(offset-first_offset)
                        out_file.write(int(frame[23:].replace(' ', ''),16).to_bytes(length=int(len(frame[23:].replace(' ', ''))/2), byteorder='big'))
            if(int(str(frame[23:].find(' ff d9 '))) >= int(0)):
                offset=bitstring.BitStream(hex=str(frame[15:23])).read('uintle')
                try:
                    with open('Hout_image_'+str(name)+'.jpg', 'r+b') as out_file:
                        out_file.seek(offset-first_offset)
                        out_file.write(int(frame[23:].replace(' ', ''),16).to_bytes(length=int(len(frame[23:].replace(' ', ''))/2), byteorder='big'))
                except FileNotFoundError:
                    first_offset=offset
                    with open('Hout_image_'+str(name)+'.jpg', 'wb') as out_file:
                        out_file.seek(offset-first_offset)
                        out_file.write(int(frame[23:].replace(' ', ''),16).to_bytes(length=int(len(frame[23:].replace(' ', ''))/2), byteorder='big'))
                name=str(time.strftime("%m-%d_%H-%M-%S"))
        if(str(frame[:18]) == str('84 8a 82 86 9e 9c ')):
            telemetry_decoder(data=str(str(frame).replace(' ', '')))

if(__name__=='__main__'):
    name=f'Delete_this_file_{time.strftime("%m-%d_%H-%M")}'
    ip=parser.parse_args().ip
    port=parser.parse_args().port
    s=start_socket(ip=ip, port=int(port))
    agw_connect(s=s)
    main(s=s,name=name)