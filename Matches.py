import json
import datetime
import Helper
from azure.cosmos import CosmosClient,exceptions
import uuid
import qpgpt


with open('config.json', 'r') as config_file:
    config = json.load(config_file)

cosmos_client = CosmosClient(config['ACCOUNT_HOST'], config['ACCOUNT_KEY'])
database = cosmos_client.get_database_client(config['DATABASE_ID'])




def send(username, type, file1, file2):
    utc_offset = datetime.timedelta(hours=3)
    now_utc3 = datetime.datetime.utcnow() + utc_offset
    timestamp=now_utc3.strftime('%Y-%m-%d %H:%M:%S')

    user_1 = Helper.imgToUrl(file1, username,"matchpictures")
    user_2 = Helper.imgToUrl(file2, username,"matchpictures")
    
    match_analysis=json.loads(qpgpt.matches(type,user_1,user_2))
    
    
    container = database.get_container_client("Users")
    users_query = f"SELECT * FROM Users u WHERE u.username='{username}'"
    items = list(
        container.query_items(query=users_query, enable_cross_partition_query=True)
    )
    
    user=items[0]

    result = {
        "id":str(uuid.uuid4()),
        "user_id":user['id'],
        "analysis_type":"Match",
        "username":user['username'],
        'user_1':user_1,
        'user_2':user_2,
        'description': match_analysis.get("Açıklama","Bir hata oluştu, Lütfen tekrar deneyin."),
        'match_type':type,
        'percentage':match_analysis.get("Uyum Yüzdesi","Bir hata oluştu, Lütfen tekrar deneyin."),
        'timestamp':timestamp,
        "likes": [],
        "comments": []
    }
    return json.dumps(result)


def save(username,isShared,data):
    isShared = isShared.lower() == "true"
    utc_offset = datetime.timedelta(hours=3)
    now_utc3 = datetime.datetime.utcnow() + utc_offset
    timestamp=now_utc3.strftime('%Y-%m-%d %H:%M:%S')
    
    container = database.get_container_client('test_Matches')
    
    # Check if match already exists
    match_query = """
        SELECT * FROM c
        WHERE c.username = @username
        AND c.user_1 = @user_1
        AND c.user_2 = @user_2
    """
    match_query_params = [
        {"name": "@username", "value": username},
        {"name": "@user_1", "value": data['user_1']},
        {"name": "@user_2", "value": data['user_2']}
    ]

    match_items = list(
        container.query_items(
            query=match_query,
            parameters=match_query_params,
            enable_cross_partition_query=True,
        )
    )
    
    if len(match_items) == 0:
        result={"isShared":isShared}
        result.update(data)
        result['timestamp']=timestamp
        container.upsert_item(body=result)
      

        return json.dumps(result)

    else:
        result = {
            "Hata": "Bu hesaplama zaten daha önceden yapılmış!"
        }
        return json.dumps(result)
    

def delete(username, id):

    container = database.get_container_client('test_Matches')

    # Sadece ilgili id'ye sahip öğeyi sorgula
    query = """
    SELECT *
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
        error_message = {
            'Error': f'Böyle bir eşleşme buluanamadı: {username} : {id}!',
        }
        return json.dumps(error_message, ensure_ascii=True)

    # Assume there's only one matching item due to unique id
    item_to_delete = items[0]

    # Deleting photos if exist
    user_1 = item_to_delete.get("user_1")
    user_2 = item_to_delete.get("user_2")
    
    if user_1: 
        Helper.delete_photo_from_azure(user_1, "matchpictures")
    if user_2:  
        Helper.delete_photo_from_azure(user_2, "matchpictures")

    # Delete the item
    try:
        container.delete_item(item=item_to_delete['id'], partition_key=item_to_delete['username'])
        result = {
            'Result': f'{username} kullanicisinin {id} nolu uyum hesaplaması başarıyla silindi!'
        }
        return json.dumps(result)
    except Exception as e:
        error_message = {
            'Error': str(e)
        }
        return json.dumps(error_message)