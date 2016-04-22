# Here is an attempt to write music to a MIDI file. We select a range of notes
# using the note_range function, then create a Pattern from that. The resulting
# .mid files are ...odd. There is a bug converting the tick numbers that doesn't
# quite work out.

import music
import midi

pattern_1 = music.midi_import('./midi/bwv529-1.mid')
pattern_2 = music.midi_import('./midi/bwv0541f.mid')

a = midi.Track()
b = midi.Track()
a.format = pattern_1.format
b.format = pattern_2.format
a.resolution = pattern_1.resolution
b.resolution = pattern_2.resolution

a.append(music.note_range(pattern_1, 692, 714))
b.append(music.note_range(pattern_2, 1073, 1092))

a[0].tick_relative = False
b[0].tick_relative = False

a[0].make_ticks_rel()
b[0].make_ticks_rel()

for event in b[0]:
    if (event.name == 'Note On') or (event.name == 'Note Off'):
        event.pitch += -6



midi.write_midifile("Pattern_A.mid", a)
midi.write_midifile("Pattern_B.mid", b)
