import requests
import sessioncontroller
import urllib.parse
import os

URL = "example.com"
USER = "user"
PASSWORD = "password"
# filter illegal chars
ILLEGAL_CHARS = ['<', '>', ':', '"', "'", '/', '\\', '|', '?', '*']
TRANSLATION_TABLE = str.maketrans({char: '_' for char in ILLEGAL_CHARS})

# login to server

if not sessioncontroller.validateCurrentSession():
    sessioncontroller.loginUsername(URL,USER,PASSWORD)

# Format Selector
print("Select Format:")
formats = [
    ("h264", "aac", "mp4", "Best compatibility"),
    ("hevc", "aac", "mp4", "Best Quality"),
    ("av1", "opus", "webm", "For newer Chromebooks that can't play HEVC (playback might use more power)")
]

for i in range(len(formats)):
    print(f'    {i}. {formats[i][0]} + {formats[i][1]} in {formats[i][2]}')
download_format = int(input(f'Choose download format [0-{len(formats)-1}]: '))
download_format = formats[download_format]
print(f'Chosen format: {download_format[0]} + {download_format[1]} in {download_format[2]}')

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
    'videoCodec': download_format[0],
    'maxVideoBitDepth': 8,
    'deinterlace': True,
    'videoBitRate': 10000000,
    'width': 1920,
    'height': 1080,
    'audioCodec': download_format[1],
    'audioBitRate': 256000,
    'maxAudioChannels': 2,
    'audioSampleRate': 48000,
    'maxAudioBitDepth': 16,
    'subtitleMethod': 'Encode',
    'segmentContainer': 'mp4'
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
        
        chosenVideo = None
        chosenAudio = None
        chosenSub = None
        downloadList = []

        for ep in eps:

            epno = ep.get('IndexNumber')
            if epno is None:
                epno = 0
            print(f"Preprocessing {ep['SeriesName']} {ep['SeasonName']} EP.{epno} - {ep['Name']}")
            ep = sessioncontroller.get(f"Items/{ep['Id']}").json()
            streams = ep['MediaStreams']
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
            
            video = [s for s in streams if s['DisplayTitle'] == chosenVideo]
            audio = [s for s in streams if s['DisplayTitle'] == chosenAudio]
            sub = [s for s in streams if s['DisplayTitle'] == chosenSub]

            if video:
                video = video[0]
            
            else:
                if len(videos) > 1:
                    print('Select Video Stream:')
                    for i in range(len(videos)):
                        print(f'    {i}. {videos[i]['DisplayTitle']}')

                    video = input(f'Choose an item [0-{len(videos)-1}]: ')
                    video = videos[int(video)]
                else:
                    video = videos[0]
                
                chosenVideo = video['DisplayTitle']
            
            if audio:
                audio = audio[0]
            else:
                if len(audios) > 1:
                    print('Select Audio Stream:')
                    for i in range(len(audios)):
                        print(f'    {i}. {audios[i]['DisplayTitle']}')

                    audio = input(f'Choose an item [0-{len(audios)-1}]: ')
                    audio = audios[int(audio)]
                else:
                    audio = audios[0]
                
                chosenAudio = audio['DisplayTitle']

            if sub:
                sub = sub[0]

            else:
                if len(subs) > 0:
                    print('Select Subtitle Stream:')
                    for i in range(len(subs)):
                        print(f'    {i}. {subs[i]['DisplayTitle']}')

                    sub = input(f'Choose an item, leave blank for none [0-{len(subs)-1}]: ')
                    sub = subs[int(sub)] if sub else None
                
                if sub:
                    chosenSub = sub['DisplayTitle']
                else:
                    chosenSub = None

            # print('Selected Streams:')
            # print(f'    Video: {video['DisplayTitle']}')
            # print(f'    Audio: {audio['DisplayTitle']}')
            # if sub is not None:
            #     print(f'    Subtitle: {sub['DisplayTitle']}')


            url = f'{sessioncontroller.serverIp}/Videos/{ep['Id']}/main.m3u8?'
            params = BaseParams.copy()
            

            # epno = ep.get('IndexNumber')
            # if epno is None:
            #     epno = 0
            
            filename = f'{ep['SeriesName'].translate(TRANSLATION_TABLE)} {ep['SeasonName'].translate(TRANSLATION_TABLE)} EP.{epno:02d} - {ep['Name'].translate(TRANSLATION_TABLE)}.{download_format[2]}'
            ep = sessioncontroller.get(f"Items/{ep['Id']}").json()

            params['videoStreamIndex'] = [s for s in ep['MediaStreams'] if s['DisplayTitle'] == video['DisplayTitle']][0]['Index']
            params['audioStreamIndex'] = [s for s in ep['MediaStreams'] if s['DisplayTitle'] == audio['DisplayTitle']][0]['Index']
            if sub:
                params['subtitleStreamIndex'] = [s for s in ep['MediaStreams'] if s['DisplayTitle'] == sub['DisplayTitle']][0]['Index']


            url += urllib.parse.urlencode(params)

            config = {
                'filename': filename,
                'id': ep['Id'],
                'params': params
            }

            downloadList.append(config)
        
        for i in downloadList:
            session_url = f'Items/{i['id']}/PlaybackInfo'
            session_resp = sessioncontroller.post(session_url)
            session_id = session_resp.json()['PlaySessionId']
            sessionbody = {
                'SessionId': session_id,
                'ItemId': i['id']
            }

            start_url = f'Sessions/Playing'
            start_resp = sessioncontroller.post(start_url, rjson=sessionbody)

            params = i['params']
            params['playSessionId'] = session_id
            url = f'{sessioncontroller.serverIp}/Videos/{i['id']}/main.m3u8?{urllib.parse.urlencode(params)}'
            filename = i['filename']
            os.system(f'ffmpeg -i "{url}" -c copy "{filename}"')


            stop_url = f"PlayingItems/{i['id']}"

            stop_resp = sessioncontroller.delete(stop_url, params={'playSessionId': session_id})

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


