'''
Created on Mar 8, 2020

@author: hwase
'''
import yagmail


if __name__ == '__main__':
    contents = ['This is the body, and here is just text http://somedomain/image.png',
                'You can find an audio file attached.', '/local/path/song.mp3']
    sender_email = "insider4trader@gmail.com"
    # yagmail.register(sender_email, 'vwxaotmoawdfwxzx')  # trader@2020
    yagmail.SMTP(sender_email, password="vwxaotmoawdfwxzx").send('roysten.tan@gmail.com', 'test', contents)
