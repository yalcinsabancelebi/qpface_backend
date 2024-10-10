import json
from azure.storage.blob import BlobServiceClient
import Helper
import uuid
import json
from azure.cosmos import CosmosClient
import datetime
from datetime import timedelta


with open('config.json', 'r') as config_file:
    config = json.load(config_file)

cosmos_client = CosmosClient(config['ACCOUNT_HOST'], config['ACCOUNT_KEY'])
database = cosmos_client.get_database_client(config['DATABASE_ID'])
blob_service_client = BlobServiceClient.from_connection_string(config['BLOB_CONNECTION_STRING'])
container = database.get_container_client('Users')

utc_offset = timedelta(hours=3)
now_utc3 = datetime.datetime.utcnow() + utc_offset
timestamp=now_utc3.strftime('%Y-%m-%d %H:%M:%S')

default_profile_pic_url = "https://qpface.blob.core.windows.net/assets/defaultUser.jpg"
default_cover_pic_url="https://qpface.blob.core.windows.net/assets/defaultCover.jpg"
database = cosmos_client.create_database_if_not_exists(config['DATABASE_ID'])



async def register(username, token, mail, name, surname):
    query = "SELECT VALUE COUNT(1) FROM c WHERE c.username = @username"
    query_params = [{"name": "@username", "value": username}]
   
    try:
        user_count = list(container.query_items(
            query=query,
            parameters=query_params,
            enable_cross_partition_query=True
        ))

        if user_count and user_count[0] > 0:
            return json.dumps({'Result': "Kullanıcı adı daha önce alınmış."}, ensure_ascii=True)
        
        new_item = {
            "id": str(uuid.uuid4()),
            "token": token,
            "username": username,
            "email": mail,
            "firstname": name,
            "lastname": surname,
            "profile_pic": default_profile_pic_url,
            "cover_pic": default_cover_pic_url,
            "gender": "",
            "birthdate": "",
            "horoscope": "",
            "biography": "",
            "created_time": timestamp,
            "social_stats": {
                "followersCount": [],
                "followingCount": [],
            },
            "settings": {
                "privateAccount": True,
                "receiveMessagesFromNonFollowers": True
            }
        }

        container.upsert_item(body=new_item)
        return json.dumps(new_item, ensure_ascii=False, indent=4)

    except Exception as e:
        return json.dumps({'Result': "Failed to register user in Cosmos DB.", 'Error': str(e)}, ensure_ascii=False, indent=4)

def update(username, mail, name, surname, profile_pic, cover_pic, gender, birthdate, biography, privateAccount, receiveMessagesFromNonFollowers):
    query = "SELECT VALUE COUNT(1) FROM c WHERE c.username = @username"
    
    query_params = [
        {"name": "@username", "value": username}
    ]
   
    user_count = list(container.query_items(
        query=query,
        parameters=query_params,
        enable_cross_partition_query=True
    ))

    if len(user_count) == 0 or user_count[0] == 0:
        username_error = {
            'Error': f'Hata! {username} kullanıcı adında herhangi bir kayıt bulunamadı'
        }
        return json.dumps(username_error, ensure_ascii=True)
    
    profile_pic = Helper.upload_photo_from_azure(username, profile_pic, "profilepictures") if profile_pic else default_profile_pic_url
    cover_pic = Helper.upload_photo_from_azure(username, cover_pic, "coverpictures") if cover_pic else default_cover_pic_url
    horoscope = calc_horoscope(birthdate) if birthdate else ""
    utc_offset = timedelta(hours=3)
    now_utc3 = datetime.utcnow() + utc_offset
    timestamp = now_utc3.strftime('%Y-%m-%d %H:%M:%S')
        
    query = f"SELECT * FROM c WHERE c.username = '{username}'"
    items = list(container.query_items(query=query, enable_cross_partition_query=True))
    if items:
        user_item = items[0]
        user_item['email'] = mail
        user_item['firstname'] = name
        user_item['lastname'] = surname
        user_item['profile_pic'] = profile_pic
        user_item['cover_pic'] = cover_pic
        user_item['gender'] = gender
        user_item['birthdate'] = birthdate
        user_item['horoscope'] = horoscope
        user_item['biography'] = biography
        user_item['settings']['privateAccount'] = privateAccount
        user_item['settings']['receiveMessagesFromNonFollowers'] = receiveMessagesFromNonFollowers
        user_item['updated_time'] = timestamp
        
        try:
            response = container.replace_item(item=user_item['id'], body=user_item)
            
            # Tüm kullanıcı verilerini güncelle
            Helper.update_all_user_data(username, name, surname, profile_pic)
            
            return json.dumps(response)
        except Exception as e:
            return json.dumps({'Error': "Failed to update user in Cosmos DB.", 'Exception': str(e)}, ensure_ascii=False, indent=4)
    else:
        return json.dumps({'Error': f'Hata! {username} kullanıcı adında herhangi bir kayıt bulunamadı'}, ensure_ascii=True)


   
def delete(username):
    
    container_names = ["Users", "test_Matches", "test_Analysis","test_Moodify","Login"]
    for container_name in container_names:
        container = database.get_container_client(container_name) 
        query = f"SELECT * FROM c WHERE c.username = '{username}'"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        for item in items:
            container.delete_item(item=item, partition_key=item['username'])


    container_names = ["Notifications","Follow","Messages"]
    for container_name in container_names:
        container = database.get_container_client(container_name) 
        query = f"SELECT * FROM c WHERE c.receiver= '{username}' or c.sender = '{username}'"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        for item in items:
            container.delete_item(item=item, partition_key=item['sender'])


    container_names = ["analysispictures", "matchpictures", "moodpictures","profilepictures","coverpictures"]
    for container_name in container_names:
        container_client = blob_service_client.get_container_client(container_name)
        Helper.delete_user_blob(container_client, username)

    return json.dumps({'Result': "Veri silindi",}, ensure_ascii=False, indent=4)

import json
from datetime import datetime

def fetch(username, from_user):
    users_container = database.get_container_client('Users')
    analysis_container = database.get_container_client('test_Analysis')
    matches_container = database.get_container_client('test_Matches')
    follow_container = database.get_container_client('Follow')
    notifications_container = database.get_container_client('Notifications')

    user_query = f"SELECT * FROM Users u WHERE u.username = @username"
    user_parameters = [{"name": "@username", "value": username}]
    user_items = list(users_container.query_items(query=user_query, parameters=user_parameters, enable_cross_partition_query=True))

    analysis_query = f"SELECT * FROM test_Analysis a WHERE a.username = @username"
    analysis_parameters = [{"name": "@username", "value": username}]
    analysis_items = list(analysis_container.query_items(query=analysis_query, parameters=analysis_parameters, enable_cross_partition_query=True))

    matches_query = f"SELECT * FROM test_Matches a WHERE a.username = @username"
    matches_parameters = [{"name": "@username", "value": username}]
    matches_items = list(matches_container.query_items(query=matches_query, parameters=matches_parameters, enable_cross_partition_query=True))

    def get_timestamp(item):
        if 'timestamp' in item:
            return datetime.strptime(item['timestamp'], '%Y-%m-%d %H:%M:%S')
        else:
            return None

    def filter_valid_items(items):
        return [item for item in items if get_timestamp(item) is not None]

    if username == from_user:
        all_items = analysis_items + matches_items
        valid_items = filter_valid_items(all_items)
        sorted_items = sorted(valid_items, key=get_timestamp, reverse=True)
        analysis_items = [item for item in sorted_items if item in analysis_items]
        matches_items = [item for item in sorted_items if item in matches_items]

        result = {
            "user_info": user_items[0] if user_items else None,
            "content": {
                "analysis": analysis_items,
                "matches": matches_items
            }
        }
    else:
        notifications_query = f"SELECT * FROM Notifications a WHERE a.receiver = '{username}' and a.sender = '{from_user}'"
        notifications_items = list(notifications_container.query_items(query=notifications_query, enable_cross_partition_query=True))

        follow_query = f"SELECT * FROM c WHERE c.receiver = '{username}' AND c.sender = '{from_user}'"
        existing_follows = list(follow_container.query_items(query=follow_query, enable_cross_partition_query=True))

        if user_items:
            private_account = user_items[0]['settings'].get('privateAccount', True)  # Varsayılan olarak privateAccount'u True kabul ediyoruz.
        else:
            private_account = True
            
        try:
            if any(follow['status'] == 'approved' for follow in existing_follows):
                status = "approved"
            elif any(follow['status'] == 'pending' for follow in notifications_items):
                status = "pending"
            else:
                status = "rejected"
            
        except:
            status = "rejected"



        if status == "approved" or (status == "pending" and not private_account) or not private_account:
            all_items = analysis_items + matches_items
            valid_items = filter_valid_items(all_items)
            sorted_items = sorted(valid_items, key=get_timestamp, reverse=True)
            analysis_items = [item for item in sorted_items if item in analysis_items]
            matches_items = [item for item in sorted_items if item in matches_items]
        else:
            analysis_items = []
            matches_items = []

        result = {
            "private_account": private_account,
            "status": status,
            "user_info": user_items[0] if user_items else None,
            "content": {
                "analysis": analysis_items,
                "matches": matches_items
            }
        }

    return json.dumps(result)





def calc_horoscope(birthdate):
    try:
        _, month,day = map(int, birthdate.split('-')) 
        dates = [
            (21, 3, 20, 4), (21, 4, 20, 5), (21, 5, 21, 6), (22, 6, 22, 7),
            (23, 7, 23, 8), (24, 8, 23, 9), (24, 9, 23, 10), (24, 10, 22, 11),
            (23, 11, 21, 12), (22, 12, 20, 1), (21, 1, 19, 2), (20, 2, 20, 3)
        ]
        horoscopes = [
            'Koç', 'Boğa', 'İkizler', 'Yengeç',
            'Aslan', 'Başak', 'Terazi', 'Akrep',
            'Yay', 'Oğlak', 'Kova', 'Balık'
        ]

        for i, (start_day, start_month, end_day, end_month) in enumerate(dates):
            if ((month == start_month and day >= start_day) or 
                (month == end_month and day <= end_day)):
                return horoscopes[i]

    except ValueError:
        return "Geçersiz tarih formatı. Lütfen yıl-ay-gün formatında bir tarih girin."