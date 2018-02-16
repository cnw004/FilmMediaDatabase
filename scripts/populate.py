#!/usr/bin/env python
import os
import sys
import subprocess
import json
import threading
import timeit
import textwrap

from logger import Logger, Msg
import psycopg2

def process(img):
    '''
    Pipes a filename into darknet for recognition

    :param: img The path to the image
    '''
    DARKNET_PROC.stdin.write(img + '\n')
    DARKNET_PROC.stdin.flush()


def traverse():
    '''
    Traverses all of the files in media_dir, and checks if a given
    one has been processed already. If it has not, adds the file
    for processing. Needs to be run in a thread

    :param: media_dir The directory to recursively check
    '''
    with open(os.path.join(os.path.curdir, 'files.txt')) as file_list:
        process(file_list.read())
    LOGGER.log(
        Msg(
            'traverse',
            'Added files',
            prefix_color='green'
        ),
        tag_id='LIST_T_DISP'
    )


def upload():
    '''
    Uploads data that is generated by the DARKNET_PROC to the
    database. Needs to be run in a thread
    '''
    step = 0

    movies = {}

    cur_oclc_id = ''
    cur_line_no = ''

    with open(os.path.join(THIS_FILE, '..', 'logs', 'populate.log'), 'w+') as log:
        while DARKNET_PROC.poll() is None:
            recognized_object = DARKNET_PROC.stdout.readline().rstrip()
            
            if recognized_object == '':
                break

            # JSON data
            data = json.loads(recognized_object)

            oclc_id = data['oclc_id']
            line_no = data['db_line_id']

            # Populate cache
            if oclc_id not in movies.keys():
                movies[oclc_id] = {}

            if line_no not in movies[oclc_id].keys():
                try:
                    # Get DB Line ID
                    READ_CUR_UPLOAD_T.execute('''
                        SELECT db_line_id FROM media_text WHERE oclc_id = %(oclc_id)s AND line_number = %(db_line_id)s LIMIT 1;
                    ''', data)
                    res = READ_CUR_UPLOAD_T.fetchone()
                    movies[oclc_id][line_no] = res[0]
                except Exception as e:
                    if oclc_id != cur_oclc_id:
                        log.write('{oclc_id}\n'.format(**locals()))
                        cur_oclc_id = oclc_id
                    # log.write('    {}\n'.format(e.message))
                    continue

            data['db_line_id'] = movies[oclc_id][line_no]

            # Insert new data
            WRITE_CUR_UPLOAD_T.execute('''
                INSERT INTO media_recognized_objects
                (db_line_id, text_label, confidence, bounding_left, bounding_right, bounding_top, bounding_bottom)
                VALUES
                (%(db_line_id)s, %(label)s, %(confidence)s, %(l)s, %(r)s, %(t)s, %(b)s)
                ON CONFLICT DO NOTHING;
                ''', data)

            LOGGER.log(
                Msg(
                    'upload',
                    '{step} entered into DB ({oclc_id}/{line_no})'.format(**locals()),
                    prefix_color='blue'
                ),
                tag_id='UPLOAD_T_COUNT'
            )
            if step % 100 == 0 and step > 0:
                CONN.commit()
            if cur_oclc_id != oclc_id or cur_line_no != line_no:
                cur_oclc_id = oclc_id
                cur_line_no = oclc_id
                step += 1

        # commit all remaining lines
        LOGGER.log(
            Msg(
                'upload',
                '{step} entered into DB'.format(**locals()),
                prefix_color='blue'
            ),
            tag_id='UPLOAD_T_COUNT'
        )
        CONN.commit()
        CONN.close()


if __name__ == '__main__':

    #==============================
    #      LOGGER/DB SETUP
    #==============================

    LOGGER = Logger()

    LOGGER.log(Msg('populate.py', 'Populate Database'))
    LOGGER.log(Msg('populate.py', '-----------------'))

    THIS_FILE = os.path.dirname(os.path.realpath(__file__))
    CFG_FILE = os.path.join(THIS_FILE, '..', 'src', 'dbConfig.json')

    # Load the config file
    with open(CFG_FILE) as DB_CFG:
        PG_CFG = json.loads(DB_CFG.read())

    DB_CFG = {
        'dbname': 'filmtvse',
        'user': PG_CFG["DATABASE"]["username"],
        'password': PG_CFG["DATABASE"]["password"],
        'host': PG_CFG["DATABASE"]["host"],
        'port': PG_CFG["DATABASE"]["port"]
    }

    LOGGER.tag('db_login').log(Msg('DB Login', 'Logging into DB...', prefix_color='yellow'))
    try:
        CONN = psycopg2.connect(**DB_CFG)
        READ_CUR_LIST_T = CONN.cursor()
        READ_CUR_UPLOAD_T = CONN.cursor()
        WRITE_CUR_UPLOAD_T = CONN.cursor()
        psycopg2.extensions.register_type(psycopg2.extensions.UNICODE, READ_CUR_LIST_T)
        psycopg2.extensions.register_type(psycopg2.extensions.UNICODE, READ_CUR_UPLOAD_T)
        psycopg2.extensions.register_type(psycopg2.extensions.UNICODE, WRITE_CUR_UPLOAD_T)
    except Exception as err:
        LOGGER.log(
            Msg(
                'DB Login',
                'Login Failed: {err.message}'.format(**locals()),
                prefix_color='yellow',
                msg_color='red'
            ),
            tag_id='db_login'
        )
        sys.exit(1)
    LOGGER.log(
        Msg(
            'DB Login',
            'Login Success!'.format(**locals()),
            prefix_color='yellow',
            msg_color='green'
        ),
        tag_id='db_login'
    )

    #==============================
    #         DATA ENTRY
    #==============================

    START = timeit.default_timer()

    # Start thread for adding all necessary files
    # LIST_T = threading.Thread(target=traverse, args=[sys.argv[1]])
    # LIST_T.start()
    FIND_PATH = os.path.join(sys.argv[1], '*')
    LIST_T = subprocess.Popen(
        'find {} -maxdepth 1 -type f \( -iname \*.jpg -o -iname \*.png \) && exit 0'.format(FIND_PATH),
        shell=True, 
        stdout=subprocess.PIPE
    )
    LOGGER.tag('LIST_T_WAIT').log(Msg('traverse', 'Traversing directories', prefix_color='green'))
    LOGGER.wait('LIST_T_WAIT', Msg('traverse', 'Traversing directories', prefix_color='green'), LIST_T)
    LOGGER.tag('LIST_T_DISP').log(Msg('traverse', '', prefix_color='green'))


    #==============================
    #       DARKNET SETUP
    #==============================

    # Start darknet
    DARKNET_DIR = os.path.join(THIS_FILE, '..', 'submodules', 'darknet')
    DARKNET = os.path.join('.', 'darknet')
    CMD = './darknet detector test cfg/coco.data cfg/yolo.cfg yolo.weights'
    DARKNET_PROC = subprocess.Popen(
        CMD,
        cwd=DARKNET_DIR,
        shell=True,
        stdin=LIST_T.stdout,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Start thread for uploading to DB
    UPLOAD_T = threading.Thread(target=upload)
    UPLOAD_T.start()
    LOGGER.tag('UPLOAD_T_WAIT').log(Msg('upload', 'Entering into DB', prefix_color='blue'))
    LOGGER.wait('UPLOAD_T_WAIT', Msg('upload', 'Entering into DB', prefix_color='blue'), UPLOAD_T)
    LOGGER.tag('UPLOAD_T_COUNT').log(Msg('upload', '0 Entered into DB', prefix_color='blue'))

    # Start thread for adding all necessary files
    LIST_T = threading.Thread(target=traverse, args=[])
    LOGGER.tag('LIST_T_WAIT').log(Msg('traverse', 'Traversing directories', prefix_color='green'))
    LOGGER.wait('LIST_T_WAIT', Msg('traverse', 'Traversing directories', prefix_color='green'), LIST_T)
    LOGGER.tag('LIST_T_DISP').log(Msg('traverse', '', prefix_color='green'))
    LIST_T.start()

    # Start thread for adding all necessary files
    T1 = threading.Thread(target=traverse, args=[])
    LOGGER.tag('T1_WAIT').log(Msg('traverse', 'Traversing directories', prefix_color='green'))
    LOGGER.wait('T1_WAIT', Msg('traverse', 'Traversing directories', prefix_color='green'), T1)
    LOGGER.tag('T1_DISP').log(Msg('traverse', '', prefix_color='green'))
    T1.start()

    # Wait for threads to finish
    LIST_T.wait()
    LOGGER.log(
        Msg(
            'traverse',
            'Done in {}s'.format(timeit.default_timer() - START),
            prefix_color='green',
            msg_color='green'
        ),
        tag_id='LIST_T_WAIT'
    )

    DARKNET_PROC.wait()

    UPLOAD_T.join()
    LOGGER.log(
        Msg(
            'upload',
            'Done in {}s'.format(timeit.default_timer() - START),
            prefix_color='blue',
            msg_color='green'
        ),
        tag_id='UPLOAD_T_WAIT'
    )

    LOGGER.log(Msg('populate.py', '-----------------'))
    LOGGER.log(Msg('populate.py', 'Done.'))
