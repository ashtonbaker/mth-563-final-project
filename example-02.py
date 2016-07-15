# Get a summary of the similarities between two pieces of music. This will
# be a great place to start if investigating the structural similarities
# between two pieces, because it give explicit note numbers

import music
pattern_1 = music.midi_import('./midi/bwv529-1.mid')
pattern_2 = music.midi_import('./midi/bwv0541f.mid')
x = music.comparison_matrix(pattern_1, pattern_2)
music.summarize_similarity(x, 10)
