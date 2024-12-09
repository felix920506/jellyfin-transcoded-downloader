import requests
import sessioncontroller
import urllib.parse
import os

URL = "example.com"
USER = "user"
PASSWORD = "password"

# login to server

if not sessioncontroller.validateCurrentSession():
    sessioncontroller.loginUsername(URL,USER,PASSWORD)

# Get available Libraries

ALLOWED_LIB_TYPES = ("movies", "tvshows")
views = sessioncontroller.get("UserViews").json()['Items']
views = [view for view in views if view['CollectionType'] in ALLOWED_LIB_TYPES]

# Select Library

lib = views[0]
if len(views) > 1:
    print("Available Libraries:")
    for i in range(len(views)):
        print(f'    {i}. {views[i]['Name']}')

    lib = input(f'Choose a library [0-{len(views)-1}]: ')
    lib = views[int(lib)]

print(f'Selected Library: {lib['Name']}, type: {lib['CollectionType']}')

queue = [lib]
VIDEO_TYPES = ('Episode', 'Movie')
COLLECTION_TYPES = ('CollectionFolder', 'Series')

BaseParams = {
    'ApiKey': sessioncontroller._token,
    'videoCodec': 'h264',
    'maxVideoBitDepth': 8,
    'h264-deinterlace': True,
    'videoBitRate': 10000000,
    'width': 1920,
    'height': 1080,
    'audioCodec': 'aac',
    'audioBitRate': 256000,
    'maxAudioChannels': 2,
    'audioSampleRate': 48000,
    'maxAudioBitDepth': 16,
    'subtitleMethod': 'Encode'
}



while len(queue) > 0:
    item = queue.pop(0)
    if item['Type'] in COLLECTION_TYPES:
        res = sessioncontroller.get("Items",{'parentId':item['Id']}).json()['Items']
        t = res[0]
        if len(res) > 1:
            print("Available Items:")
            for i in range(len(res)):
                print(f'    {i}. {res[i]['Name']}')

            t = input(f'Choose an item [0-{len(res)-1}]: ')
            t = res[int(t)]
        print(f'Selected Item: {t['Name']}, type: {t['Type']}')
        queue.append(t)
    
    elif item['Type'] == 'Season':
        eps = sessioncontroller.get("Items",{'parentId':item['Id']}).json()['Items']
        streams = sessioncontroller.get(f"Items/{eps[0]['Id']}").json()['MediaStreams']
        videos = []
        audios = []
        subs = []
        for stream in streams:
            match stream['Type']:
                case 'Video':
                    videos.append(stream)
                case 'Audio':
                    audios.append(stream)
                case 'Subtitle':
                    subs.append(stream)
                case _:
                    pass
        
        video = videos[0]
        audio = audios[0]
        sub = None

        if len(videos) > 1:
            print('Select Video Stream:')
            for i in range(len(videos)):
                print(f'    {i}. {videos[i]['DisplayTitle']}')

            video = input(f'Choose an item [0-{len(videos)-1}]: ')
            video = videos[int(video)]
        
        if len(audios) > 1:
            print('Select Audio Stream:')
            for i in range(len(audios)):
                print(f'    {i}. {audios[i]['DisplayTitle']}')

            audio = input(f'Choose an item [0-{len(audios)-1}]: ')
            audio = audios[int(audio)]

        if len(subs) > 0:
            print('Select Subtitle Stream:')
            for i in range(len(subs)):
                print(f'    {i}. {subs[i]['DisplayTitle']}')

            sub = input(f'Choose an item, leave blank for none [0-{len(subs)-1}]: ')
            sub = subs[int(sub)] if sub else None

        print('Selected Streams:')
        print(f'    Video: {video['DisplayTitle']}')
        print(f'    Audio: {audio['DisplayTitle']}')
        if sub is not None:
            print(f'    Subtitle: {sub['DisplayTitle']}')

        for ep in eps:
            url = f'{sessioncontroller.serverIp}/Videos/{ep['Id']}/main.m3u8?'
            params = BaseParams.copy()
            
            filename = f'{ep['SeriesName']} {ep['SeasonName']} EP.{ep['IndexNumber']:02d} - {ep['Name']}.mp4'
            ep = sessioncontroller.get(f"Items/{ep['Id']}").json()

            params['videoStreamIndex'] = [s for s in ep['MediaStreams'] if s['DisplayTitle'] == video['DisplayTitle']][0]['Index']
            params['audioStreamIndex'] = [s for s in ep['MediaStreams'] if s['DisplayTitle'] == audio['DisplayTitle']][0]['Index']
            if sub is not None:
                params['subtitleStreamIndex'] = [s for s in ep['MediaStreams'] if s['DisplayTitle'] == sub['DisplayTitle']][0]['Index']


            url += urllib.parse.urlencode(params)

            os.system(f'ffmpeg -i "{url}" -c copy "{filename}"')

    elif item['Type'] == 'Movie':
        streams = sessioncontroller.get(f"Items/{item['Id']}").json()['MediaStreams']
        videos = []
        audios = []
        subs = []
        for stream in streams:
            match stream['Type']:
                case 'Video':
                    videos.append(stream)
                case 'Audio':
                    audios.append(stream)
                case 'Subtitle':
                    subs.append(stream)
                case _:
                    pass
        
        video = videos[0]
        audio = audios[0]
        sub = None

        if len(videos) > 1:
            print('Select Video Stream:')
            for i in range(len(videos)):
                print(f'    {i}. {videos[i]['DisplayTitle']}')

            video = input(f'Choose an item [0-{len(videos)-1}]: ')
            video = videos[int(video)]
        
        if len(audios) > 1:
            print('Select Audio Stream:')
            for i in range(len(audios)):
                print(f'    {i}. {audios[i]['DisplayTitle']}')

            audio = input(f'Choose an item [0-{len(audios)-1}]: ')
            audio = audios[int(audio)]

        if len(subs) > 0:
            print('Select Subtitle Stream:')
            for i in range(len(subs)):
                print(f'    {i}. {subs[i]['DisplayTitle']}')

            sub = input(f'Choose an item, leave blank for none [0-{len(subs)-1}]: ')
            sub = subs[int(sub)] if sub else None

        print('Selected Streams:')
        print(f'    Video: {video['DisplayTitle']}')
        print(f'    Audio: {audio['DisplayTitle']}')
        if sub is not None:
            print(f'    Subtitle: {sub['DisplayTitle']}')


        url = f'{sessioncontroller.serverIp}/Videos/{item['Id']}/main.m3u8?'
        params = BaseParams.copy()
        
        filename = f'{item['Name']}.mp4'

        params['videoStreamIndex'] = video['Index']
        params['audioStreamIndex'] = audio['Index']
        if sub is not None:
            params['subtitleStreamIndex'] = sub['Index']


        url += urllib.parse.urlencode(params)

        os.system(f'ffmpeg -i "{url}" -c copy "{filename}"')

    else:
        print(item)


