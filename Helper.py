from PIL import Image
import requests
from openai import OpenAI
from azure.storage.blob import BlobServiceClient
import uuid
import datetime
import base64
import io
import json
import datetime
import os
from azure.cosmos import CosmosClient
import hashlib
from google.oauth2 import service_account
import google.auth.transport.requests
##

with open("config.json", "r") as config_file:
    config = json.load(config_file)

cosmos_client = CosmosClient(config["ACCOUNT_HOST"], config["ACCOUNT_KEY"])
database = cosmos_client.get_database_client(config["DATABASE_ID"])
CONTAINER_ID = os.getenv("COSMOS_CONTAINER", "Users")
container = database.get_container_client(CONTAINER_ID)
mood_container = database.get_container_client("test_Moodify")
analysis_container = database.get_container_client("test_Analysis")
matches_container = database.get_container_client("test_Matches")

connection_string = BlobServiceClient.from_connection_string(
    config["BLOB_CONNECTION_STRING"]
)

utc_offset = datetime.timedelta(hours=3)
now_utc3 = datetime.datetime.utcnow() + utc_offset


MIN_WIDTH = 300
MIN_HEIGHT = 300


def imgToUrl(img, email, containername):
    container_name = containername
    image = Image.open(io.BytesIO(img.read()))

    original_width, original_height = image.size

    # Ölçek faktörünü ve kaliteyi hesaplamak için formül
    max_dimension = max(original_width, original_height)

    # 1000 pikselden küçük resimler için (yaklaşık %90 boyutunda ve kalite yüksek)
    # 3000 pikselden büyük resimler için (yaklaşık %30 boyutunda ve kalite düşük)
    scale_factor = 1 - 0.7 * ((max_dimension - 1000) / 2000)
    scale_factor = max(0.3, min(scale_factor, 0.9))  # %30 ile %90 arasında sınırlıyoruz

    quality = 80 - 60 * ((max_dimension - 1000) / 2000)
    quality = max(
        50, min(int(quality), 80)
    )  # Kaliteyi %20 ile %80 arasında sınırlıyoruz

    new_width = max(int(original_width * scale_factor), MIN_WIDTH)
    new_height = max(int(original_height * scale_factor), MIN_HEIGHT)

    # Image'i yeniden boyutlandır
    image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Benzersiz bir blob ismi oluştur
    photo_uuid = str(uuid.uuid1()).split("-")[0]
    now_utc3 = datetime.datetime.now()
    photo_datetime = now_utc3.strftime("%Y-%m-%d%H:%M:%S_")
    blob_name = f"QpFace_{email}_{photo_datetime}{photo_uuid}.jpg"

    # Blob client oluştur
    blob_client = connection_string.get_blob_client(
        container=container_name, blob=blob_name
    )

    # ByteIO stream oluştur ve image save yap
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format="JPEG", quality=quality)

    # Stream başını resetle
    img_byte_arr.seek(0)

    # Blob'a upload yap
    blob_client.upload_blob(
        img_byte_arr, blob_type="BlockBlob", content_type="image/jpeg"
    )

    # Blob URL'yi return et
    blob_url = blob_client.url
    img_url = blob_url.replace("%40", "@").replace("%3A", ":")

    return img_url


def generator(liste, type_char):
    all_responses = []
    client = OpenAI(api_key="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")
    for x in type_char:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": f" {liste} Avoid statements about the future. Let comments about the individual reflect their current situation. Include information about the person's inner experiences, feelings, and thoughts. It should be like sample text, and you won't be adding your own words. Do not use a foreign language. Write the output in Turkish. Avoid using contradictory sentences. You can rephrase and rewrite sentences in your own unique way. Be original and enjoyable. Write in only 90 words about just {x}. Sample Text: Iletisim becerileri yüksektir ve bu özelligini is hayatinda basarili bir sekilde kullanabilir. Cömert ve arkadaslari tarafindan sevilen biri olabilir.ögrenmeye açik, duygularini kontrol edebilen bir yapiya sahip. Yenilikçi fikirler üretebilir ancak karar verme sürecini yavaslatabilir. Takim çalismasina katki saglamasi muhtemeldir.Yaratici fikirleri ile katki saglayabilir. Ancak sert duygu geçisleri nedeniyle stresli veya baski altinda çalismaya uygun olmayabilir. Agresifligi, performansini olumsuz etkileyebilir.Kontrolcü ve güvenilmez bir tavir sergileme egilimindedirler. Ayrica, yüksek ego ve ben-merkezci yapisi nedeniyle isbirligi yapmakta zorlanabilir.Ekip çalismasina uyumlu, pozitif ve gelisime açik bir yapiya sahip olabilir. Insanlarla iyi iletisim kurabilir ve is disiplinine uyum saglayabilir.Tabiati geregi insanlara yardim etmekten hoslanir ve dürüst bir yapiya sahiptir. Is arkadaslari ve müsteriler tarafindan saygi duyulan bir kisidir.Liderlik pozisyonlari için uygun olabilir. Ikna kabiliyeti yüksektir, satis, pazarlama veya müsteri iliskileri gibi alanlarda basarili olabilir.Is hayatinda basarili olma potansiyeli yüksektir. Is arkadaslari tarafindan sevilen ve saygi duyulan biri olarak, takim çalismasinda etkili bir rol oynayabilir.Detaylara önem veren ve planli bir yapiya sahiptir. Zaman zaman esneklik ve adaptasyon konusunda sikintilar yasayabilir.Karar vermeden önce detaylari derinlemesine incelemek isteyebilir. Sitematik bir çalisma yöntemi benimsemistir. Is hayatinda stres faktörleriyle iyi basa çikabilir.Kararli ve liderlik özellikleri gelismis, isine bagli bir çalisan olabilir.Zaman yönetimi ve sinirlari belirleme zayif olabilir. Kalabalik ortamlarda iyi performans gösterip, ekip çalismalarinda basarili olabilir. Liderlik pozisyonlari için çok iyi olmayabilir.Hirsli yapisi, fikir ayriliklarinda zaman anlasmazliklara ve tartismalara sebebiyet verebilir.",
                }
            ],
        )
        all_responses.append(
            response.choices[0].message.content.replace("\n\n", "")
        )  # Her döngüdeki yanıtı listeye ekleyin

    return all_responses


def delete_photo_from_azure(photo_url, container_name):
    # Fotoğrafın adını URL'den ayıkla
    photo_name = photo_url.split("/")[-1]  # URL'nin son kısmı fotoğrafın adıdır

    # Azure bağlantı dizesi
    connect_str = "DefaultEndpointsProtocol=https;AccountName=qpface;AccountKey=EyMLc4tr5oXFHGmt2C+/hhlAWb/sC1OJbPGdFgQMrYrxnBnpWhJITRrMF9UCXlWXuRBWOAm48mso+ASt8z9Efg==;EndpointSuffix=core.windows.net"

    blob_client = connection_string.get_blob_client(
        container=container_name, blob=photo_name
    )

    # Eğer blob varsa sil
    if blob_client.exists():
        blob_client.delete_blob()
        result = {"Status_code": 200, "Message": "Photo deleted successfully."}
    else:
        result = {"Status_code": 404, "Message": "Photo not found."}

    return json.dumps(result)


def upload_photo_from_azure(username, photo, containername):
    container_client = connection_string.get_container_client(containername)

    # Base64 veriyi çöz ve PIL Image instance oluştur
    image_data = base64.b64decode(photo)
    image = Image.open(io.BytesIO(image_data))

    # Image'in orijinal boyutlarını al
    original_width, original_height = image.size

    # Ölçek faktörünü ve kaliteyi hesaplamak için formül
    max_dimension = max(original_width, original_height)

    # 1000 pikselden küçük resimler için (yaklaşık %90 boyutunda ve kalite yüksek)
    # 3000 pikselden büyük resimler için (yaklaşık %30 boyutunda ve kalite düşük)
    scale_factor = 1 - 0.7 * ((max_dimension - 1000) / 2000)
    scale_factor = max(0.3, min(scale_factor, 0.9))  # %30 ile %90 arasında sınırlıyoruz

    quality = 80 - 60 * ((max_dimension - 1000) / 2000)
    quality = max(
        20, min(int(quality), 80)
    )  # Kaliteyi %20 ile %80 arasında sınırlıyoruz

    new_width = max(int(original_width * scale_factor), MIN_WIDTH)
    new_height = max(int(original_height * scale_factor), MIN_HEIGHT)

    # Image'i yeniden boyutlandır
    image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # ByteIO stream oluştur
    image_stream = io.BytesIO()

    # Kalite parametresi ile image save yap
    image.save(image_stream, format="JPEG", quality=quality)

    # Stream başını resetle
    image_stream.seek(0)

    # Benzersiz bir blob ismi oluştur
    blob_name = f"QpFace_{containername}_{username}.jpg"

    # Blob client oluştur ve image upload yap
    blob_client = container_client.get_blob_client(blob_name)
    blob_client.upload_blob(
        image_stream, blob_type="BlockBlob", content_type="image/jpeg", overwrite=True
    )

    # Blob URL'yi return et
    photo_url = blob_client.url
    return photo_url


def delete_user_blob(container_client, username):
    blob_list = container_client.list_blobs(
        name_starts_with="QpFace_" + container_client.container_name + "_" + username
    )
    for blob in blob_list:
        blob_client = container_client.get_blob_client(blob)
        blob_client.delete_blob()


def delete_from_table(query, container_name):
    client = CosmosClient(config["ACCOUNT_HOST"], config["ACCOUNT_KEY"])
    database = client.get_database_client(config["DATABASE_ID"])
    container = database.get_container_client(container_name)

    analysis_items = list(
        container.query_items(query=query, enable_cross_partition_query=True)
    )

    for item in analysis_items:
        try:
            container.delete_item(item=item["id"], partition_key=item["username"])
            print(f"Deleted item with id: {item['id']}")
        except Exception as e:
            print(f"Failed to delete item with id: {item['id']}, Error: {str(e)}")


def firebase_fcm_notification(token, message, post_type=None, post_id=None):
    
    def _get_access_token():
        credentials = service_account.Credentials.from_service_account_file("qpfacemobile-firebase-adminsdk-as8qd-4b6b9004b9.json", scopes=["https://www.googleapis.com/auth/firebase.messaging"])
        request = google.auth.transport.requests.Request()
        credentials.refresh(request)
        return credentials.token

    url = "https://fcm.googleapis.com/v1/projects/qpfacemobile/messages:send"
    data = {
        "message": {
            "token": token,
            "notification": {
                "body": message,
                "title": "Qpface",
            },
            "data": {"post_type": post_type, "post_id": post_id},
        }
    }

    headers = {
        'Authorization': 'Bearer ' + _get_access_token(),
        'Content-Type': 'application/json; UTF-8',
    }

    response = requests.post(url, json=data, headers=headers)
    return response



def update_all_user_data(username, new_firstname, new_lastname, new_profile_pic):
    containers = [matches_container, mood_container, analysis_container]

    for container in containers:
        # Kullanıcıya ait verileri güncelle
        query = "SELECT * FROM c WHERE c.username = @username"
        query_params = [{"name": "@username", "value": username}]
        items = list(
            container.query_items(
                query=query, parameters=query_params, enable_cross_partition_query=True
            )
        )

        for item in items:
            # Kullanıcı bilgilerini güncelle
            item["firstname"] = new_firstname
            item["lastname"] = new_lastname
            item["profile_pic"] = new_profile_pic

            # likes ve comments alt öğelerini güncelle
            if "likes" in item:
                for like in item["likes"]:
                    if like["username"] == username:
                        like["firstname"] = new_firstname
                        like["lastname"] = new_lastname
                        like["profile_pic"] = new_profile_pic

            if "comments" in item:
                for comment in item["comments"]:
                    if comment["username"] == username:
                        comment["firstname"] = new_firstname
                        comment["lastname"] = new_lastname
                        comment["profile_pic"] = new_profile_pic

            try:
                container.replace_item(item=item["id"], body=item)
            except Exception as e:
                print(f"Failed to update item in {container.id}. Exception: {str(e)}")

    # Diğer kullanıcıların like ve comments içeren verilerini güncelle
    for container in containers:
        # Tüm öğeleri sorgula (tüm kullanıcılar için)
        query = "SELECT * FROM c"
        items = list(
            container.query_items(query=query, enable_cross_partition_query=True)
        )

        for item in items:
            updated = False
            # likes alt öğelerini güncelle
            if "likes" in item:
                for like in item["likes"]:
                    if like["username"] == username:
                        like["firstname"] = new_firstname
                        like["lastname"] = new_lastname
                        like["profile_pic"] = new_profile_pic
                        updated = True

            # comments alt öğelerini güncelle
            if "comments" in item:
                for comment in item["comments"]:
                    if comment["username"] == username:
                        comment["firstname"] = new_firstname
                        comment["lastname"] = new_lastname
                        comment["profile_pic"] = new_profile_pic
                        updated = True

            if updated:
                try:
                    container.replace_item(item=item["id"], body=item)
                except Exception as e:
                    print(
                        f"Failed to update item in {container.id}. Exception: {str(e)}"
                    )


def generate_unique_key(text1, text2):
    # Bir set oluşturup, metinleri sıralı hale getir
    unique_elements = sorted({text1, text2})

    # Set'e dönüştürülmüş ve sıralanmış metinlerin birleşimini oluştur
    combined_sorted = f"{unique_elements[0]}_{unique_elements[1]}"

    # Benzersiz anahtar oluşturmak için bir hash fonksiyonu kullan
    key = hashlib.md5(combined_sorted.encode()).hexdigest()

    # Anahtarın rakamla başlamadığından emin olun
    if key[0].isdigit():
        key = "a" + key  # Başına 'a' ekleyin

    return str(key)
