# pip install smartcard
from smartcard.Exceptions import CardConnectionException, NoCardException
from smartcard.System import *
from smartcard import util
import vlc  # pip install python-vlc
import time
from configparser import ConfigParser

class MustBeEvenException(Exception):
    pass

class VlcPlayer:

    def __init__(self, *args):
        if args:
            instance = vlc.Instance(*args)
            print("인스턴스 생성")
            self.media = instance.media_player_new()
        else:
            self.media = vlc.MediaPlayer()
            print("플레이어 생성")

    def set_uri(self, mrl):
        self.media.set_mrl(mrl)


    def play(self, path=None):
        if path:
            self.set_uri(path)
            return self.media.play()
        else:
            return self.media.play()

    def get_length(self):
        return self.media.get_length() / 1000

    def stop(self):
        return self.media.stop()

    def fullscreen(self):
        return self.media.set_fullscreen(True)

    def add_callback(self, event_type, callback):
        self.media.event_manager().event_attach(event_type, callback)

COMMAND = [0xFF, 0xCA, 0x00, 0x00, 0x00]
config = ConfigParser()
video = config.read('config.ini')
def my_call_back(event):
    global status
    status = 1

def stringParser(dataCurr):
    # --------------String Parser--------------#
    # ([85, 203, 230, 191], 144, 0) -> [85, 203, 230, 191]
    if isinstance(dataCurr, tuple):
        temp = dataCurr[0]
        code = dataCurr[1]
    # [85, 203, 230, 191] -> [85, 203, 230, 191]
    else:
        temp = dataCurr
        code = 0

    dataCurr = ''

    # [85, 203, 230, 191] -> bfe6cb55 (int to hex reversed)
    for val in temp:
        # dataCurr += (hex(int(val))).lstrip('0x') # += bf
        dataCurr += format(val, '#04x')[2:]  # += bf

    # bfe6cb55 -> BFE6CB55
    dataCurr = dataCurr.upper()

    # if return is successful
    if (code == 144):
        return dataCurr

if "__main__" == __name__:
    # get and print a list of readers attached to the system
    sc_readers = readers()
    print(sc_readers)

    # create a connection to the first reader
    first_reader = sc_readers[0]
    connection = first_reader.createConnection()

    # get ready for a command
    get_uid = util.toBytes("FF CA 00 00 00")
    alt_get_uid = [0xFF, 0xCA, 0x00, 0x00, 0x00] # alternative to using the helper
    while True:
        try:
            # send the command and capture the response data and status
            connection.connect()
            data, sw1, sw2 = connection.transmit(get_uid)
            connection.transmit(COMMAND)
            resp = connection.transmit([0xFF, 0xB0, 0x00, int(4), 0x04])
            dataCurr = stringParser(resp)
            while True:
                if (dataCurr is not None):
                    break
                else:
                    print("Something went wrong. Page " + str(4))
                    break
            # print the response
            uid = util.toHexString(data)
            status = util.toHexString([sw1, sw2])


        except NoCardException:
            print("ERROR: Card not present")
            dataCurr = 0

        except CardConnectionException:
            print("ERROR: Card Connection Error")
            dataCurr = 0
        media_file = ""

        if dataCurr:
            media_file = config.get(dataCurr, 'media_file')

        else:
            media_file = ""


        if media_file:
            player = VlcPlayer()
            player.fullscreen()
            player.add_callback(vlc.EventType.MediaPlayerStopped, my_call_back)
            print("파일을 재생하겠습니다")
            player.play(media_file)
            print(media_file)
            status = 0

            while dataCurr:
                try:
                    # send the command and capture the response data and status
                    connection.connect()
                    data, sw1, sw2 = connection.transmit(get_uid)
                    connection.transmit(COMMAND)
                    resp = connection.transmit([0xFF, 0xB0, 0x00, int(4), 0x04])
                    dataCurr = stringParser(resp)
   
                    if status==1:
                        print("영상종료")
                        time.sleep(1)
                        player.stop()  # stop을 통해 열려있는 player 닫기
                        break

                except NoCardException:
                    print("ERROR: Card not present")
                    dataCurr = 0
                    print(dataCurr)
                    print(status)
                    break

                except CardConnectionException:
                    print("ERROR: Card Connection Error")
                    dataCurr = 0
                    print(dataCurr)
                    print(status)
                    break

            while status == 0:

                # 파일 빈 값 입력 시(NFC 제거 시) 종료
                if dataCurr == 0:
                    print("NFC제거")
                    time.sleep(1)
                    player.stop()  # stop을 통해 열려있는 player 닫기
                    break
                elif dataCurr is None:
                    print("NFC제거")
                    time.sleep(1)
                    player.stop()  # stop을 통해 열려있는 player 닫기
                    break
                else:
                    pass

