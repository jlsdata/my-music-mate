# Created by jongwonkim on 07/07/2017.


import os
import logging
import json
import boto3
from botocore.exceptions import ClientError
from src.dynamodb.intents import DbIntents
from src.dynamodb.concerts import DbConcerts
import requests
from googleapiclient.discovery import build
from requests.exceptions import HTTPError
import random
import time
from urllib.parse import quote_plus


log = logging.getLogger()
log.setLevel(logging.DEBUG)
db_intents = DbIntents(os.environ['INTENTS_TABLE'])
db_concerts = DbConcerts(os.environ['CONCERTS_TABLE'])
sns = boto3.client('sns')


def mark_queued_concerts(queued):
    for concert in queued:
        db_response = db_concerts.add_concert({
            'team_id': concert['team_id'],
            'channel_id': concert['channel_id'],
            'artists': concert['artists'],
            'event_id': concert['event_id'],
            'event_name': concert['event_name'],
            'event_date': concert['event_date'],
            'event_venue': concert['event_venue'],
            'ticket_url': concert['ticket_url'],
            'interest': concert['interest'],
            'queued': True
        })
        log.info('!!! CONCERT DB UPDATE RESPONSE !!!')
        log.info(db_response)
        print('!!! CONCERT DB UPDATE RESPONSE !!!')
        print(db_response)


def publish_voting_ui(event, queued, artist_visited):
    event['intents']['callback_id'] = '1|' + ','.join(artist_visited)
    text = 'Please select one that you are most interested in within '
    sleep_duration = int(os.environ['DEFAULT_VOTING_TIMEOUT'])
    minutes = int(sleep_duration / 60)
    seconds = int(sleep_duration - minutes * 60)

    if minutes > 0:
        if minutes == 1:
            text += str(minutes) + ' minute'
        else:
            text += str(minutes) + ' minutes'
    if seconds > 0:
        if minutes > 0:
            text += ' '
        if seconds == 1:
            text += str(seconds) + ' second'
        else:
            text += str(seconds) + ' seconds'
    text += '.'

    attachments = [
        {
            'fallback': 'You are unable to vote',
            'callback_id': '1|' + ','.join(artist_visited),
            'color': os.environ['BLINK_OFF_COLOR'],
            'attachment_type': 'default',
            'actions': []
        }
    ]
    for i, concert in enumerate(queued):
        artists = []
        print('!!! CONCERT INDIVIDUAL !!!')
        print(concert)
        for artist in concert['artists']:
            artists.append(artist['name'])

        attachments[0]['actions'].append({
            'name': concert['event_name'],
            'text': '[0] ' + concert['event_name'],
            'type': 'button',
            'style': 'primary',
            'value': concert['event_id']
        })

    attachments[0]['actions'].append({
        'name': 'Other options?',
        'text': '[0] Other options?',
        'type': 'button',
        'value': '0'
    })

    log.info('!!! ATTACHMENTS !!!')
    log.info(attachments)
    print('!!! ATTACHMENTS !!!')
    print(attachments)
    sns_event = {
        'team': event['sessionAttributes']['team_id'],
        'token': event['sessionAttributes']['bot_token'],
        'channel': event['sessionAttributes']['channel_id'],
        'text': text,
        'attachments': attachments
    }
    log.info('!!! SNS EVENT !!!')
    log.info(sns_event)
    print('!!! SNS EVENT !!!')
    print(sns_event)
    print('!!! ARN ADDRRESS !!!')
    print(os.environ['POST_MESSAGE_SNS_ARN'])
    return sns.publish(
        TopicArn=os.environ['POST_MESSAGE_SNS_ARN'],
        Message=json.dumps({'default': json.dumps(sns_event)}),
        MessageStructure='json'
    )


def publish_concert_list(event, queued):
    # if len(queued) == 0:
    #     text = 'Sorry, I couldn\'t find any concert you might interested in.'
    # elif len(queued) > 1:
    #     text = 'Here are {} concerts that you guys might interested in.'.format(len(queued))
    # else:
    #     text = 'Hmm, I only found one option. Are you interested in?'
    print('!!! QUEUED !!!')
    print(queued)
    youtube = build(os.environ['YOUTUBE_API_SERVICE_NAME'], os.environ['YOUTUBE_API_VERSION'], developerKey=os.environ['DEVELOPER_KEY'])

    for i, concert in enumerate(queued):
        attachments = []
        artists = []
        print('!!! CONCERT INDIVIDUAL !!!')
        print(concert)
        for artist in concert['artists']:
            artists.append(artist['name'])
        search_response = youtube.search().list(
            q=concert['artists'][0]['name'] + " live concert",
            part="id,snippet",
            type="video",
            maxResults=1
        ).execute()
        result = search_response.get("items", [])
        youtubeurl = "http://youtube.com/watch?v=%s" % result[0]["id"]["videoId"]
        order = ''
        emoji = ''
        if i == 0:
            if len(queued) == i + 1:
                order = 'only'
                emoji = ':point_up:'
            else:
                order = 'first'
                emoji = ':point_up:'
        if i == 1:
            if len(queued) == i + 1:
                order = 'last'
                emoji = ':v:'
            else:
                order = 'second'
                emoji = ':v:'
        elif i == 2:
            if len(queued) == i + 1:
                order = 'last'
                emoji = ':spock-hand:'
            else:
                order = 'last'
            emoji = ':spock-hand:'

        # pretext += 'Here is the {} option. I chose this because you are interested in {}.'.format(
        #    order, concert['interest'])

        attachments.append({
            'title': concert['event_name'],
            'author_name': ', '.join(artists),
            'author_icon': concert['artists'][0]['thumb_url'],
            'fields': [
                {
                    'title': 'Concert Date:',
                    'value': concert['event_date'],
                    'short': True
                },
                {
                    'title': 'Concert Location:',
                    'value': concert['event_venue']['name'] + ', ' + concert['event_venue']['city'] + ', ' +
                             concert['event_venue']['region'],
                    'short': True
                },
                # {
                #     'title': 'Lineup:',
                #     'value': ', '.join(artists)
                # }
            ]
        })
        time.sleep(.5)
        # "Here is the {} option. I chose this because you are interested in {}. <{}| >".format(order, concert['interest'], youtubeurl)
        sns_event = {
            'token': event['sessionAttributes']['bot_token'],
            'channel': event['sessionAttributes']['channel_id'],
            'text': '{}Here is the {} option. <{}| >'.format(
                emoji, order, youtubeurl),
            'attachments': attachments
        }
        sns.publish(
            TopicArn=os.environ['POST_MESSAGE_SNS_ARN'],
            Message=json.dumps({'default': json.dumps(sns_event)}),
            MessageStructure='json'
        )

    log.info('!!! ATTACHMENTS !!!')
    log.info(attachments)
    print('!!! ATTACHMENTS !!!')
    print(attachments)
    # sns_event = {
    #     'token': event['sessionAttributes']['bot_token'],
    #     'channel': event['sessionAttributes']['channel_id'],
    #     'text': '',
    #     'attachments': attachments
    # }
    # log.info('!!! SNS EVENT !!!')
    # log.info(sns_event)
    # print('!!! SNS EVENT !!!')
    # print(sns_event)
    # print('!!! ARN ADDRRESS !!!')
    # print (os.environ['POST_MESSAGE_SNS_ARN'])
    # return sns.publish(
    #     TopicArn=os.environ['POST_MESSAGE_SNS_ARN'],
    #     Message=json.dumps({'default': json.dumps(sns_event)}),
    #     MessageStructure='json'
    # )
    return


def retrieve_intents(event):
    if 'sessionAttributes' not in event:
        raise Exception('Required keys: `team_id` and `channel_id` are not provided.')
    event['intents'] = db_intents.retrieve_intents(
        event['sessionAttributes']['team_id'],
        event['sessionAttributes']['channel_id']
    )


def store_intents(event):
    return db_intents.store_intents(
        keys={
            'team_id': event['sessionAttributes']['team_id'],
            'channel_id': event['sessionAttributes']['channel_id']
        },
        attributes=event['intents']
    )


def add_taste(event, taste_name, taste_type, interest):
    if taste_name.lower() not in event['intents']['tastes']:
        event['intents']['tastes'][taste_name.lower()] = {
            'taste_name': taste_name.lower(),
            'display_name': taste_name,
            'taste_type': taste_type,
            'interest': interest
        }
    log.info('!!! ADD TASTE !!!')
    log.info(event)


def add_genre_tastes(event):
    # Take each Genre from the Tastes table and use the lastfm API to obtain a random list of related artists (limit 3)
    log.info('!!! ADD GENRES TO TASTES !!!')
    log.info(event)
    genres = event['intents']['genres']
    for genre in genres:
        api_response = requests.get(os.environ['LASTFM_TOP_URL'].format(genre, os.environ['LASTFM_KEY']))
        log.info('!!! API RESPONSE !!!')
        log.info(api_response)
        top_albums = json.loads(api_response.text)['albums']['album']
        log.info('!!! TOP ALBUMS !!!')
        log.info(top_albums)
        # TODO When we shuffled the list, there is lot of chance that we pick artists who don't have concert schedules
        if os.environ['SHUFFLE_CONCERT_LIST'] == '1':
            random.shuffle(top_albums)
        log.info('!!! SHUFFLED TOP ALBUMS !!!')
        log.info(top_albums)
        for i, album in enumerate(top_albums):
            if i < int(os.environ['GENRE_TO_ARTIST_MAX']):
                add_taste(event, album['artist']['name'], 'artist', genre)
            else:
                break


def add_artist_tastes(event):
    log.info('!!! ADD ARTISTS TO TASTES !!!')
    log.info(event)
    artists = event['intents']['artists']
    for artist in artists:
        add_taste(event, artist, 'artist', artist)


def search_concerts(event):
    log.info('!!! SEARCH CONCERTS !!!')
    for key in event['intents']['tastes']:
        taste = event['intents']['tastes'][key]
        log.info('!!! CONCERT ITEM !!!')
        log.info(taste)
        if taste['taste_type'] == 'artist':
            try:
                print('!!! API ADDRESS !!!')
                print(os.environ['BIT_CONCERT_SEARCH_BY_ARTISTS_API'].format(
                        taste['taste_name'],
                        event['intents']['city'],
                        os.environ['CONCERT_SEARCH_RADIUS']))
                concerts = requests.get(
                    os.environ['BIT_CONCERT_SEARCH_BY_ARTISTS_API'].format(
                        taste['taste_name'],
                        event['intents']['city'],
                        os.environ['CONCERT_SEARCH_RADIUS']
                )).json()
                print('!!! api_response !!!')
                print(concerts)
                count = 0
                for concert in concerts:
                    if concert['ticket_url'] is not None:
                        artists = []
                        if 'artists' in concert:
                            for artist in concert['artists']:
                                artists.append({
                                    'name': artist['name'],
                                    'thumb_url': artist['thumb_url'],
                                    'image_url': artist['image_url']
                                })

                        if 'venue' in concert:
                            print('!!! CONVERT VENUE !!!')
                            print(concert['venue'])
                            concert['venue']['latitude'] = str(concert['venue']['latitude'])
                            concert['venue']['longitude'] = str(concert['venue']['longitude'])

                        try:
                            # Store concert data into a db table for tracking voting results.
                            db_response = db_concerts.add_concert({
                                'team_id': event['sessionAttributes']['team_id'],
                                'channel_id': event['sessionAttributes']['channel_id'],
                                'artists': artists,
                                'event_id': str(concert['id']),
                                'event_name': concert['title'],
                                'event_date': concert['formatted_datetime'],
                                'event_venue': concert['venue'],
                                'ticket_url': concert['ticket_url'],
                                'interest': taste['interest'],
                                'queued': False
                            })
                            log.info('!!! CONCERT DB ADD RESPONSE !!!')
                            log.info(db_response)
                            print('!!! CONCERT DB ADD RESPONSE !!!')
                            print(db_response)
                        except ClientError:
                            log.error('Conditional Check Failed Exception during concert search')
                    count += 1
                    if count >= 30:
                        break;
            except Exception as e:
                log.error('Error coming from BIT API')
                print('Error coming from BIT API')
                log.error(str(e))
                print(str(e))


def show_results(event):
    concerts = db_concerts.fetch_concerts(event['sessionAttributes']['channel_id'])
    print('!!! SHOW CONCERT RESULTS !!!')
    print(concerts)
    log.info('!!! SHOW CONCERT RESULTS !!!')
    log.info(concerts)
    artist_visited = []
    concerts_queued = []

    if os.environ['SHUFFLE_CONCERT_LIST'] == '1':
        random.shuffle(concerts)

    for concert in concerts:
        if len(concerts_queued) < int(os.environ['CONCERT_VOTE_OPTIONS_MAX']):
            print('!!! artist_visited !!!')
            print(artist_visited)
            print('!!! concerts_queued !!!')
            print(concerts_queued)
            artists = concert['artists']
            # First loop through concerts - get concerts whose artist = interest
            # False unless interest = artist AND not visited
            temp_artist_visited = []
            need_to_be_queued = True
            for artist in artists:
                if artist['name'].lower() not in artist_visited:
                    temp_artist_visited.append(artist['name'].lower())
                else:
                    need_to_be_queued = False
            # change concert['interest'] in temp_artist_visited
            # to any in temp_artist_visited in requested artists?
            if need_to_be_queued and concert['interest'] in temp_artist_visited:
                for temp_artist in temp_artist_visited:
                    artist_visited.append(temp_artist)
                concerts_queued.append(concert)
        else:
            log.info("breaking out of loop 1, 3 concerts found")
            break
    for concert in concerts:
        if len(concerts_queued) < int(os.environ['CONCERT_VOTE_OPTIONS_MAX']):
            print('!!! artist_visited2 !!!')
            print(artist_visited)
            print('!!! concerts_queued2 !!!')
            print(concerts_queued)
            artists = concert['artists']
            if os.environ['SHUFFLE_CONCERT_LIST'] == '1':
                random.shuffle(artists)
            # Second loop through concerts - get any concerts
            temp_artist_visited = []
            need_to_be_queued = True
            for artist in artists:
                if artist['name'].lower() not in artist_visited:
                    temp_artist_visited.append(artist['name'].lower())
                else:
                    need_to_be_queued = False
            if need_to_be_queued:
                for temp_artist in temp_artist_visited:
                    artist_visited.append(temp_artist)
                print("loop 2 adding {}".format(concert['event_name']))
                log.info(print("loop 2 adding {}".format(concert['event_name'])))
                concerts_queued.append(concert)
        else:
            break

    # Bring the users back to taste make when there is no concert at all.
    if len(concerts_queued) > 0:
        mark_queued_concerts(concerts_queued)
        publish_concert_list(event, concerts_queued)
        time.sleep(2.5)
        publish_voting_ui(event, concerts_queued, artist_visited)
        activate_voting_timer(event, artist_visited)
    else:
        event['intents']['current_intent'] = 'AskTaste'
        out_of_options(event)
        start_over(event)


def activate_voting_timer(event, artist_visited):
    event['intents']['timeout'] = os.environ['DEFAULT_VOTING_TIMEOUT']
    sns_event = {
        'slack': {
            'team_id': event['sessionAttributes']['team_id'],
            'channel_id': event['sessionAttributes']['channel_id'],
            'api_token': event['sessionAttributes']['api_token'],
            'bot_token': event['sessionAttributes']['bot_token']
        },
        'timeout': os.environ['DEFAULT_VOTING_TIMEOUT']
    }

    return sns.publish(
        TopicArn=os.environ['VOTING_TIMER_SNS_ARN'],
        Message=json.dumps({'default': json.dumps(sns_event)}),
        MessageStructure='json'
    )


def out_of_options(event):
    # print(response.history)
    text = 'Sorry, we couldn\'t find any concerts meeting your music taste. Let\'s try again.'
    sns_event = {
        'token': event['sessionAttributes']['bot_token'],
        'channel': event['sessionAttributes']['channel_id'],
        'text': text,
    }
    log.info('!!! OUT OF OPTIONS !!!')
    log.info(sns_event)
    return sns.publish(
        TopicArn=os.environ['POST_MESSAGE_SNS_ARN'],
        Message=json.dumps({'default': json.dumps(sns_event)}),
        MessageStructure='json'
    )


def start_over(event):
    print('!!! START OVER !!!')
    print(event)
    event['intents']['genres'] = []
    event['intents']['artists'] = []
    event['intents']['city'] = None
    event['intents']['tastes'] = {}
    # store_intents(event)

    sns_event = {
        'team': {
            'team_id': event['sessionAttributes']['team_id'],
            'access_token': event['sessionAttributes']['api_token'],
            'bot': {
                'bot_access_token': event['sessionAttributes']['bot_token']
            }
        },
        'slack': {
            'event': {
                'channel': event['sessionAttributes']['channel_id'],
                'user': event['intents']['host_id'],
                'text': 'THIS ASK TASTE INTENT SHOULD NOT BE INVOKED BY ANY UTTERANCES'
            }
        }
    }

    log.info('!!! START OVER !!!')
    log.info(sns_event)

    return sns.publish(
        TopicArn=os.environ['DISPATCH_ACTIONS_SNS_ARN'],
        Message=json.dumps({'default': json.dumps(sns_event)}),
        MessageStructure='json'
    )


def handler(event, context):
    log.info(json.dumps(event))
    event = json.loads(event['Records'][0]['Sns']['Message'])
    response = {
        "statusCode": 200,
        "body": json.dumps({"message": 'message has been sent successfully.'})
    }
    try:
        retrieve_intents(event)
        log.info(response)
        add_artist_tastes(event)
        add_genre_tastes(event)

        search_concerts(event)
        show_results(event)
        store_intents(event)
    except Exception as e:
        response = {
            "statusCode": 400,
            "body": json.dumps({"message": str(e)})
        }
        log.error(response)
    finally:
        return response
