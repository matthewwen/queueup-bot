import os
from typing import List

from firebase_admin.firestore import firestore
from google.cloud.firestore_v1.watch import DocumentChange

from bot264.discord_wrapper import create_server_db, create_db


def get_db():
    reference = os.getenv('REFERENCE', None)
    if reference is None:
        return None
    return firestore.Client().collection(u'servers').document(reference).collection('queueup-bot')


def get_server_db():
    try:
        return firestore.Client().collection(u'discord').document(u'queueup-bot').collection('servers')
    except:
        return None


class Database:
    db: firestore.CollectionReference = None
    servers: firestore.CollectionReference = None
    snapshot: firestore.Watch = None

    @staticmethod
    def init():
        Database.db = get_db()
        Database.servers = get_server_db()
    
    @staticmethod
    async def can_access(user):
        print(user)
        return -1


    @staticmethod
    def on_set(server_id, attributes):
        connection = create_db(force_create=True, return_connection=True)
        if connection:
            cursor = connection.cursor()
            command = f"""DELETE FROM teaching_roles WHERE server_id={server_id};"""
            cursor.execute(command)
            command = f"""DELETE FROM queues WHERE server_id={server_id};"""
            cursor.execute(command)

            if 'queues' in attributes:
                for k, v in attributes['queues'].items():
                    v = "NULL" if v is None else v
                    command = f"""REPLACE INTO queues (queue_channel_id, history_channel_id, server_id) 
                    VALUES({k}, {v}, {server_id})"""
                    cursor.execute(command)

            if 'ta_roles' in attributes:
                for k, _ in attributes['ta_roles'].items():
                    command = f"""
                    REPLACE INTO teaching_roles (teaching_role_id, assigned_level, server_id) 
                    VALUES({k}, 0, {server_id}); 
                    """
                    cursor.execute(command)
            
            if 'bot' in attributes:
                bot_channel_id = attributes['bot']
                command = f"""
                REPLACE INTO servers (server_id, bot_channel_id) VALUES({server_id}, {bot_channel_id});
                """
                cursor.execute(command)

            if 'waiting' in attributes:
                waiting_room = attributes['waiting'] 
                command = f"""
                REPLACE INTO servers (server_id,  waiting_room_id) 
                VALUES({server_id}, {waiting_room}); 
                """
                cursor.execute(command)
            cursor.close()
            connection.commit()
            connection.close()

        connection = create_server_db(server_id, force_create=True, return_connection=True)
        if connection:
            cursor = connection.cursor()
            command = """DELETE FROM rooms WHERE room_voice_channel_id NOT NULL;"""
            cursor.execute(command)

            # The room_text_channel_id is depreciated 
            if 'rooms' in attributes:
                for k, v in attributes['rooms'].items():
                    v = "NULL" if v is None else v
                    command = f"""
                    REPLACE INTO rooms (room_voice_channel_id, room_text_channel_id) VALUES({k}, {v});
                    """
                    cursor.execute(command)
            connection.commit()
            cursor.close()
            connection.close()