
# This script takes mp3 songs downloaded from YouTube, then applies
# various regex rules to rename the files, updates metadata, and
# adjusts the volume to be similar for all songs.

from shutil import copyfile
from os import listdir, mkdir
from os.path import isfile, join, isdir, exists
import re
from tqdm import tqdm
import eyed3
from logging import getLogger
from pydub import AudioSegment # dependent on having ffmpeg
from pydub.utils import mediainfo

src_dir = r'C:\Users\hobbs\Music\YouTube'
dest_dir = r'C:\Users\hobbs\Music\YouTube-processed'
target_dBFS = -13 # target volume

getLogger().setLevel('ERROR') # suppress warnings

if not isdir(dest_dir):
    mkdir(dest_dir)

# transform a file name
patterns = ['yt5s.com - ', 'yt\ds.io - ', 'y2meta.com - ', 'X2Download.com\s+-', \
    'X2Download.app - ', 'Y2mate.mx - ', 'x2mate.com - ', 'video _ ', 
    'official version', 'official', 'with lyrics', 'lyrics', 'Letra', 'audio', ' HQ', \
    ' HD', '\(.*\)', '\[.*\]', '\{.*\}', '\+', '」', '「', '^\s*-\s*', '🎵', '^\d+\.']
def transform(f):
    for p in patterns:
        f = re.sub(p, '', f, flags=re.IGNORECASE)
    f = re.sub('\s+\.mp3$', '.mp3', f) # remove trailing whitespace before .mp3
    f = re.sub('\s*-\.mp3$', '.mp3', f) # remove trailing dashes before .mp3
    f = re.sub('\s+', ' ', f) # remove repeated whitespace
    return f.strip()

# change volume of sound
def match_target_amplitude(sound, target_dBFS, threhsold=0):
    change_in_dBFS = target_dBFS - sound.dBFS
    if abs(change_in_dBFS) < threhsold:
        return sound
    return sound.apply_gain(change_in_dBFS)


if __name__ == '__main__':

    # copy mp3s to dest_dir with transformed file names (and title metadata)
    mp3s = [f for f in listdir(src_dir) if isfile(join(src_dir, f)) and f.lower().endswith('.mp3')]
    for f in tqdm(mp3s):
        # copy file
        output_name = transform(f)
        src = join(src_dir, f)
        dest = join(dest_dir, output_name)
        copyfile(src, dest)
        # update title metadata
        file_obj = eyed3.load(dest)
        if file_obj.tag.title is None:
            file_obj.tag.title = output_name[:-4] # drop the ".mp3"
        else:
            file_obj.tag.title = transform(file_obj.tag.title)
        # if title is too short, then use file name
        if file_obj.tag.title is None or len(file_obj.tag.title) < 4:
            file_obj.tag.title = output_name[:-4] # drop the ".mp3"
        file_obj.tag.save(dest)

    # adjust volumes of songs in dest folder
    mp3s = [f for f in listdir(dest_dir) if isfile(join(dest_dir, f)) and f.lower().endswith('.mp3')]
    for f in tqdm(mp3s):
        song_path = join(dest_dir, f)
        try:
            original_bitrate = mediainfo(song_path)['bit_rate']
            song = AudioSegment.from_file(song_path, "mp3")
            adjusted_song = match_target_amplitude(song, target_dBFS, 0)
            adjusted_song.export(song_path, format="mp3", bitrate=original_bitrate)
        except:
            print(f)

