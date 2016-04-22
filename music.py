import sys
egg_path='./midi-0.2.3-py2.7.egg'
sys.path.append(egg_path)
import midi
from matplotlib import pyplot as plt

class Node(object):
    __slots__ = ('max_origin', 'max_bottom', 'max_score')
    def __init__(self):
        self.max_origin = []
        self.max_bottom = []
        self.max_score = 0
    #def __str__(self):
    #   return '\nmax_origin ' + str(self.max_origin) + \
    #          '\nmax_bottom ' + str(self.max_bottom) + \
    #          '\nmax_score  ' + str(self.max_score)

def find_intervals(m, search_interval, values):
    matrix = [[x for x in y] for y in m]
    #search_interval = search_interval % 12
    for x in xrange(len(matrix)):
        for y in xrange(len(matrix[x])):
            if matrix[x][y] != search_interval:
                matrix[x][y] = values[0]
            else:
                matrix[x][y] = values[1]
    return matrix

def flatten(pattern):
    a = pattern
    a.make_ticks_abs()

    b = midi.Track()
    for track in a:
        for event in track:
            b.append(event)

    b.sort()
    return b

def comparison_matrix(pattern_1, pattern_2):
    # Extract the pitch values of the ordered note on events
    a = [x.data[0] for x in flatten(pattern_1) if x.name == 'Note On']
    b = [x.data[0] for x in flatten(pattern_2) if x.name == 'Note On']

    # Build a similarity grid
    matrix = []
    for x in b:
        new_line = []
        for y in a:
            new_line.append((x - y) % 12)
        matrix.append(new_line)
    return matrix

def explore(pattern_1, pattern_2, interval=None):
    # Generate a comparison matrix for the two patterns
    matrix = comparison_matrix(pattern_1, pattern_2)

    if interval != None:
        # Show black dots where the interval appears
        matrix = find_intervals(matrix, interval, [0, 255])
        # Plot in greyscale
        plt.imshow(matrix, cmap = 'Greys', interpolation='none')
    else:
        # Plot in color
        plt.imshow(matrix, interpolation='none')

    plt.show()

def midi_import(file_name):
    return midi.read_midifile(file_name)

def length(pattern):
    a = [x.data[0] for x in flatten(pattern) if x.name == 'Note On']
    return len(a)

def all_runs(matrix, threshold = 10):
    output = []

    for n in range(7):
        print 'Finding runs in transposition ' + str(n) + '...'
        a, runs = identify_runs(matrix, n, 10)
        print str(len(runs)) + ' runs found.'
        for x in runs:
            a = x[0][::-1]
            if a[0] <= a[1]:
                t = -1 * n
            else:
                t = (12 - n) % 12

            output.append({ 'length': len(x), \
                            'beginning': a, \
                            'end': x[-1][::-1], \
                            'transposition': t})
    return output

def summarize_similarity(matrix, threshold = 10):
    print 'Summarizing similarity...'
    runs = all_runs(matrix, threshold)
    print max([x['length'] for x in runs])
    for n in range(-12, 12):
        l = [x for x in runs if x['transposition'] == n]
        max_len = 0
        arg_max = None
        for x in l:
            if x['length'] > max_len:
                arg_max = x
                max_len = arg_max['length']
        if arg_max != None:
            k = max( arg_max['end'][0] - arg_max['beginning'][0], \
                     arg_max['end'][1] - arg_max['beginning'][1])
            percent_similarity = 100 * float(arg_max['length'])/float(k)
            print 'Track A %i to %i and Track B %i to %i: %i notes (%l percent similar), transposed %i' \
                    % (arg_max['beginning'][0], \
                       arg_max['end'][0], \
                       arg_max['beginning'][1], \
                       arg_max['end'][1], \
                       arg_max['length'], \
                       percent_similarity, \
                       arg_max['transposition'])

def note_range(pattern, a, b):
    pattern.make_ticks_abs()
    output_track = midi.Track()

    p = flatten(pattern)
    notes_passed = 0
    for i in range(len(p)):
        if (p[i].name == 'Note On'):
            notes_passed += 1
            if a <= notes_passed <= b:
                output_track.append(p[i])
                j = i
                pitch = p[i].data[0]
                while (p[j].name != 'Note Off') or (p[j].data[0] != pitch):
                    j += 1
                output_track.append(p[j])
        elif p[i].name == 'Note Off':
            pass
        else:
            output_track.append(p[i])
    output_track.sort()

    return output_track

def similarity_score(matrix, threshold = 10):
    total_dots = 0.0

    runs = all_runs(matrix, threshold)
    runs = sorted(runs, key=lambda x: x['length'])

    y = len(matrix)
    x = len(matrix[0])

    y_available = [True for i in xrange(y)]
    x_available = [True for j in xrange(x)]

    for r in runs:
        m, n = r['beginning']
        o, p = r['end']

        if x_available[m] and x_available[o] and y_available[n] and y_available[p]:
            total_dots += r['length']

            for c in xrange(n, p):
                y_available[c] = False

            for d in xrange(m, o):
                x_available[d] = False

    print total_dots
    print x, y
    return total_dots / float(max(x, y))



def identify_runs(matrix, n=0, threshold=10, plot = False):
    steps = [[1, 1], [2, 2], [3, 3], [1, 2], [2, 1], [3, 1], [1, 3]]

    m = find_intervals(matrix, n, [0, 1])

    x_max = len(m)
    y_max = len(m[0])

    p = [[Node() for y in xrange(y_max)] for x in xrange(x_max)]

    for x in xrange(x_max):
        for y in xrange(y_max):
            if m[x][y] == 1:
                for step in steps:
                    i = x + step[0]
                    j = y + step[1]
                    if (i < x_max) & (j < y_max):
                        if m[i][j] == 1:
                            if p[i][j].max_score < p[x][y].max_score + 1:
                                p[i][j].max_score = p[x][y].max_score + 1
                                p[i][j].max_origin = [x, y]

    for x in xrange(x_max):
        for y in xrange(y_max):
            i = x
            j = y
            path = []
            while p[i][j].max_origin != []:
                i, j = p[i][j].max_origin

            if p[i][j].max_score < p[x][y].max_score:
                p[i][j].max_score = p[x][y].max_score
                p[i][j].max_bottom = [x, y]

    runs = []
    for x in xrange(x_max):
        for y in xrange(y_max):
            i = x
            j = y
            if p[x][y].max_score >= threshold:
                path = [[i, j]]
                while p[i][j].max_origin != []:
                    path.append(p[i][j].max_origin)
                    i, j = p[i][j].max_origin

                if p[i][j].max_bottom == [x, y]:
                    runs.append(path[::-1])

    matrix = [[0 for y in xrange(y_max)] for x in xrange(x_max)]

    for path in runs:
        for point in path:
            matrix[point[0]][point[1]] = 255

    #runs = [[x[::-1] for x in y] for y in runs]

    if plot:
        plt.imshow(matrix, cmap = 'Greys', interpolation='none')
        plt.show()

    return matrix, runs
