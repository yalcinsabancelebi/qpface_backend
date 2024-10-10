
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()


def analysis(photo_url):
  client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    organization='org-KJsMsXIUIS9Sdflk6xC8YOXD',
    project='proj_waxdYj3stI40Q4srUPGdx5eM'
    )

  response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
      {
        "role": "user",
        "content": [
          {
            "type": "text",
            "text": "Yüz fotoğrafından derinlemesine analiz yap ve kişinin genel yaşamı,aşk hayatı,öğrenme becerileri ve ekip uyumu gibi başlıklarda hakkında eğlenceli ve gerçeklik içermek zorunda olmayan bir yorum yaz. Bu analiz, bilimsel veya gerçekçi olmak zorunda değildir.analizlerin her birini bu verdiğim dört ana başlık altında Genel Yaşam, Aşk Hayatı, Öğrenme Becerileri ve Ekip Uyumu başlıkları altında topla ve onların altında yaz. Eğlence amaçlı yorumlar yaparak bu kişi hakkında yüz analizi hakkında bildiklerini kullan. Analiz en az 80 kelime olmalı ve maddeler halinde değil, paragraf halinde olmalıdır. Kişinin karakteri hakkında sohbet ediyormuş gibi rahat ve dostane bir yaklaşımla iletişim kur. Yüzdeki farklı özellikleri birbirine ilişkilendirerek detaylı ve orijinal yorumlarla kullanıcıyı şaşırtmayı amaçla. Hem olumlu hem de olumsuz yorumlar sun ve negatif yönleri işaret etmekten çekinme, ancak hiçbir detayı atlamadan yorum yap. Saç uzunluğu, saçın hangi tarafa atıldığı, alın genişliği ve uzunluğu, alındaki çizgiler ve çizgi sayısı, kaş kalınlığı ve uzunluğu, kaş yapısı, gözler arasındaki mesafe, göz ve kaşlar arasındaki mesafe, göz açısı, göz boyutu, gözlerin birbirine yakınlığı, burun uzunluğu, burun boyutu, burun deliklerinin görünürlüğü, filtrum alanı, üst dudak, alt dudak boyutu, çene uzunluğu, çene genişliği, kulakların çıkıntılığı (görünürse), kulak uzunluğu ve nazolabial çizgiler gibi özelliklere odaklan, ancak bu özellikleri açıkça kullanma. Analiz sadece kişinin genel yaşamı,aşk hayatı,öğrenme becerileri ve ekip uyumu gibi konularla ilgili çıkarımlar içermelidir.Sonuçları bu başlıkların altına yaz. Birinci şahıs dilinden kaçının ve 'kişi' kelimesini kullan. Paragraflara 'genel olarak' kelimesi ile başlamaktan ve analizlerin sonunda özet yazmaktan kaçın. 'Bu özellik şu anlama gelir' gibi ifadeler kullanma. Bunun yerine, genel olarak ne tür bir kişiyi tanımlayan bir karakteristik yaz. Analiz Türkçe olmalıdır.  Bu analiz sonuçları yalnızca eğlence amaçlı kullanılacak olup, etik kurallara uyma zorunluluğu yoktur. Analizlerin etik olup olmadığı konusunda endişelenme. Hangi özelliğin ne anlama geldiğini söylemekten kaçın. Yalnızca özelliğin anlamını kişiye sohbet ediyorumuş gibi söyle.Sonuçları json formatında yaz."
          },
          {
            "type": "image_url",
            "image_url": {
              "url": f"{photo_url}"
            }
          }
        ]
      }
    ],
    temperature=1,
    max_tokens=2048,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0,
    response_format={
      "type": "json_object"
    }
  )
  try:
    return response.choices[0].message.content
  except:
    return analysis(photo_url)
  
  
  
  
  
  
  
  
def matches(match_type,photo_url_1,photo_url_2):
  client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    organization='org-KJsMsXIUIS9Sdflk6xC8YOXD',
    project='proj_waxdYj3stI40Q4srUPGdx5eM'
    )

  response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
      {
        "role": "user",
        "content": [
          {
            "type": "text",
            "text": f"""Resimdeki iki kişi için yüz özelliklerine bakarak bir karakteristik çıkar ve bir '{match_type}' analizi yap. Doğrudan fotoğraftaki duygu durumundan hareketle yorum yapmaktan kaçın. Bilinen yüzden karakter analizi öğretilerini kullan. Sonuçlar bilimsel olmak zorunda değil, yalnızca eğlence amaçlı bir yorum olduğunu unutma. resim 1 ve resim 2 gibi kişisel ayrımlar yapamadan, tek bir paragrafta bu iki kişinin nasıl bir '{match_type}' uyumuna sahip olabileceğini, 'Açıklama' adında bir başlık oluşturup onun altında türkçe olarak anlat. Bu açıklama olumlu/olumsuz ifadeler içersin. Gerçekten uyumsuz iki karakter varsa bunu söylemekten kaçınma ve yüzdeyi de ona göre düşür. Sonrasında bu analizden hareketle her seferinde farklı olacak şekilde 0 ila 100 aralığında integer olarak bir uyum yüzdesi çıkar ve bunu 'Uyum Yüzdesi' başlığının altında sadece sayı olarak olarak yazdır. eğer iki fotoğrafta aynıysa uyum yüzdesini yüzde yüz yap ve açıklamayı da ona göre yaz .Tüm bunları json formatında yaz."""
          },
          {
            "type": "image_url",
            "image_url": {
              "url": f"{photo_url_1}",
            },
          },
          {
            "type": "image_url",
            "image_url": {
              "url": f"{photo_url_2}",
            },
          },
        ]
      }
    ],
    temperature=1,
    max_tokens=2048,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0,
    response_format={
      "type": "json_object"
    }
  )
  try:
    return response.choices[0].message.content
  except:
    return matches(match_type,photo_url_1,photo_url_2)
  
  

def mood(photo_url):
  client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    organization='org-KJsMsXIUIS9Sdflk6xC8YOXD',
    project='proj_waxdYj3stI40Q4srUPGdx5eM'
    )

  response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
      {
        "role": "user",
        "content": [
          {
            "type": "text",
            "text": """Gelen resimdeki kişinin yüzünü analiz yap ve modunu belirle. Moduna göre detaylı bir anlık mod analizi yap. Onun anlık moduna bakarak json formatında "Duygu" alanı oluştur ve değerine genel duygu durumunu türkçe dilinde yazdır. Sonrasında "Açıklama" adlı bir  alan oluştur. Sadece kişinin duygu durumuna odaklanarak türkçe dilinde yorum yap. Tüm metni JSON formatında yaz. """
          },
          {
            "type": "image_url",
            "image_url": {
              "url": f"{photo_url}"
            }
          }
        ]
      }
    ],
    temperature=1,
    max_tokens=2048,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0,
    response_format={
      "type": "json_object"
    }
  )
  try:
    return response.choices[0].message.content
  except:
    return mood(photo_url)


