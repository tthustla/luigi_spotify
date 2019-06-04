import luigi
from luigi.contrib.s3 import S3Target, S3Client
import spotipy
import spotipy.util as util
import csv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import date
from time import strftime

class spotify_cred(luigi.Config):
    user = luigi.Parameter()
    id = luigi.Parameter()
    secret = luigi.Parameter()

class gmail(luigi.Config):
    id = luigi.Parameter()
    password = luigi.Parameter()


spotify_user = spotify_cred().user
spotify_id = spotify_cred().id
spotify_secret = spotify_cred().secret

token = util.prompt_for_user_token(spotify_user, 
                                   scope='playlist-read-private', 
                                   client_id=spotify_id, 
                                   client_secret=spotify_secret,
                                  redirect_uri='https://localhost:8080')


if token:
    sp = spotipy.Spotify(auth=token)


 
class GetWeeklyTracks(luigi.Task):
 
    def requires(self):
        return []
 
    def output(self):
        client = S3Client()
        return S3Target('s3://luigi-spotify/{}/weekly_tracks.tsv'.format(strftime("%Y-%m-%d")), client=client)
 
    def run(self):
        with self.output().open('w') as f:
            fnames = ["Track ID", "Track Name","Track URL","Album ID","Album Name","Artist ID","Artist Name"]
            writer = csv.DictWriter(f, fieldnames=fnames, delimiter='\t')
            writer.writeheader()
            results = sp.current_user_playlists()
            for i in results['items']:
                if i['name'] == 'Discover Weekly':
                    tracks = sp.user_playlist_tracks(spotify_user, playlist_id=i['id'])
                    for t in tracks['items']:
                        track_id = t['track']['id']
                        track_name = t['track']['name']
                        track_url = t['track']['external_urls']['spotify']
                        album_id = t['track']['album']['id']
                        album_name = t['track']['album']['name']
                        artist_id = t['track']['artists'][0]['id']
                        artist_name = t['track']['artists'][0]['name']
                        writer.writerow({"Track ID":track_id, "Track Name":track_name,"Track URL":track_url,
                                         "Album ID":album_id,"Album Name":album_name,
                                         "Artist ID":artist_id,"Artist Name":artist_name})



class SendWeeklyEmail(luigi.Task):
 
    def requires(self):
        return [GetWeeklyTracks()]
 
    def output(self):
        client = S3Client()
        return S3Target('s3://luigi-spotify/{}/email_sent_status.txt'.format(strftime("%Y-%m-%d")), client=client)
 
    def run(self):
        email = gmail().id
        password = gmail().password
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Discover Weekly {}".format(str(date.today()))
        msg['From'] = email
        msg['To'] = email
        html = """
                <html>
                  <head></head>
                  <body>
                """
        with self.input()[0].open() as csv_file:
            csv_reader = csv.reader(csv_file, delimiter='\t')
            line_count = 0
            for row in csv_reader:
                if line_count == 0:
                    line_count += 1
                else:
                    track_info = f'{row[1]} - {row[6]}'
                    track_link = f'{row[2]}'

                    html += '<p><a href="{}">{}</a></p>'.format(track_link,track_info)
        html += "</body></html>"
        msg.attach(MIMEText(html, 'html'))
        with self.output().open('w') as fout:
            try:
                mail = smtplib.SMTP('smtp.gmail.com', 587)
                mail.ehlo()
                mail.starttls()
                mail.ehlo()
                mail.login(email, password)
                mail.sendmail(email, email, msg.as_string())
                fout.write("email sent successfully")
            except Exception as e:
                fout.write(str(e))
            finally:
                mail.quit() 

 
                 
if __name__ == '__main__':
    luigi.run()
