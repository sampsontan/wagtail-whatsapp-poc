import requests
import json
import sys
from io import BytesIO

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from bakerydemo.breads.models import BreadPage
from bakerydemo.webhooks.decorators import is_engage_api


@csrf_exempt
@is_engage_api
def whatsapp(request):
    token = settings.WEBHOOKS_WHATSAPP_TOKEN
    url = 'https://whatsapp.praekelt.org/v1/messages'
    try:
        body = json.loads(request.body.decode('utf-8'))
        message = body["messages"][0]["text"]["body"]
        contact = body["contacts"][0]["wa_id"]
        name =  body["contacts"][0]["profile"]["name"]
    except:
        return HttpResponse('No body in request')
    if message:
        if 'Join' in message or 'join' in message:
            body = "Welcome %s. I can help you find information about bread. Please type in a type of bread that you would like to know more about, and I will send you a message with some details about that bread! 😊🥖" % name
            data = {
            "preview_url": False,
            "recipient_type": "individual",
            "to": contact,
            "type": "text",
            "text": {
                "body": body
            }
            }
            headers={
                'Authorization': 'Bearer %s' % token,
                'Content-Type': 'application/json'
            }
            response = requests.post(
                url, data=json.dumps(data), headers=headers)
            return HttpResponse(response)
        elif 'search' in message or 'Search' in message:
            # TODO: return whole body not just introduction
            search_word = message[7:]
            results = BreadPage.objects.live().search(search_word)
            if len(results) == 1:
                body = results[0].introduction
                body += "\n" + results[0].get_full_url()
            elif len(results) > 1:
                body = "We've found %s articles:" % len(results)
                for result in results:
                    body += "\n\n" + result.introduction
                    body += "\n" + result.get_full_url()
            else:
                body = "Sorry, we couldn't find an article matching that keyword"
            data = {
                "preview_url": False,
                "recipient_type": "individual",
                "to": contact,
                "type": "text",
                "text": {
                    "body": body
                }
            }
            headers={
                'Authorization': 'Bearer %s' % token,
                'Content-Type': 'application/json'
            }
            response = requests.post(
                url, data=json.dumps(data), headers=headers)
            return HttpResponse(response)
        else:
            headers = {
                'Authorization': 'Bearer %s' % token,
                'Content-Type': 'application/json'
            }
            try:
                page = BreadPage.objects.get(title__icontains=message)
                if page.image:
                     # get image from admin
                    image = page.image
                    r = image.get_rendition('fill-300x150|jpegquality-80')
                    with r.image.open_file() as f:
                        # image_bytes = f.read()
                        media_url = 'https://whatsapp.praekelt.org/v1/media'
                        image_headers = {
                            'Authorization': 'Bearer %s' % token,
                            'Content-Type': 'image/jpeg'
                        }
                        # upload image
                        image_upload_response = requests.post(
                            media_url, 
                            data=f, 
                            headers=image_headers
                        )
                        # get image id from response
                        data_1 = image_upload_response.json()
                        image_id = data_1['media'][0]['id']
        
                        # send media message with caption
                        data = {
                            "preview_url": False,
                            "recipient_type": "individual",
                            "to": contact,
                            "type": "image",
                            "image": {
                                "id": image_id,
                                "caption": page.introduction
                            }
                        }
                        
                        response = requests.post(
                            url, data=json.dumps(data), headers=headers)
                        return HttpResponse(response)

                else:
                     # send text message if no image
                    data = {
                        "preview_url": False,
                        "recipient_type": "individual",
                        "to": contact,
                        "type": "text",
                        "text": {
                            "body": page.introduction,
                        }
                    }
                    response = requests.post(
                        url, data=json.dumps(data), headers=headers)
            except:
                # no result or more than one result found
                data = {
                    "preview_url": False,
                    "recipient_type": "individual",
                    "to": contact,
                    "type": "text",
                    "text": {
                        "body": 'Please try again by typing search followed by keyword',
                    }
                }
                response = requests.post(
                    url, data=data, headers=headers)

    else:
        data = {
            "preview_url": False,
            "recipient_type": "individual",
            "to": contact,
            "type": "text",
            "text": {
                "body": "Please type in keyword to search..."
            }
        }
        headers={
            'Authorization': 'Bearer %s' % token,
            'Content-Type': 'application/json'
        }
        response = requests.post(
            url=url, data=json.dumps(data), headers=headers)
        return HttpResponse(response)

    return HttpResponse('I did nothing :/')