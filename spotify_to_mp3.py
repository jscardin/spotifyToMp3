# Downloads a Spotify playlist into a folder of MP3 tracks
# Jason Chen, 21 June 2020

import os
import spotipy
import spotipy.oauth2 as oauth2
import youtube_dl
from youtube_search import YoutubeSearch
from fuzzywuzzy import fuzz

import glob
import shutil

mp3_path='/media/jscardin/C0BA-D6E9/'



# **************PLEASE READ THE README.md FOR USE INSTRUCTIONS**************

def generate_token(client_id: str, client_secret: str):
    credentials = oauth2.SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    token = credentials.get_access_token()
    #token = credentials.get_cached_token()
    return token


def write_tracks(text_file: str, tracks: dict):
    # Writes the information of all tracks in the playlist to a text file. 
    # This includins the name, artist, and spotify URL. Each is delimited by a comma.
    with open(text_file, 'w+', encoding='utf-8') as file_out:
        while True:
            for item in tracks['items']:
                if 'track' in item:
                    track = item['track']
                else:
                    track = item
                try:
                    track_url = track['external_urls']['spotify']
                    track_name = track['name']
                    track_artist = track['artists'][0]['name']
                    csv_line = track_name + "," + track_artist + "," + track_url + "\n"
                    try:
                        file_out.write(csv_line)
                    except UnicodeEncodeError:  # Most likely caused by non-English song names
                        print("Track named {} failed due to an encoding error. This is \
                            most likely due to this song having a non-English name.".format(track_name))
                except KeyError:
                    print(u'Skipping track {0} by {1} (local only?)'.format(
                            track['name'], track['artists'][0]['name']))
            # 1 page = 50 results, check if there are more pages
            if tracks['next']:
                tracks = spotify.next(tracks)
            else:
                break


def write_playlist(username: str, playlist_id: str):
    global tracks
    results = spotify.user_playlist(username, playlist_id, fields='tracks,next,name')
    playlist_name = results['name']
    text_file = u'{0}.txt'.format(playlist_name, ok='-_()[]{}')
    print(u'Writing {0} tracks to {1}.'.format(results['tracks']['total'], text_file))
    tracks = results['tracks']
    write_tracks(text_file, tracks)
    return playlist_name


def find_and_download_songs(reference_file: str):
    global best_url,results_list,text_to_search,dir_content
    dir_content=os.listdir(mp3_path)
    TOTAL_ATTEMPTS = 10
    with open(reference_file, "r", encoding='utf-8') as file:
        for line in file:
            temp = line.split(",")
            name, artist = temp[0], temp[1]
            # if any([fuzz.ratio(artist+" "+name,a)>20 for a in dir_content]): 
            text_to_search = artist + " - " + name
            text_to_search=text_to_search.replace('/','-')
            a=[a[0] for a in enumerate(dir_content) if text_to_search in a[1]]
            if len(a):
                print("SKIP: ",text_to_search)
                dir_content.pop(a[0])
                continue
            print('text_to_search')
            best_url = None
            attempts_left = TOTAL_ATTEMPTS
            while attempts_left > 0:
                try:
                    results_list = YoutubeSearch(text_to_search, max_results=1).to_dict()
                    a=results_list
                    best_url = "https://www.youtube.com{}".format(results_list[0]['url_suffix'])
                    break
                except IndexError:
                    attempts_left -= 1
                    print("No valid URLs found for {}, trying again ({} attempts left).".format(
                        text_to_search, attempts_left))
            if best_url is None:
                print("No valid URLs found for {}, skipping track.".format(text_to_search))
                continue
            # Run you-get to fetch and download the link's audio
            print("DL:   ",format(text_to_search))
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }
            
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([best_url])
            list_of_files = glob.glob('*') # * means all if need specific format then *.csv
            latest_file = max(list_of_files, key=os.path.getctime)
            os.rename(latest_file,text_to_search+'.mp3')
            shutil.copy(text_to_search+'.mp3',mp3_path+text_to_search+'.mp3')
    for file in dir_content:
        print('REMOVING: ',file)
        os.remove(mp3_path+file)
            
            
if __name__ == "__main__":
    # Parameters
    
    #https://open.spotify.com/playlist/0hCOjcbWg33xXRk2RnIFc9?si=3eaed9adf09d4860
    client_id = "ad21eeb11e544e049cc4f18b809a5407" #input("Client ID: ")
    client_secret = "0e3d25a97777486693f26a48d954ddb1" #input("Client secret: ")
    username = "9uftjfidtv074b3yj6oebs4ez"  #input("Spotify username: ")
    playlist_uri = "0hCOjcbWg33xXRk2RnIFc9?si=3eaed9adf09d4860" #   input("Playlist URI (excluding \"spotify:playlist:\"): ")
    token = generate_token(client_id, client_secret)
    spotify = spotipy.Spotify(auth=token['access_token'])
    playlist_name = write_playlist(username, playlist_uri)
    reference_file = "{}.txt".format(playlist_name)
    # Create the playlist folder
    if not os.path.exists(playlist_name):
        os.makedirs(playlist_name)
    os.rename(reference_file, playlist_name + "/" + reference_file)
    os.chdir(playlist_name)
    find_and_download_songs(reference_file)
    print("Operation complete.")
