import datetime
from azure.cosmos import CosmosClient
import json
import uuid
import Helper

with open('config.json', 'r') as config_file:
    config = json.load(config_file)
    
    
cosmos_client = CosmosClient(config['ACCOUNT_HOST'], config['ACCOUNT_KEY'])
database = cosmos_client.create_database_if_not_exists(config['DATABASE_ID'])
notifications_container = database.get_container_client('Notifications')
users_container = database.get_container_client('Users')
follow_container = database.get_container_client('Follow')


def remove_social_stat(user, field, username):
    # Öncelikle kullanıcı ve alan bilgisinin doğru olup olmadığını kontrol et
    if isinstance(user, dict) and 'social_stats' in user and isinstance(user['social_stats'], dict):
        if field in user['social_stats'] and isinstance(user['social_stats'][field], list):
            user['social_stats'][field] = [x for x in user['social_stats'][field] if x['username'] != username]
            users_container.replace_item(item=user['id'], body=user)
        else:
            print(f"Expected a list for '{field}', but got {type(user['social_stats'][field])}. Check data integrity.")
    else:
        print("Error: User data structure is not as expected.")


def update_social_stats(username, field, new_data):
    query = f"SELECT c.social_stats, c.id FROM c WHERE c.username='{username}'"
    items = list(users_container.query_items(query=query, enable_cross_partition_query=True))
    if items:
        user_id = items[0]['id']
        user_document = users_container.read_item(item=user_id, partition_key=username)
        
        # `field` olarak belirtilen alanı kontrol edin, eğer yoksa yeni bir liste oluşturun.
        if field not in user_document['social_stats']:
            user_document['social_stats'][field] = []

        # Yeni veriyi listeye ekleyin.
        user_document['social_stats'][field].append(new_data)

        # Yeni liste ile belgeyi güncelleyin.
        users_container.replace_item(item=user_id, body=user_document)


def follow(sender, receiver, type):
    
    notification_query = f"SELECT * FROM c WHERE c.sender = '{sender}' AND c.receiver = '{receiver}' and c.status = 'pending'"
    notification_items = list(notifications_container.query_items(query=notification_query, enable_cross_partition_query=True))
    
    if notification_items:
        if notification_items[0].get('status')=="pending":
            notifications_container.delete_item(item=notification_items[0], partition_key=notification_items[0]['sender'])
            return json.dumps({"Result":"Bu isteyi geri aldınız"},ensure_ascii=True)
    
    else :  
        user_query = f"SELECT c.token, c.profile_pic, c.settings.privateAccount FROM c WHERE c.username='{receiver}'"
        user_items = list(users_container.query_items(query=user_query, enable_cross_partition_query=True))
        
        if not user_items:
            return json.dumps({"Result": "Kullanıcı Bulunamadı"}, ensure_ascii=True)
        
    
        private_account = user_items[0].get('privateAccount')
        token = user_items[0].get('token')
        follow_items = []  # Initialize follow_items

        if private_account == False:
            follow_query = f"SELECT * FROM c WHERE c.sender = '{sender}' AND c.receiver = '{receiver}' and c.type='{type}'"
            follow_items = list(notifications_container.query_items(query=follow_query, enable_cross_partition_query=True))
            
            sender_query = f"SELECT c.token, c.profile_pic FROM c WHERE c.username='{sender}'"
            sender_items = list(users_container.query_items(query=sender_query, enable_cross_partition_query=True))
            
            if not follow_items:
                friend_request = {
                    "is_read":False,
                    'id': str(uuid.uuid4()),
                    'sender_token': sender_items[0]['token'],
                    'sender': sender,
                    'receiver_token': user_items[0]['token'],
                    'receiver': receiver,
                    'type': type,
                    'sender_photo': sender_items[0]['profile_pic'],
                    "message": f"{sender} seni takip etmeye başladı!",
                    'timestamp': str(datetime.datetime.utcnow() + datetime.timedelta(hours=3)),
                    'status': 'approved'
                }
                notifications_container.create_item(friend_request)
                # Helper.firebase_fcm_notification(token,f"{sender} seni takip etmeye başladı!")
                follow = {
                    "id": str(uuid.uuid4()),
                    "sender": sender,
                    "receiver": receiver,
                    "type": "friendship",
                    "status": "approved"
                }
                follow_container.upsert_item(body=follow)
                    
                selec_query=f"SELECT c.id,c.token, c.username,c.firstname,c.lastname,c.profile_pic FROM c WHERE c.username='{receiver}'"
                selec_items = list(users_container.query_items(query=selec_query, enable_cross_partition_query=True))
                follower_data ={
                    "id":selec_items[0]['id'],
                    "username":selec_items[0]['username'],
                    "token":selec_items[0]['token'],
                    "username":selec_items[0]['username'],
                    "firstname":selec_items[0]['firstname'],
                    "lastname":selec_items[0]['lastname'],
                    "profile_pic":selec_items[0]['profile_pic']
                }

            
                select_query=f"SELECT c.id,c.token ,c.username,c.firstname,c.lastname,c.profile_pic FROM c WHERE c.username='{sender}'"
                select_items = list(users_container.query_items(query=select_query, enable_cross_partition_query=True))
            
                new_follower_data ={
                    "id":select_items[0]['id'],
                    "username":select_items[0]['username'],
                    "token":select_items[0]['token'],
                    "username":select_items[0]['username'],
                    "firstname":select_items[0]['firstname'],
                    "lastname":select_items[0]['lastname'],
                    "profile_pic":select_items[0]['profile_pic']
                }
                update_social_stats(receiver, 'followersCount', new_follower_data )
                update_social_stats(sender, 'followingCount', follower_data )
                
            
                return json.dumps(friend_request, ensure_ascii=True)
            
        elif private_account == True:
            follow_query = f"SELECT * FROM c WHERE c.sender = '{sender}' AND c.receiver = '{receiver}' and c.type='{type}'"
            follow_items = list(notifications_container.query_items(query=follow_query, enable_cross_partition_query=True))
            
            sender_query = f"SELECT c.token, c.profile_pic FROM c WHERE c.username='{sender}'"
            sender_items = list(users_container.query_items(query=sender_query, enable_cross_partition_query=True))
            
            if not follow_items:
                friend_request = {
                    "is_read":False,
                    'id': str(uuid.uuid4()),
                    'sender_token': sender_items[0]['token'],
                    'sender': sender,
                    'receiver_token': user_items[0]['token'],
                    'receiver': receiver,
                    'type': type,
                    'sender_photo': sender_items[0]['profile_pic'],
                    "message": f"{sender} seni arkadaş olarak eklemek istiyor!",
                    'timestamp': str(datetime.datetime.utcnow() + datetime.timedelta(hours=3)),
                    'status': 'pending'
                }
                notifications_container.create_item(friend_request)
                # Helper.firebase_fcm_notification(token,f"{sender} seni arkadaş olarak eklemek istiyor!")
                return json.dumps(friend_request, ensure_ascii=True)

def unfollow(sender, receiver):
    # Takip durumunu kontrol eden sorgu
    follow_query = f"SELECT * FROM c WHERE c.sender = '{sender}' AND c.receiver = '{receiver}'"
    follow_items = list(notifications_container.query_items(query=follow_query, enable_cross_partition_query=True))

    # Gönderici kullanıcının verilerini çeken sorgu
    sender_user_query = f"SELECT * FROM c WHERE c.username = '{sender}'"
    sender_user_items = list(users_container.query_items(query=sender_user_query, enable_cross_partition_query=True))

    # Alıcı kullanıcının verilerini çeken sorgu
    receiver_user_query = f"SELECT * FROM c WHERE c.username = '{receiver}'"
    receiver_user_items = list(users_container.query_items(query=receiver_user_query, enable_cross_partition_query=True))

    # Takip etmeyi bırakma durumunu kontrol eden sorgu
    unfollow_user_query = f"SELECT * FROM c WHERE c.sender = '{sender}' and c.receiver = '{receiver}'"
    unfollow_user_items = list(follow_container.query_items(query=unfollow_user_query, enable_cross_partition_query=True))

    # Sorgu sonuçlarının kontrolü
    if not follow_items or not unfollow_user_items or not sender_user_items or not receiver_user_items:
        return json.dumps({"Result": "Böyle bir istek bulunamadı"}, ensure_ascii=True)

    # İlgili verilerin çekilmesi
    user_item = follow_items[0]
    unfollow_item = unfollow_user_items[0]
    sender_user = sender_user_items[0]
    receiver_user = receiver_user_items[0]

    # Takip bilgisinin veritabanından silinmesi
    notifications_container.delete_item(item=user_item['id'], partition_key=user_item['sender'])
    follow_container.delete_item(item=unfollow_item['id'], partition_key=unfollow_item['sender'])

    # Eğer takip onaylanmışsa sosyal istatistiklerin güncellenmesi
    if user_item['status'] == 'approved':
        remove_social_stat(sender_user, 'followingCount', receiver)
        remove_social_stat(receiver_user, 'followersCount', sender)

    return json.dumps({"Result": "Arkadaşlık isteği silindi!"}, ensure_ascii=True)

def response(sender, receiver, type, status):
   
    follow_container = database.get_container_client('Follow')
    notifications_container = database.get_container_client('Notifications')
    users_container = database.get_container_client('Users')


    


    notification_query = f"SELECT * FROM c WHERE c.sender = '{sender}' AND c.receiver = '{receiver}'"
    items = list(notifications_container.query_items(query=notification_query, enable_cross_partition_query=True))

    if not items:
        return json.dumps({"Result": "Arkadaşlık isteği bulunamadı!"}, ensure_ascii=True)

    if status == "approved":
        follow_query = f"SELECT * FROM c WHERE c.sender = '{sender}' AND c.receiver = '{receiver}' AND c.status = 'approved'"
        existing_follows = list(follow_container.query_items(query=follow_query, enable_cross_partition_query=True))

        user_query = f"SELECT c.token FROM c WHERE c.username='{sender}'"
        user_items = list(users_container.query_items(query=user_query, enable_cross_partition_query=True))
        if items:
            token=user_items[0]['token']
            items[0]['status'] = status
            items[0]['message']=f"{sender} adlı kullanıcının takip isteğini kabul ettin."
          
            notifications_container.replace_item(item=items[0]['id'], body=items[0])
          
        else :
            result={
            'Hata':f'{sender} adresine ait token bulunamadı!'
            }
        
            return json.dumps(result)

        if any(follow['status'] == 'approved' for follow in existing_follows):
            result={
                "Result":f"{receiver} zaten arkadaşlık isteğini kabul etti!"
            }
            return json.dumps(result, ensure_ascii=True)
        else:
            
            for item in items:
                follow = {
                    "id": item["id"],
                    "sender": item["sender"],
                    "receiver": item["receiver"],
                    "type": "friendship",
                    "status": "approved"
                }
                follow_container.create_item(body=follow)


            select_query=f"SELECT c.id,c.token ,c.username,c.firstname,c.lastname,c.profile_pic FROM c WHERE c.username='{sender}'"
            select_items = list(users_container.query_items(query=select_query, enable_cross_partition_query=True))
            if items:
                new_follower_data ={
                    "id":select_items[0]['id'],
                    "username":select_items[0]['username'],
                    "token":select_items[0]['token'],
                    "username":select_items[0]['username'],
                    "firstname":select_items[0]['firstname'],
                    "lastname":select_items[0]['lastname'],
                    "profile_pic":select_items[0]['profile_pic']
                }
            selec_query=f"SELECT c.id,c.token, c.username,c.firstname,c.lastname,c.profile_pic FROM c WHERE c.username='{receiver}'"
            selec_items = list(users_container.query_items(query=selec_query, enable_cross_partition_query=True))
            if items:
                follower_data ={
                    "id":selec_items[0]['id'],
                    "username":selec_items[0]['username'],
                    "token":selec_items[0]['token'],
                    "username":selec_items[0]['username'],
                    "firstname":selec_items[0]['firstname'],
                    "lastname":selec_items[0]['lastname'],
                    "profile_pic":selec_items[0]['profile_pic']
                }
                
            
        
            update_social_stats(receiver, 'followersCount', new_follower_data )
            update_social_stats(sender, 'followingCount', follower_data )
            # Helper.firebase_fcm_notification(token,f"{receiver} arkadaşlık isteğini kabul etti!")
            result={
                "Result":f"{receiver} arkadaşlık isteğini kabul etti!"
            }
            return json.dumps(result, ensure_ascii=True)

    elif status == "rejected":
        
        follow_query = f"SELECT * FROM c WHERE c.sender = '{sender}' AND c.receiver = '{receiver}'"
        follow_items = list(follow_container.query_items(query=follow_query, enable_cross_partition_query=True))
        if follow_items:
            follow_container.delete_item(item=follow_items[0], partition_key=follow_items[0]['sender'])

        notification_query = f"SELECT * FROM c WHERE c.sender = '{sender}' AND c.receiver = '{receiver}' and c.type = '{type}'"
        notification_items = list(notifications_container.query_items(query=notification_query, enable_cross_partition_query=True))
        if notification_items:
            notifications_container.delete_item(item=notification_items[0], partition_key=notification_items[0]['sender'])

        return json.dumps("Arkadaşlık isteği silindi", ensure_ascii=True)

    elif status == "pending":
        follow_query = f"SELECT * FROM c WHERE c.sender = '{sender}' AND c.receiver = '{receiver}'"
        follow_items = list(follow_container.query_items(query=follow_query, enable_cross_partition_query=True))
        if follow_items:
            follow_container.delete_item(item=follow_items[0], partition_key=follow_items[0]['sender'])
            return json.dumps("Arkadaşlık isteği silindi", ensure_ascii=True)
        
    result={
        "Result":f"{receiver} zaten arkadaşlık isteğini kabul etti!"
    }
    return json.dumps(result)
 

def userList():
    container_name = 'Users'
    database = cosmos_client.get_database_client(config['DATABASE_ID'])
    container = database.get_container_client(container_name)
    
    # Define the query
    query = 'SELECT c.id,c.token,c.profile_pic, c.username, c.firstname, c.lastname FROM c'

    # Run the query
    items = list(container.query_items(
        query=query,
        enable_cross_partition_query=True
    ))

    return json.dumps(items)