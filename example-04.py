import os
import music

files = os.listdir('./midi')

for a in files:
    for b in files:
        if a == b:
            break

        pattern_1 = music.midi_import('./midi/' + a)
        pattern_2 = music.midi_import('./midi/' + b)
        print a, b, music.similarity_score(music.comparison_matrix(pattern_1, pattern_2), 10)
