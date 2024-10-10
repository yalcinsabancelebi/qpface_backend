import Helper
from azure.storage.blob import BlobServiceClient
import qpgpt
import json
import datetime
import uuid
from azure.cosmos import CosmosClient



with open("config.json", "r") as config_file:
    config = json.load(config_file)

cosmos_client = CosmosClient(config["ACCOUNT_HOST"], config["ACCOUNT_KEY"])
database = cosmos_client.get_database_client(config["DATABASE_ID"])
container = database.get_container_client("Users")


def getuserinfo(username):
    user_query = f"SELECT * FROM Users u WHERE u.username = @username"
    user_parameters = [{"name": "@username", "value": username}]
    user_items = list(
        container.query_items(
            query=user_query,
            parameters=user_parameters,
            enable_cross_partition_query=True,
        )
    )
    if user_items:
        user = user_items[0]
        return user
    else:
        return f"{username} adlı kullanıcı bulunamadı"


def send(photo, username):
    utc_offset = datetime.timedelta(hours=3)
    now_utc3 = datetime.datetime.utcnow() + utc_offset
    timestamp = now_utc3.strftime("%Y-%m-%d %H:%M:%S")
    try:
        query = f"SELECT * FROM users u WHERE u.username='{username}'"
        items = list(
            container.query_items(query=query, enable_cross_partition_query=True)
        )

        if not items:
            result = {"Hata": f"{username} adresinde herhangi kayıt bulunamadı"}
            return json.dumps(result, ensure_ascii=True)

        photo_path = Helper.imgToUrl(photo, username, "analysispictures")
        result = json.loads(qpgpt.analysis(photo_path))
        user = getuserinfo(username)

        results = {
            "id":str(uuid.uuid4()),
            "user_id": user["id"],
            "analysis_type":"Face",
            "username": username,
            "analysis_photo": photo_path,
            "main_life": result.get("Genel Yaşam","Bir hata oluştu, Lütfen tekrar deneyin."),
            "love_life": result.get("Aşk Hayatı","Bir hata oluştu, Lütfen tekrar deneyin."),
            "team_harmony": result.get("Ekip Uyumu","Bir hata oluştu, Lütfen tekrar deneyin."),
            "learning_skills": result.get("Öğrenme Becerileri","Bir hata oluştu, Lütfen tekrar deneyin."),
            "timestamp": timestamp,
            "likes": [],
            "comments": []
        }

        return json.dumps(results)
    except Exception as e:
        return str(e)

with open('config.json', 'r') as config_file:
    config = json.load(config_file)

account_key = config['ACCOUNT_KEY']

# Initialize Cosmos DB client
cosmos_client = CosmosClient(
    "https://qpface.documents.azure.com:443/",
    account_key,
)
database = cosmos_client.get_database_client("qpFaceCosmosDb")



async def save(username, isShared, data):
    isShared = isShared.lower() == "true"
    try:
        utc_offset = datetime.timedelta(hours=3)
        now_utc3 = datetime.datetime.utcnow() + utc_offset
        timestamp = now_utc3.strftime("%Y-%m-%d %H:%M:%S")
        container = database.get_container_client("test_Analysis")

        # Check if analysis already exists
        analysis_query = """
            SELECT * FROM c
            WHERE c.username = @username
            AND c.analysis_photo = @photo
        """
        analysis_query_params = [
            {"name": "@username", "value": username},
            {"name": "@photo", "value": data['analysis_photo']},
        ]
        analysis_items = list(
            container.query_items(
                query=analysis_query,
                parameters=analysis_query_params,
                enable_cross_partition_query=True,
            )
        )

        if len(analysis_items) == 0:
            result={"isShared":isShared}
            result.update(data)
            result['timestamp']=timestamp
            container.upsert_item(body=result)
           
        
            return json.dumps(result)
        else:
            return json.dumps(
                {"Hata": "Bu hesaplama zaten daha önceden yapılmış!"},
                ensure_ascii=False,
                indent=4,
            )
    except Exception as e:
     
        return json.dumps(
            {"Hata": f"{str(e)}"},
            ensure_ascii=False,
            indent=4,
        )


def delete(username, analysis_id):

    url = "https://qpface.documents.azure.com:443/"
    key = account_key
    database_name = "qpFaceCosmosDb"
    analysis_container_name = "test_Analysis"

    client = CosmosClient(url, credential=key)
    database = client.get_database_client(database_name)
    analysis_container = database.get_container_client(analysis_container_name)

    query = (
        f"SELECT * FROM c WHERE c.id = '{analysis_id}' AND c.username = '{username}'"
    )
    analysis_items = list(
        analysis_container.query_items(query=query, enable_cross_partition_query=True)
    )

    if not analysis_items:
        error_message = {
            "Hata": f"{username} kullanıcısına ait böyle bir analiz bulunamadı!",
        }
        return json.dumps(error_message, ensure_ascii=True)

    analysis_item = analysis_items[0]  # İlk analizi al
    photo_url = analysis_item.get("analysis_photo", None)

    if photo_url is None:
        error_message = {
            "Hata": f"{username} kullanıcısına ait böyle bir fotoğraf bulunamadı!",
        }
        return json.dumps(error_message, ensure_ascii=True)
    else:
        try:

            Helper.delete_photo_from_azure(photo_url, "analysispictures")

            analysis_container.delete_item(item=analysis_id, partition_key=username)

            result = {
                "Result": f"{username} adresine ait analiz başarıyla silindi!",
            }
            return json.dumps(result)
        except Exception as e:
            error_message = {
                "Hata": f"{username} kullanıcısının analizini silerken bir hata oluştu: {str(e)}",
            }
            return json.dumps(error_message)
