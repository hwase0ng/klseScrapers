"""
Created on Mar 8, 2020

@author: hwase
"""
import settings as S
import yagmail


if __name__ == '__main__':
    contents = ['This is the body, and here is just text http://somedomain/image.png',
                'You can find an audio file attached.', '/local/path/song.mp3']
    # yagmail.register(sender_email, 'vwxaotmoawdfwxzx')  # trader@2020
    yagmail.SMTP(S.MAIL_SENDER, S.MAIL_PASSWORD).send('roysten.tan@gmail.com', 'test', contents)
