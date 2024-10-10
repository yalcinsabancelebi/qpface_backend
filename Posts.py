import asyncio
import datetime
import random
from azure.cosmos import CosmosClient
import json
import uuid
import Helper


utc_offset = datetime.timedelta(hours=3)
now_utc3 = datetime.datetime.utcnow() + utc_offset

with open('config.json', 'r') as config_file:
    config = json.load(config_file)
    
    
cosmos_client = CosmosClient(config['ACCOUNT_HOST'], config['ACCOUNT_KEY'])
database = cosmos_client.create_database_if_not_exists(config['DATABASE_ID'])
users_container = database.get_container_client('Users')
follow_container = database.get_container_client('Follow')
post_container = database.get_container_client('Posts')
analysis_container = database.get_container_client('test_Analysis')
matches_container = database.get_container_client('test_Matches')
notifications_container = database.get_container_client('Notifications')
mood_container = database.get_container_client('test_Moodify')
post_id = str(uuid.uuid4())
timestamp = str(datetime.datetime.utcnow() + datetime.timedelta(hours=3))



async def fetch_analysis_data(username):
    items = []

    query = f"SELECT * FROM c where c.username='{username}' and c.isShared= true ORDER BY c.timestamp DESC"
    for item in analysis_container.query_items(query=query, enable_cross_partition_query=True):
        items.append(item)
    return items

async def fetch_matches_data(username):
    items = []

    query = f"SELECT * FROM c where c.username='{username}' and c.isShared= true ORDER BY c.timestamp DESC"
    for item in matches_container.query_items(query=query, enable_cross_partition_query=True):
        items.append(item)
    return items

async def fetch_mood_data(username):
    items = []

    query = f"SELECT * FROM c where c.username='{username}' and c.isShared= true ORDER BY c.timestamp DESC"
    for item in mood_container.query_items(query=query, enable_cross_partition_query=True):
        items.append(item)
    return items




async def fetch_shared_data(username):
    # Kullanıcı bilgilerini çek
    user_query = f"SELECT c.id, c.token, c.username, c.firstname, c.lastname, c.profile_pic, c.email FROM c WHERE c.username = '{username}'"
    users_items = list(users_container.query_items(query=user_query, enable_cross_partition_query=True))

    if not users_items:
        username_error = {
            'Error': f'Hata! {username} mail adresinde herhangi bir kayıt bulunamadı',
        }
        return json.dumps(username_error, ensure_ascii=True)

    # Kullanıcının takip ettiği kullanıcıları al (profil durumu göz ardı ediliyor)
    friend_list_query = f"SELECT c.receiver FROM c WHERE c.sender = '{username}' and c.status = 'approved'"
    friend_items = list(follow_container.query_items(query=friend_list_query, enable_cross_partition_query=True))

    # Takip edilen kullanıcıları listeye ekle
    user_list = [username] + [item.get('receiver', '') for item in friend_items if item.get('receiver')]
  
    user_homepage = []

    # Asenkron işlemleri başlat ve sonuçları topla
    tasks = []
    for user_name in user_list:
        tasks.append(fetch_analysis_data(user_name))
        tasks.append(fetch_matches_data(user_name))
        tasks.append(fetch_mood_data(user_name))

    # Tüm asenkron işlemler tamamlandığında sonuçları topla
    results = await asyncio.gather(*tasks)

    # Sonuçları tek bir listede birleştir
    for result in results:
        user_homepage.extend(result)
        
    user_homepage.sort(key=lambda x: x.get('timestamp', 0), reverse=True)

    # Kullanıcı bilgilerini her analize ekle
    for item in user_homepage:
        user_query = f"SELECT c.id, c.token, c.username, c.firstname, c.lastname, c.profile_pic, c.email FROM c WHERE c.username = '{item['username']}'"
        user_info = list(users_container.query_items(query=user_query, enable_cross_partition_query=True))

        if user_info:
            user_data = user_info[0]
            item.update({
                'user_id': user_data['id'],
                'username': user_data['username'],
                'firstname': user_data['firstname'],
                'lastname': user_data['lastname'],
                'profile_pic': user_data['profile_pic'],
                'email': user_data['email']
            })

    # Kullanıcı bilgilerini ve sonuçları döndür
    user_info = users_items[0]
    result = {
        'user_info': {
            'firstname': user_info['firstname'],
            'lastname': user_info['lastname'],
            'username': user_info['username'],
            'profile_pic': user_info['profile_pic'],
            'email': user_info['email']
        },
        'items': user_homepage
    }

    return result




async def homepage(username):
    items = await fetch_shared_data(username)
    return json.dumps(items, ensure_ascii=False)




user_cache = {}

async def fetch_sender_info(users_container, top_count):
    if top_count:
        query = f"SELECT TOP {top_count} c.id, c.token, c.username, c.firstname, c.lastname, c.profile_pic, c.email FROM c WHERE c.settings.privateAccount=false"
    else:
        query = "SELECT c.id, c.token, c.username, c.firstname, c.lastname, c.profile_pic, c.email FROM c WHERE c.settings.privateAccount=false"
    result_iterable = users_container.query_items(query=query, enable_cross_partition_query=True)
    return [item for item in result_iterable]

async def fetch_user_info(username, users_container):
    if username in user_cache:
        return user_cache[username]

    query = f"SELECT c.firstname, c.lastname, c.username, c.profile_pic, c.email FROM c WHERE c.username = '{username}'"
    result_iterable = users_container.query_items(query=query, enable_cross_partition_query=True)
    user_info = list(result_iterable)
    if user_info:
        user_data = {
            'firstname': user_info[0]['firstname'],
            'lastname': user_info[0]['lastname'],
            'profile_pic': user_info[0]['profile_pic'],
            'email': user_info[0]['email']
        }
    else:
        user_data = {
            'firstname': '',
            'lastname': '',
            'profile_pic': '',
            'email': ''
        }
    
    user_cache[username] = user_data
    return user_data

async def fetch_user_data(user_name, container, top_count):
    if top_count:
        query = f"SELECT TOP {top_count} * FROM c WHERE c.username = '{user_name}' AND c.isShared = true"
    else:
        query = f"SELECT * FROM c WHERE c.username = '{user_name}' AND c.isShared = true"
    result_iterable = container.query_items(query=query, enable_cross_partition_query=True)
    return [item for item in result_iterable]

async def fetch_explore():
    user_explore = []

    # Tüm kullanıcıları al
    sender_infos = await fetch_sender_info(users_container, None)  # None, tüm kullanıcıları almak için
    user_list = [item['username'] for item in sender_infos]

    tasks = []
    for user_name in user_list:
        tasks.extend([
            fetch_user_data(user_name, container, None) for container in [analysis_container, matches_container, mood_container]
        ])
    
    results = await asyncio.gather(*tasks)
    
    for result in results:
        user_explore.extend(result)

    # Kullanıcı bilgilerini ekleme
    for item in user_explore:
        user_info = await fetch_user_info(item['username'], users_container)
        item.update(user_info)


    return user_explore

async def explore(username):
    items = await fetch_explore()

    random.shuffle(items)

    user_info = await fetch_user_info(username, users_container)

    if not user_info['firstname']:
        user_header = {'Error': f'Hata! {username} kullanıcısının bilgileri bulunamadı'}
    else:
        user_header = user_info

    result = {
        'user_info': user_header,
        'items': items
    }

    return json.dumps(result, ensure_ascii=False)





def like(post_id, sender, receiver, post_type):
    
        # Alıcı bilgilerini sorgula
        receiver_query = f"SELECT c.id, c.token FROM c WHERE c.username='{receiver}'"
        receiver_items = list(users_container.query_items(query=receiver_query, enable_cross_partition_query=True))

        # Gönderici bilgilerini sorgula
        sender_query = f"SELECT c.id, c.token, c.username, c.firstname, c.lastname, c.profile_pic FROM c WHERE c.username='{sender}'"
        sender_items = list(users_container.query_items(query=sender_query, enable_cross_partition_query=True))

        follower_data = {
            "id":sender_items[0]['id'],
            "username": sender_items[0]['username'],
            "firstname": sender_items[0]['firstname'],
            "lastname": sender_items[0]['lastname'],
            "profile_pic": sender_items[0]['profile_pic']
        }

        # İlgili konteynerı seç
        container = None
        if post_type == 'Analysis':
            container = analysis_container
        elif post_type == 'Match':
            container = matches_container
        else:
            post_type='Mood'
            container = mood_container

        # Post verisini sorgula
        query = f"SELECT c.token ,c.id, c.likes, c.comments, c.username FROM c WHERE c.username='{receiver}' AND c.id='{post_id}'"
        data = list(container.query_items(query=query, enable_cross_partition_query=True))
        user_id = data[0]['id']
        user_document = container.read_item(item=user_id, partition_key=receiver)

        # Belirli ID'ye sahip bir nesne varsa sil, yoksa ekle
        existing_like = next((like for like in user_document['likes'] if like['id'] == sender_items[0]['id']), None)
        if existing_like:
            user_document['likes'].remove(existing_like)
            container.replace_item(item=user_id, body=user_document)
            
            # Notifications container'dan ilgili bildirimi sil
            notification_query = f"SELECT * FROM c WHERE c.post_id='{post_id}' AND c.sender='{sender}' AND c.receiver='{receiver}' AND c.type='like'"
            notifications = list(notifications_container.query_items(query=notification_query, enable_cross_partition_query=True))
            
            if notifications:
                notification_id = notifications[0]['id']
                notifications_container.delete_item(item=notification_id, partition_key=sender)

            return json.dumps('Like geri alındı')
        else:
            user_document['likes'].append(follower_data)
            if sender!=receiver:
                like_request = {
                    "is_read":False,
                    'id': str(uuid.uuid4()),
                    'sender_token': sender_items[0]['token'],
                    'sender': sender,
                    'receiver_token': receiver_items[0]['token'],
                    'receiver': receiver,
                    "post_type":post_type,
                    "post_id":post_id,
                    'type': "like",
                    'sender_photo': sender_items[0]['profile_pic'],
                    "message": f"{sender} senin fotoğrafını beğendi!",
                    'timestamp': str(datetime.datetime.utcnow() + datetime.timedelta(hours=3))
                }
                notifications_container.create_item(like_request)
                #Helper.firebase_fcm_notification(receiver_items[0]['token'],f"{sender} gönderini beğendi",post_type,post_id)
            result = {
                'sender': sender,
                'receiver': receiver,
                'post_id': post_id,
                'post_type': post_type,
                
            }
           
            container.replace_item(item=user_id, body=user_document)
            return json.dumps(result)


def comment(post_id, sender, receiver, post_type, comment_text):

    utc_offset = datetime.timedelta(hours=3)
    now_utc3 = datetime.datetime.utcnow() + utc_offset
    timestamp = now_utc3.strftime('%Y-%m-%d %H:%M:%S')

    try:
        # Alıcı bilgilerini sorgula
        receiver_query = f"SELECT c.id, c.token FROM c WHERE c.username='{receiver}'"
        receiver_items = list(users_container.query_items(query=receiver_query, enable_cross_partition_query=True))

        # Gönderici bilgilerini sorgula
        sender_query = f"SELECT c.id, c.token, c.username, c.firstname, c.lastname, c.profile_pic FROM c WHERE c.username='{sender}'"
        sender_items = list(users_container.query_items(query=sender_query, enable_cross_partition_query=True))

        if not sender_items:
            return json.dumps({'error': 'Sender not found'})

        sender_data = sender_items[0]
        comment_id=str(uuid.uuid4())

        follower_data = {
            "username": sender_data['username'],
            "firstname": sender_data['firstname'],
            "lastname": sender_data['lastname'],
            "profile_pic": sender_data['profile_pic'],
            "text": comment_text,
            "timestamp": timestamp,
            "comment_id": comment_id
        }

        # İlgili konteynerı seç
        container = None
        if post_type == 'Analysis':
            container = analysis_container
        elif post_type == 'Match':
            container = matches_container
        else:
            container = mood_container

        # Post verisini sorgula
        query = f"SELECT c.id, c.comments FROM c WHERE c.username='{receiver}' AND c.id='{post_id}'"
        data = list(container.query_items(query=query, enable_cross_partition_query=True))

        if not data:
            return json.dumps({'error': 'Post not found'})

        user_id = data[0]['id']
        user_document = container.read_item(item=user_id, partition_key=receiver)

        # Yorumları güncelle
        user_document['comments'].append(follower_data)

        # Güncellenmiş veriyi kaydet
        container.replace_item(item=user_id, body=user_document)

        if sender!=receiver:
                comment_request = {
                 
                "is_read":False,
                'id': str(uuid.uuid4()),
                'sender_token': sender_items[0]['token'],
                'sender': sender,
                'receiver_token': receiver_items[0]['token'],
                'receiver': receiver,
                "post_type":post_type,
                "post_id":post_id,
                'type': "comment",
                "comment_id":comment_id,
                'sender_photo': sender_items[0]['profile_pic'],
                "message": f"{sender} senin fotoğrafına yorum yaptı!",
                'timestamp': str(datetime.datetime.utcnow() + datetime.timedelta(hours=3))
            }
                notifications_container.create_item(comment_request)
                # Helper.firebase_fcm_notification(receiver_items[0]['token'], f"{sender} gönderine yorum yaptı!",post_type,post_id)

        # Sonucu döndür
        result = {
            'data': follower_data,
        }
        return json.dumps(result)
    except Exception as e:
        return json.dumps({'error': str(e)})




def delete_comment(post_id, post_type, comment_id):
    # İlgili konteynerı seç
    container = None
    if post_type == 'Analysis':
        container = analysis_container
    elif post_type == 'Match':
        container = matches_container
    else:
        container = mood_container

    # Gönderiyi seçen sorgu
    query = f"SELECT * FROM c WHERE c.id='{post_id}'"
    items = list(container.query_items(query=query, enable_cross_partition_query=True))

    if not items:
        raise ValueError("Gönderi bulunamadı")
    
    post = items[0]  # Tek bir gönderi olduğu varsayılıyor
    
    # Yorumları kontrol et
    comments = post.get('comments', [])
    comment_found = any(comment['comment_id'] == comment_id for comment in comments)
    
    if not comment_found:
        return json.dumps({"Result": "Yorum bulunamadı"})

    # Yorumları filtrele
    updated_comments = [comment for comment in comments if comment['comment_id'] != comment_id]
    
    # Yorum güncelle
    post['comments'] = updated_comments
    container.upsert_item(post)
    
    # Bildirimi silmek için sorgu
    query = f"SELECT * FROM c WHERE c.post_id='{post_id}' AND c.comment_id='{comment_id}' AND c.type='comment'"
    notifications = list(notifications_container.query_items(query=query, enable_cross_partition_query=True))
    
    if notifications:
        for notification in notifications:
            notification_id = notification['id']
            sender_partition_key = notification['sender']
            
            # Bildirimi sil
            notifications_container.delete_item(item=notification_id, partition_key=sender_partition_key)
        
        return json.dumps({"Result": "Yorum silindi"})
    else:
        return json.dumps({"Result": "Bildirim bulunamadı"})








def details(post_id,container_type):
    
    container = None
    if container_type == 'Analysis':
        container = analysis_container
    elif container_type == 'Match':
        container = matches_container
    else:
        container = mood_container

    query=f"select * from c Where c.id = '{post_id}'"
    items = list(container.query_items(query=query, enable_cross_partition_query=True))

    return json.dumps(items)











