import re
from robobrowser import RoboBrowser
from getpass import getpass
import subprocess
import os

class AoDDownloader:

    def __init__(self):
        self.browser = RoboBrowser(parser='html.parser',history=True)
        self.baseurl = 'https://anime-on-demand.de'
        self.__username = ''
        self.__password = ''

    def login(self):
        self.browser.open(self.baseurl + '/users/sign_in')
        form = self.browser.get_form(action='/users/sign_in')
        if not self.__username:
            username = input('Username: ')
        else:
            username = self.__username
        if not self.__password:
            password = getpass()
        else:
            password = self.__password
        form['user[login]'].value = username
        form['user[password]'].value = password

        self.browser.submit_form(form)
        # TODO
        # Test, ob Login funktionierte

    def get_all_animes(self):
        self.browser.open(self.baseurl + '/animes')

        all_anime = []
        all_boxes = self.browser.find_all(class_='animebox')
        for box in all_boxes:
            all_anime.append({'title':box.div.h3.string,'link':box.div.find(class_='animebox-link').a['href'],'movie':('film' in box.div.find(class_='animebox-link').a.string.lower())})

        return all_anime

    def get_all_episodes(self, sublink: str, isMovie: bool):
        self.browser.open(self.baseurl + sublink)

        if isMovie:
            title = ''.join(list(self.browser.find('h1',{'itemprop':'name'}).stripped_strings))
            return [{
                'title': title,
                'playlist_sub': self.browser.find(attrs={'data-lang':'jap'},class_='streamstarter_html5')['data-playlist'],
                'playlist_dub': self.browser.find(attrs={'data-lang':'ger'},class_='streamstarter_html5')['data-playlist']
            }]
        else:
            all_episodes = []
            all_boxes = self.browser.find_all(class_='episodebox')
            for box in all_boxes:
                title = list(map(lambda x: str(x), box.find(class_='episodebox-title').contents))
                title = (' '.join(title)).replace('<br/>','-')
                playlist_sub = box.find(attrs={'data-lang':'jap'},class_='streamstarter_html5')
                if playlist_sub:
                    playlist_sub = playlist_sub['data-playlist']
                playlist_dub = box.find(attrs={'data-lang':'ger'},class_='streamstarter_html5')
                if playlist_dub:
                    playlist_dub = playlist_dub['data-playlist']

                all_episodes.append({'title':title,'playlist_sub':playlist_sub,'playlist_dub':playlist_dub})
                    
            return all_episodes
    
    def get_movie_streams(self, sublink: str):
        self.browser.open(self.baseurl + sublink)

    def get_single_episode_playlists(self, playlist_link):
        return self._get_all_episode_playlist(playlist_link)['playlist'][0]['sources'][0]['file']
    
    def get_multi_episodes_playlists(self, playlist_link, e_range):
        all_file_links = self._get_all_episode_playlist(playlist_link)['playlist'][0:e_range+1]
        return list(map(lambda x: x['sources'][0]['file'], all_file_links))
    
    def _get_all_episode_playlist(self, playlist_link):
        headers = {
            'accept': 'application/json',
            'x-requested-with': 'XMLHttpRequest',
        }

        self.browser.open(self.baseurl + playlist_link, headers=headers)
        return self.browser.response.json()
    
    def download_episode(self, playlist: str, title: str, usesDub: bool = False, dir_name: str = ''):
        title = title.replace('ä','ae').replace('ö','oe').replace('ü','ue').replace('ß','ss').replace('Ä','Ae').replace('Ö','Oe').replace('Ü','Ue')
        title = re.sub(r'[^a-zA-Z0-9 \-_\(\)&\.]','',title)
        if usesDub:
            title += ' - Dub'
        else:
            title += ' - Sub'
        print('Starte: ' + title + '...')
        subprocess.run(['ffmpeg','-i',playlist,'-c','copy','-loglevel','warning',dir_name+title+'.mp4'],stderr=subprocess.STDOUT)
        print('Fertig: ' + title + '!')

def get_anime_input():    
    i = 0
    a_list = aod.get_all_animes()
    if not a_list:
        return False
    for entry in a_list:
        if entry['movie']:
            print(str(i) + ':\t' + entry['title'] + ' (Film)')
        else:
            print(str(i) + ':\t' + entry['title'])
        i+=1
    a_idx = input('Wähle einen Anime zum Download: ')
    while not re.match('^[0-9][0-9]*$',a_idx) or int(a_idx) < 0 or int(a_idx) >= i:
        print('Gibt bitte eine Zahl, die vor einem Anime steht, ein!')
        print('(Strg+C beendet das Programm)')        
        a_idx = input('Wähle einen Anime zum Download: ')
    print()
    print('Ausgewählt: ' + a_list[int(a_idx)]['title'])
    print()
    return a_list[int(a_idx)]

def get_episode_list(animePayload: dict):
    return aod.get_all_episodes(animePayload['link'],animePayload['movie'])

def get_movie_input(e_list: list):
    print()
    if not e_list[0]['playlist_sub']:
        print('Nur dub vorhanden!')
        e_dub = True    
    elif e_list[0]['playlist_dub']:
        e_lang = input('Dub? (y/N): ')
        if e_lang == 'y':
            print('Wenn möglich wird Dub genutzt!')
            e_dub = True
        else:
            e_dub = False
    return e_dub

def get_episodes_input(e_list: list):
    print()
    i = 1
    for entry in e_list:
        print(str(i) + ':\t' + entry['title'])
        i+=1
    i-=1
    print()
    print('Wähle Episoden aus!')
    print('h für Hilfe')
    print()
    e_select = input('Treffe deine Auswahl: ')
    while e_select == 'h' or (not re.match('^[0-9][0-9]*-[0-9][0-9]*$',e_select) and not re.match('^[0-9][0-9]*-$',e_select) and not re.match('^-[0-9][0-9]*$',e_select) and not re.match('^[0-9]*$',e_select) and not e_select == 'a'):
        print()
        print('Wähle Episoden aus!')
        print('h für Hilfe')
        print()
        if(e_select == 'h'):
            print('(n und m sind Nummern)')
            print('n:\tEpisode n runterladen')
            print('n-m:\tEpisoden n bis m runterladen')
            print('n-:\tAlles ab Episode n runterladen')
            print('-m:\tAlles bis Episode m runterladen')
            print('"a":\tAlles runterladen')
            print()
        e_select = input('Treffe deine Auswahl: ')
    if re.match('^[0-9][0-9]*-[0-9][0-9]*$',e_select):
        e_split = e_select.split('-')
        if int(e_split[1]) < int(e_split[0]):
            e_split[0], e_split[1] = e_split[1], e_split[0]
        if int(e_split[0]) < 1 and int(e_split[1]) < 1 or int(e_split[0]) > i and int(e_split[1]) > i:
            print('Keine gültige Eingabe, breche ab.')
            exit()
        if int(e_split[0]) < 1:
            print('Untere Grenze zu tief, nutze 1.')
            e_split[0] = '1'
        if int(e_split[1]) > i:
            print('Obere Grenze zu hoch, nutze ' + str(i) + '.')
            e_split[1] = str(i)
        if int(e_split[0]) == int(e_split[1]):
            e_select = e_split[0]
        else:
            e_select = '-'.join(e_split)
    elif re.match('^[0-9][0-9]*-$',e_select):
        e_split = e_select.split('-')
        if int(e_split[0]) < 1:
            print('Untere Grenze zu tief, nutze 1.')
            e_split[0] = '1'
        elif int(e_split[0]) > i:
            print('Keine gültige Eingabe, breche ab.')
            exit()
        if int(e_split[0]) == i:
            e_select = e_split[0]
        else:
            e_select = e_split[0] + '-' + str(i)
            e_select = '-'.join(e_split)
    elif re.match('^-[0-9][0-9]*$',e_select):
        e_split = e_select.split('-')
        if int(e_split[1]) > i:
            print('Obere Grenze zu hoch, nutze ' + str(i) + '.')
            e_split[1] = str(i)
        elif int(e_split[1]) < 1:
            print('Keine gültige Eingabe, breche ab.')
            exit()
        if int(e_split[1]) == 1:
            e_select = '1'
        else:
            e_select = '1-' + e_split[1]
    elif e_select == 'a':
        e_select = '1-' + str(i)
    
    if not e_list[0]['playlist_sub']:
        print('Nur dub vorhanden!')
        e_dub = True    
    elif e_list[0]['playlist_dub']:
        e_lang = input('Dub? (y/N): ')
        if e_lang == 'y':
            print('Wenn möglich wird Dub genutzt!')
            e_dub = True
        else:
            e_dub = False
    else:
        e_dub = False
    return e_select, e_dub

def download_episodes(e_list: list, e_select: str, useDub: bool, dir_name: str = ''):
    if re.match('^[0-9][0-9]*-[0-9][0-9]*$',e_select):
        print('Das wird eine ganze Weile brauchen... Pack das Programm einfach in den Hintergrund!')
        e_split = e_select.split('-')
        e_split = list(map(lambda x: int(x), e_split))
        i = -1
        if useDub:
            for file_link in aod.get_multi_episodes_playlists(e_list[e_split[0]]['playlist_dub'], e_split[1]-e_split[0]):
                aod.download_episode(file_link, e_list[e_split[0]+i]['title'],useDub,dir_name)
                i+=1
            return
        else:
            for file_link in aod.get_multi_episodes_playlists(e_list[e_split[0]]['playlist_sub'], e_split[1]-e_split[0]):
                aod.download_episode(file_link, e_list[e_split[0]+i]['title'],useDub,dir_name)
                i+=1
            return
    else:
        if useDub:
            file_link = aod.get_single_episode_playlists(e_list[int(e_select)-1]['playlist_dub'])
        else:
            file_link = aod.get_single_episode_playlists(e_list[int(e_select)-1]['playlist_sub'])
        aod.download_episode(file_link, e_list[int(e_select)-1]['title'],useDub,dir_name)

def run():
    anime = get_anime_input()
    if not anime:
        print('Konnte keine Anime finden. Entweder AoD hat etwas geändert, oder das Programm ist kaputt.')
        return
    e_list = get_episode_list(anime)
    if not e_list:
        print('Konnte keine Episoden finden. Entweder es gibt keine, oder das Programm ist kaputt.')
        return
    if anime['movie']:
        print()
        print('Dies ist ein Film!')
        useDub = get_movie_input(e_list)
        download_episodes(e_list,'1',useDub)
    else:
        e_select, useDub = get_episodes_input(e_list)
        dir_name = re.sub(r'[^a-zA-Z0-9 \-_\(\)&\.]','',anime['title'])
        try:
            os.mkdir(dir_name)
            download_episodes(e_list, e_select, useDub, dir_name+'/')
        except FileExistsError:
            download_episodes(e_list, e_select, useDub, dir_name+'/')
        except PermissionError:
            print('Kann keinen Ordner erstellen. Prüfe bitte deine Berechtigungen.')
            download_episodes(e_list, e_select, useDub)
    
aod = AoDDownloader()
aod.login()
run()

while input('Weiter? (y/N): ')[:1] == 'y':
    run()
