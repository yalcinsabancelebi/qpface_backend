import asyncio
import azure.functions as func
import Users,Analysis,Matches,Moods,Social,Login,Posts,Notifications,Message

# FOTOGRAF ATILDIGINDA RESPONSE DONDUREN ENDPOINT
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)
@app.route(route="Analysis/v1/{username}/send")
def analysis_send(req: func.HttpRequest) -> func.HttpResponse:
    username = req.route_params.get('username')

    photo = req.files['photo']
    
    result=Analysis.send(photo,username)
    return func.HttpResponse(result,mimetype="application/json")


@app.route(route="Analysis/v1/{username}/save", auth_level=func.AuthLevel.ANONYMOUS)
async def analysis_save(req: func.HttpRequest) -> func.HttpResponse:
    username = req.route_params.get('username')
    isShared = req.params.get('isShared')
    data = req.get_json()

    result = await Analysis.save(username, isShared, data)
    return func.HttpResponse(result, mimetype="application/json")

# KULLANICI KAYIT OLDUGUNDA EKLENEN ENDPOINT
@app.route(route="Users/v1/{username}/register", auth_level=func.AuthLevel.ANONYMOUS)
async def user_register(req: func.HttpRequest) -> func.HttpResponse:

    username = req.route_params.get('username')
    token = req.get_json().get('token')
    mail = req.get_json().get('mail')
    name = req.get_json().get('name')
    surname = req.get_json().get('surname')

    result = await Users.register(username,token,mail,name,surname)
    return func.HttpResponse(result,mimetype="application/json")

# KULLANICI GÜNCELLEME
@app.route(route="Users/v1/{username}/update", auth_level=func.AuthLevel.ANONYMOUS)
def user_update(req: func.HttpRequest) -> func.HttpResponse:

    username = req.route_params.get('username')

    mail = req.get_json().get('mail')
    name = req.get_json().get('name')
    surname = req.get_json().get('surname')
    profile_pic = req.get_json().get('profile_pic')
    cover_pic = req.get_json().get('cover_pic')
    gender= req.get_json().get('gender')
    birthdate= req.get_json().get('birthdate')
    biography= req.get_json().get('biography')
    
    settings= req.get_json().get('settings')
    privateAccount= settings.get('privateAccount')
    receiveMessagesFromNonFollowers= settings.get('receiveMessagesFromNonFollowers')
    
    result=Users.update(username,mail,name,surname,profile_pic,cover_pic,gender,birthdate,biography,privateAccount,receiveMessagesFromNonFollowers)
    return func.HttpResponse(result,mimetype="application/json")

# DELETE ANALİZ
@app.route(route="Analysis/v1/{username}/delete", auth_level=func.AuthLevel.ANONYMOUS)
def analysis_delete(req: func.HttpRequest) -> func.HttpResponse:
   
    username =req.route_params.get('username')
    analysis_id = req.get_json().get('Analysis_Id')
    
    
    delete_analysis = Analysis.delete(username, analysis_id)
    return func.HttpResponse(delete_analysis,mimetype="application/json")


# KULLANICI SİLME
@app.route(route="Users/v1/{username}/delete", auth_level=func.AuthLevel.ANONYMOUS)
def user_delete(req: func.HttpRequest) -> func.HttpResponse:
    username = req.route_params.get('username')

    delete_users=Users.delete(username)

    return func.HttpResponse(delete_users,mimetype="application/json")

# KULLANICI UYUM YÜZDESİ
@app.route(route="Matches/v1/{username}/send", auth_level=func.AuthLevel.ANONYMOUS)
def matches_send(req: func.HttpRequest) -> func.HttpResponse:
    username = req.route_params.get('username')
    type = req.params.get('type')
    file1=req.files['user_1']
    file2=req.files['user_2']
    

    result=Matches.send(username,type,file1,file2)

    return func.HttpResponse(result,mimetype="application/json")



@app.route(route="Matches/v1/{username}/delete", auth_level=func.AuthLevel.ANONYMOUS)
def matches_delete(req: func.HttpRequest) -> func.HttpResponse:
    
    username = req.route_params.get('username')
    id = req.get_json().get('id')
    result=Matches.delete(username,id)
    return func.HttpResponse(result, mimetype="application/json")



@app.route(route="Moods/v1/{username}/send", auth_level=func.AuthLevel.ANONYMOUS)
def mood_send(req: func.HttpRequest) -> func.HttpResponse:
    photo = req.files['photo']
    username=req.route_params.get('username')
    result=Moods.send(photo,username)
   
    return func.HttpResponse(result,mimetype="application/json")


@app.route(route="Matches/v1/{username}/save", auth_level=func.AuthLevel.ANONYMOUS)
def matches_save(req: func.HttpRequest) -> func.HttpResponse:
   
    username=req.route_params.get('username')
    isShared=req.params.get('isShared')
    data = req.get_json()
   
    result=Matches.save(username,isShared,data)
    return func.HttpResponse(result,mimetype="application/json")


@app.route(route="Follow/v1", auth_level=func.AuthLevel.ANONYMOUS)
def followed(req: func.HttpRequest) -> func.HttpResponse:
    sender=req.get_json().get("sender")
    receiver=req.get_json().get("receiver")
    type=req.get_json().get("type")


    request=Social.follow(sender,receiver,type)
    return func.HttpResponse(request, status_code=200,mimetype="application/json")


@app.route(route="Unfollow/v1", auth_level=func.AuthLevel.ANONYMOUS)
def unfollowed(req: func.HttpRequest) -> func.HttpResponse:
    sender=req.get_json().get("sender")
    receiver=req.get_json().get("receiver")

    request=Social.unfollow(sender,receiver)
    return func.HttpResponse(request, status_code=200)


@app.route(route="Receive/v1/{type}", auth_level=func.AuthLevel.ANONYMOUS)
def social_receive(req: func.HttpRequest) -> func.HttpResponse:
    type=req.route_params.get('type')
    sender = req.get_json().get("sender")
    receiver = req.get_json().get("receiver")
    status=req.get_json().get("status")

    request=Social.response(sender,receiver,type,status)
    return func.HttpResponse(request, status_code=200)


@app.route(route="Users/v1/list", auth_level=func.AuthLevel.ANONYMOUS)
def user_List(req: func.HttpRequest) -> func.HttpResponse:
    alluser=Social.userList()
    return func.HttpResponse(alluser, status_code=200,mimetype="application/json")

@app.route(route="Users/v1/{username}/fetch", auth_level=func.AuthLevel.ANONYMOUS)
def fetch_user(req: func.HttpRequest) -> func.HttpResponse:
    username=req.route_params.get("username")
    from_user=req.params.get("from")
    user=Users.fetch(username,from_user)
    return func.HttpResponse(user, status_code=200,mimetype="application/json")


@app.route(route="Mood/v1/{username}/save", auth_level=func.AuthLevel.ANONYMOUS)
def mood_save(req: func.HttpRequest) -> func.HttpResponse:
    username=req.route_params.get('username')
    isShared=req.params.get('isShared')
    data= req.get_json()

    result=Moods.save(username,isShared,data)
    return func.HttpResponse(result,mimetype="application/json")



@app.route(route="Mood/v1/{username}/delete", auth_level=func.AuthLevel.ANONYMOUS)
def mood_delete(req: func.HttpRequest) -> func.HttpResponse:
     
    username = req.route_params.get('username')
    id = req.get_json().get('id')
    result=Moods.delete(username,id)
    return func.HttpResponse(result, mimetype="application/json")



@app.route(route="login/{username}", auth_level=func.AuthLevel.ANONYMOUS)
async def giris(req: func.HttpRequest) -> func.HttpResponse:
    username=req.route_params.get('username')
    fcm_token=req.get_json().get('fcm_token')
    result=await Login.girisyap(username,fcm_token)
    return func.HttpResponse(result,mimetype="application/json")



@app.route(route="homepage/{username}/fetch", auth_level=func.AuthLevel.ANONYMOUS)
async def homepage_fetch(req: func.HttpRequest) -> func.HttpResponse:
    username = req.route_params.get('username')
    results = await Posts.homepage(username)
    return func.HttpResponse(results, status_code=200, mimetype="application/json")


   

@app.route(route="explore/{username}/fetch", auth_level=func.AuthLevel.ANONYMOUS)
async def explore_fetch(req: func.HttpRequest) -> func.HttpResponse:
    username = req.route_params.get('username')

    results = await Posts.explore(username)

    return func.HttpResponse(results, status_code=200, mimetype="application/json")



@app.route(route="Notifications/{user}", auth_level=func.AuthLevel.ANONYMOUS)
def notification_fetch(req: func.HttpRequest) -> func.HttpResponse:
   
    user = req.route_params.get('user')
    is_read=req.params.get('is_read')
    result=Notifications.fetch(user,is_read)
    return func.HttpResponse(result, mimetype="application/json")

@app.route(route="like", auth_level=func.AuthLevel.ANONYMOUS)
def likes(req: func.HttpRequest) -> func.HttpResponse:
    post_id = req.get_json().get('post_id')
    sender = req.get_json().get('sender')
    receiver = req.get_json().get('receiver')
    post_type = req.get_json().get('post_type')
  
    result=Posts.like(post_id,sender,receiver,post_type)
    return func.HttpResponse(result,mimetype="application/json")

@app.route(route="comment", auth_level=func.AuthLevel.ANONYMOUS)
def comments(req: func.HttpRequest) -> func.HttpResponse:
    post_id = req.get_json().get('post_id')
    sender = req.get_json().get('sender')
    receiver = req.get_json().get('receiver')
    post_type = req.get_json().get('post_type')
    comment_text = req.get_json().get('comment_text')
    result=Posts.comment(post_id,sender,receiver,post_type,comment_text)
    return func.HttpResponse(result,mimetype="application/json")

@app.route(route="comment/delete", auth_level=func.AuthLevel.ANONYMOUS)
def delete_comments(req: func.HttpRequest) -> func.HttpResponse:
    post_id = req.get_json().get('post_id')
    post_type = req.get_json().get('post_type')
    comment_id = req.get_json().get('comment_id')

    result=Posts.delete_comment(post_id,post_type,comment_id)
    return func.HttpResponse(result,mimetype="application/json")


@app.route(route="Users/messages/list", auth_level=func.AuthLevel.ANONYMOUS)
async def messagelist(req: func.HttpRequest) -> func.HttpResponse:
    sender = req.get_json().get('sender')
    result = await Message.message_list(sender)

    return func.HttpResponse(result,mimetype="application/json")


@app.route(route="Users/messages/fetch", auth_level=func.AuthLevel.ANONYMOUS)
async def messagefetch(req: func.HttpRequest) -> func.HttpResponse:
    sender = req.get_json().get('sender')
    receiver = req.get_json().get('receiver')
    result = await Message.message_fetch(sender,receiver)

    return func.HttpResponse(result,mimetype="application/json")


@app.route(route="Users/messages/send", auth_level=func.AuthLevel.ANONYMOUS)
def message_send(req: func.HttpRequest) -> func.HttpResponse:
    
    sender = req.get_json().get('sender')
    receiver = req.get_json().get('receiver')
    message = req.get_json().get('message')
    post_type = req.get_json().get('post_type')
    post_id = req.get_json().get('post_id')

    
    result = asyncio.run(Message.send(sender, receiver, message,post_type,post_id))
    
    return func.HttpResponse(result,mimetype="application/json")


@app.route(route="Users/messages/delete", auth_level=func.AuthLevel.ANONYMOUS)
def message_delete(req: func.HttpRequest) -> func.HttpResponse:
    try:
        req_body = req.get_json()
        sender = req_body.get('sender')
        receiver = req_body.get('receiver')
        wipeall = req_body.get('wipeall', None)


        if wipeall:
            result = Message.delete_message(sender, receiver, wipeall=True)
        else:
            message_id = req_body.get('message_id')
            if not message_id:
                return func.HttpResponse(
                    "message_id is required for single message deletion.",
                    status_code=400
                )
            result = Message.delete_message(sender, receiver, message_id=message_id)

        return func.HttpResponse(result, mimetype="application/json")

    except Exception as e:
        return func.HttpResponse(
            str(e),
            status_code=500
        )

@app.route(route="Posts/{container_type}/{post_id}/details", auth_level=func.AuthLevel.ANONYMOUS)
def post_details(req: func.HttpRequest) -> func.HttpResponse:

    post_id=req.route_params.get("post_id")
    container_type=req.route_params.get("container_type")
    results=Posts.details(post_id,container_type)
    return func.HttpResponse(results,mimetype="application/json")



@app.route(route="Logout/{username}", auth_level=func.AuthLevel.ANONYMOUS)
def cikis_yap(req: func.HttpRequest) -> func.HttpResponse:

    username=req.route_params.get("username")
    results=Login.cikis(username)
    return func.HttpResponse(results,mimetype="application/json")