import uuid
import Helper
import json
from azure.storage.blob import BlobServiceClient
import datetime
from azure.cosmos import CosmosClient
import qpgpt


with open('config.json', 'r') as config_file:
    config = json.load(config_file)

cosmos_client = CosmosClient(config['ACCOUNT_HOST'], config['ACCOUNT_KEY'])
database = cosmos_client.get_database_client(config['DATABASE_ID'])
blob_service_client = BlobServiceClient.from_connection_string(config['BLOB_CONNECTION_STRING'])
container = database.get_container_client('Users')
container_hobbies = database.get_container_client( 'Hobbies')
container_mood = database.get_container_client('Mood')
container_emotions = database.get_container_client('Emotions')


def send(photo, username):
    utc_offset = datetime.timedelta(hours=3)
    now_utc3 = datetime.datetime.utcnow() + utc_offset
    timestamp = now_utc3.strftime('%Y-%m-%d %H:%M:%S')

    mood_pic = Helper.imgToUrl(photo, username, "moodpictures")
    mood_analysis = json.loads(qpgpt.mood(mood_pic))

    query_hobbies = "SELECT c.hobby_name, c.photo FROM c"
    result_hobbies = container_hobbies.query_items(query=query_hobbies, enable_cross_partition_query=True)
    hobbies_dict = [{'hobby_name': item['hobby_name'], 'photo': item['photo']} for item in result_hobbies]

    container = database.get_container_client("Users")
    users_query = f"SELECT * FROM Users u WHERE u.username='{username}'"
    items = list(container.query_items(query=users_query, enable_cross_partition_query=True))
    
    if not items:
        return json.dumps({'Error': 'User not found'}, ensure_ascii=False)

    user = items[0]

    result = {
        "hobbies": hobbies_dict,
        "id": str(uuid.uuid4()),
        "user_id": user['id'],
        "analysis_type": "Mood",
        "username": user['username'],
        "firstname":user['firstname'],
        "lastname":user['lastname'],

        'mood_photo': mood_pic,
        'emotion': mood_analysis.get("Duygu","Bir hata oluştu, Lütfen tekrar deneyin."),
        'description': mood_analysis.get("Açıklama","Bir hata oluştu, Lütfen tekrar deneyin."),
        'timestamp': timestamp,
        "likes": [],
        "comments": []
    }
    return json.dumps(result)

def save(username, isShared, data):
    utc_offset = datetime.timedelta(hours=3)
    now_utc3 = datetime.datetime.utcnow() + utc_offset
    timestamp = now_utc3.strftime('%Y-%m-%d %H:%M:%S')
    
    isShared = isShared.lower() == "true"

    container = database.get_container_client('test_Moodify')

    query = """
       SELECT * 
        FROM c
        WHERE c.username = @username 
        AND c.mood_photo = @photo 
    """
    query_params = [
        {"name": "@username", "value": username},
        {"name": "@photo", "value": data['mood_photo']}
    ]

    try:
        mood_items = list(container.query_items(
            query=query,
            parameters=query_params,
            enable_cross_partition_query=True
        ))

        if len(mood_items) == 0:
            result = {"isShared": isShared}
            result.update({k: v for k, v in data.items() if k != 'hobbies'})
            result['timestamp'] = timestamp
            container.upsert_item(body=result)

            return json.dumps(result)
        else:
            result = {
                "Hata": "Bu hesaplama zaten daha önceden yapılmış!"
            }
            return json.dumps(result)

    except Exception as e:
        result = {
            "Hata": f"{str(e)}"
        }
        return json.dumps(result)





        


import json

def delete(username, id):
    container = database.get_container_client('test_Moodify')

    # Doğru öğeyi bul
    query = """
    SELECT c.id, c.mood_photo
    FROM c 
    WHERE c.id = @id AND c.username = @username
    """
    query_params = [
        {"name": "@id", "value": id},
        {"name": "@username", "value": username}
    ]

    items = list(container.query_items(
        query=query,
        parameters=query_params,
        enable_cross_partition_query=True
    ))

    if not items:
        return json.dumps({'Error': 'No such item found!'}, ensure_ascii=False)

    # Öğeler üzerinden döngü yap
    for item in items:
        photo_url = item.get("mood_photo")
        if photo_url:
            # Fotoğrafı sil
            Helper.delete_photo_from_azure(photo_url, "moodpictures")
            # Veritabanı öğesini sil
            container.delete_item(item=item['id'], partition_key=username)
            return json.dumps({'Result': 'öğe başarıyla silindi!'}, ensure_ascii=False)
        else:
            return json.dumps({'Error': 'Photo URL bulunamadı!'}, ensure_ascii=False)

    return json.dumps({'Error': 'Unexpected error occurred!'}, ensure_ascii=False)

