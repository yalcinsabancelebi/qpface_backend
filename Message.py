
import json
from azure.cosmos import CosmosClient
import Helper
from azure.cosmos import CosmosClient
from azure.messaging.webpubsubservice import WebPubSubServiceClient
import uuid
import datetime
import json
import uuid
import Notifications
from azure.messaging.webpubsubservice import WebPubSubServiceClient

async def get_user_info(username):
    query = f"SELECT c.token, c.firstname, c.lastname, c.profile_pic FROM c WHERE c.username='{username}'"
    items = [item for item in users_container.query_items(query=query, enable_cross_partition_query=True)]
    return items[0] if items else None



with open('config.json', 'r') as config_file:
    config = json.load(config_file)

cosmos_client = CosmosClient(config['ACCOUNT_HOST'], config['ACCOUNT_KEY'])
database = cosmos_client.create_database_if_not_exists(config['DATABASE_ID'])
users_container = database.get_container_client('Users')
wss_container = database.get_container_client('wss')
connection_string = "Endpoint=https://qpface.webpubsub.azure.com;AccessKey=cqOkK9WXEGuAbnHyoKEchjHdb/Rcw3Ua6ug7CSS3CjA=;Version=1.0;"

messages_container = database.get_container_client("Messages")


async def message_fetch(sender, receiver):
    try:
        # İlk sorguyu dene
        fetch_query = f"""
            SELECT c.id, c.sender, c.receiver, c.post_type, c.post_id, c.message, c.timestamp FROM c 
            WHERE (c.receiver='{sender}' AND c.sender='{receiver}') 
               OR (c.sender='{sender}' AND c.receiver='{receiver}')
        """
        fetch_items = list(messages_container.query_items(query=fetch_query, enable_cross_partition_query=True))
    except Exception as e:
        # Eğer ilk sorgu hata verirse, ikinci sorguyu dene
        fetch_query = f"""
            SELECT c.id, c.sender, c.receiver, c.message, c.timestamp FROM c 
            WHERE (c.receiver='{sender}' AND c.sender='{receiver}') 
               OR (c.sender='{sender}' AND c.receiver='{receiver}')
        """
        fetch_items = list(messages_container.query_items(query=fetch_query, enable_cross_partition_query=True))

    hub_name = Helper.generate_unique_key(sender, receiver)

    websocketclient = WebPubSubServiceClient.from_connection_string(connection_string, hub=hub_name)
    token = websocketclient.get_client_access_token()
    websocket_url = token['url']

    receiver_info = await get_user_info(receiver)
    receiver_info['websocket_url'] = websocket_url

    # Mevcut olan alanları ekle ve sırala
    sorted_items = sorted(
        [
            {key: item[key] for key in item}
            for item in fetch_items
        ], 
        key=lambda x: x['timestamp'], 
        reverse=False
    )

    return json.dumps({"user_info": receiver_info, "messages": sorted_items})


  
  
  
  
  
async def send(sender, receiver, message,post_type=None,post_id=None):
    message_id = str(uuid.uuid4())
    utc_offset = datetime.timedelta(hours=3)
    now_utc3 = datetime.datetime.utcnow() + utc_offset
    timestamp = now_utc3.strftime('%Y-%m-%d %H:%M:%S')

    hub_name = Helper.generate_unique_key(sender, receiver)
    websocketclient = WebPubSubServiceClient.from_connection_string(connection_string, hub=f"{hub_name}")
    
    sender_info = await get_user_info(sender)
    receiver_info = await get_user_info(receiver)
    
    if("https://qpface.blob.core.windows.net" in message):
        message_data = {
            "id": message_id,
            "sender": sender,
            "receiver": receiver,
            "post_type":post_type,
            "post_id":post_id,
            "message": message,
            "timestamp": timestamp
        }
        
        message_ui_data = {
            "id": message_id,
            "sender": sender,
            "sender_token": sender_info['token'],
            "sender_fullname": sender_info['firstname'] + ' ' + sender_info['lastname'],
            "sender_profile_pic": sender_info['profile_pic'],
            "post_type":post_type,
            "post_id":post_id,
            "receiver": receiver,
            "receiver_token": receiver_info['token'],
            "receiver_fullname": receiver_info['firstname'] + ' ' + receiver_info['lastname'],
            "receiver_profile_pic": receiver_info['profile_pic'],
            "message": message,
            "timestamp": timestamp,
        }


    else:
        message_data = {
            "id": message_id,
            "sender": sender,
            "receiver": receiver,
            "message": message,
            "timestamp": timestamp
        }
        
        message_ui_data = {
            "id": message_id,
            "sender": sender,
            "sender_token": sender_info['token'],
            "sender_fullname": sender_info['firstname'] + ' ' + sender_info['lastname'],
            "sender_profile_pic": sender_info['profile_pic'],
            "receiver": receiver,
            "receiver_token": receiver_info['token'],
            "receiver_fullname": receiver_info['firstname'] + ' ' + receiver_info['lastname'],
            "receiver_profile_pic": receiver_info['profile_pic'],
            "message": message,
            "timestamp": timestamp,
        }

    websocketclient.send_to_all(message_ui_data)

    messages_container.create_item(body=message_data)




    websocketclient.send_to_all(message_ui_data)
    # Helper.firebase_fcm_notification(receiver_info['token'], f"{sender} sana bir mesaj gönderdi.")

    return json.dumps(message_ui_data)






def delete_message(sender, receiver, message_id=None, wipeall=False):
    if wipeall:
        try:
            query = f"""
                SELECT c.id, c.sender FROM c 
                WHERE 
                    (c.sender='{sender}' AND c.receiver='{receiver}') OR 
                    (c.sender='{receiver}' AND c.receiver='{sender}')
            """
            items = list(messages_container.query_items(query=query, enable_cross_partition_query=True))
            
            for item in items:
                messages_container.delete_item(item=item['id'], partition_key=item['sender'])

            return json.dumps({"Result": "Tüm mesajlar başarıyla silindi!"})
        
        except Exception as e:
            return json.dumps({"Result": str(e)})
    else:
        try:
            # Mesajı bulmak için sorgu oluştur
            query = f"""
                SELECT c.id, c.sender FROM c 
                WHERE 
                    c.id='{message_id}' AND 
                    ((c.sender='{sender}' AND c.receiver='{receiver}') OR 
                    (c.sender='{receiver}' AND c.receiver='{sender}'))
            """
            items = list(messages_container.query_items(query=query, enable_cross_partition_query=True))
            
            if not items:
                return json.dumps({"Result": f"Message {message_id} not found."})

            # Mesajı sil
            for item in items:
                messages_container.delete_item(item=item['id'], partition_key=item['sender'])
                
                
            message_ui_data = {
                "status": "deleted",
                "message_id": message_id
            }
            
            hub_name = Helper.generate_unique_key(sender, receiver)
            websocketclient = WebPubSubServiceClient.from_connection_string(connection_string, hub=f"{hub_name}")
            websocketclient.send_to_all(message_ui_data)
                
            return json.dumps({"Result": f"Message {message_id} has been deleted."})
        
        except Exception as e:
            return json.dumps({"Result": str(e)})


async def message_list(sender):
    query = f"SELECT c.sender, c.receiver, c.timestamp FROM c WHERE c.sender='{sender}' OR c.receiver='{sender}'"
    items = list(messages_container.query_items(query=query, enable_cross_partition_query=True))

    user_timestamps = {}

    for item in items:
        if item['sender'] != sender:
            if item['sender'] not in user_timestamps or item['timestamp'] > user_timestamps[item['sender']]:
                user_timestamps[item['sender']] = item['timestamp']
        if item['receiver'] != sender:
            if item['receiver'] not in user_timestamps or item['timestamp'] > user_timestamps[item['receiver']]:
                user_timestamps[item['receiver']] = item['timestamp']

    sorted_users = sorted(user_timestamps.keys(), key=lambda user: user_timestamps[user], reverse=True)
    
    user_info_list = []
    
    for username in sorted_users:
        user_info = await get_user_info(username)
        if user_info:
            user_info_list.append({
                "username": username,
                "fullname": f"{user_info['firstname']} {user_info['lastname']}",
                "profile_pic": user_info['profile_pic']
            })

    return json.dumps(user_info_list)

