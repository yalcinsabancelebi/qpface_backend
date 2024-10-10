import json
from azure.cosmos import CosmosClient

with open('config.json', 'r') as config_file:
    config = json.load(config_file)

account_key = config['ACCOUNT_KEY']



cosmos_client = CosmosClient("https://qpface.documents.azure.com:443/", account_key)
database = cosmos_client.get_database_client("qpFaceCosmosDb")
users_container = database.get_container_client("Users")

async def girisyap(username, fcm_token):
    register_query = f"SELECT * FROM c WHERE c.username = '{username}'"
    register_items = list(users_container.query_items(query=register_query, enable_cross_partition_query=True))
    if register_items:
        register_items[0]['token'] = fcm_token
        users_container.replace_item(item=register_items[0]['id'], body=register_items[0])


    return json.dumps('Giriş Başarılı')


def cikis(username):
    try:
        # Kullanıcıyı sorgula
        user_query = f"SELECT * FROM c WHERE c.username = '{username}'"
        user_items = list(users_container.query_items(
            query=user_query,
            enable_cross_partition_query=True
        ))


        user_item = user_items[0]

        # Token alanını temizle
        user_item['token'] = ""

        # Item'i güncelle (replace_item) 
        users_container.replace_item(item=user_item['id'], body=user_item, partition_key=username)
        
        return "Kullanıcının token'ı başarıyla temizlendi."
    
    except Exception as e:
        return f"Bir hata oluştu: {str(e)}"