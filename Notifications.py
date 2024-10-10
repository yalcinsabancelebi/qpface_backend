from azure.cosmos import CosmosClient
import json 

with open('config.json', 'r') as config_file:
    config = json.load(config_file)

account_key = config['ACCOUNT_KEY']


cosmos_client=CosmosClient("https://qpface.documents.azure.com:443/",account_key)
database=cosmos_client.get_database_client("qpFaceCosmosDb")
users_container=database.get_container_client("Users")



import json

def fetch(username, is_read):
    # Sorgu yap
    notifications_query = f"SELECT * FROM c WHERE c.receiver = '{username}'"
    notifications_container = database.get_container_client("Notifications")
    notifications_items = list(notifications_container.query_items(
        query=notifications_query,
        enable_cross_partition_query=True
    ))

    # Eğer is_read True ise, her bildirimi güncelle
    if is_read == str('true'):
        for notification in notifications_items:
            try:
                # is_read alanını True yap
                notification['is_read'] = True
                notifications_container.replace_item(
                    item=notification['id'], 
                    body=notification
                )
            except Exception as e:
                print(f"Error updating notification with id {notification['id']}: {e}")
    
    # Bildirimleri ters sırada döndür 
    return json.dumps(notifications_items[::-1])