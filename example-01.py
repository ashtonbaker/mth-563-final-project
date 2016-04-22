# Try exploring a similarity matrix between two pieces.

import music
import midi

pattern_1 = music.midi_import('./midi/bwv529-1.mid')
pattern_2 = music.midi_import('./midi/bwv0541f.mid')

music.explore(pattern_1, pattern_2, 0)
