import sys
import copy
egg_path='./midi-0.2.3-py2.7.egg'
sys.path.append(egg_path)
import midi
from matplotlib import pyplot as plt

class Node(object):
    # Here is a node object that helps implement the tree structure in the
    # filter algorithm. It probably needs to be optimized, since initializing a
    # large array takes a long time.

    __slots__ = ('max_origin', 'max_bottom', 'max_score')
    def __init__(self):
        self.max_origin = []
        self.max_bottom = []
        self.max_score = 0

def all_runs(matrix, threshold = 10, quiet = True):
    # Returns a list containing dictionary events which contain information
    # about each run detected in a similarity matrix. Allows for filtering by a
    # threshold length (default 10). This function can take a long time to run,
    # so an optional 'quiet' parameter lets us keep track of the progress via
    # printed status messages.

    output = []

    # For each possible interval value (we could use 0 to 11, but this would
    # just detect the same run twice, but on different sides of the matrix),
    # find all of the runs matching that interval value, and for each run
    # determine the transposition.
    for n in range(7):
        if not quiet:
            print 'Finding runs in transposition ' + str(n) + '...'
        a, runs = identify_runs(matrix, n, 10)
        if not quiet:
            print str(len(runs)) + ' runs found.'
        for x in runs:

            # let a be the first point in the run. Reverse to [x,y] format.
            a = x[0][::-1]

            # if we are above the diagonal, then we need to transpose B down.
            # Otherwise, we need to transpose B up, but by the additive opposite
            # in mod 12.
            if a[0] <= a[1]:
                t = -1 * n
            else:
                t = (12 - n) % 12

            # Build a dict object to represent the run, should be fairly
            # intuitive. We are recording the length (number of notes) of the
            # run, the starting point, the ending point, and the distance and
            # direction we need to transpose B to match the two sections.
            output.append({ 'length': len(x), \
                            'beginning': a, \
                            'end': x[-1][::-1], \
                            'transposition': t})
    return output

def comparison_matrix(pattern_1, pattern_2):
    # Generates a pitch comparison matrix between pattern A and pattern B where
    # M[x][y] = (B[x] - A[y]) % 12

    # Extract the pitch values of the ordered 'Note On' events
    a = [x.data[0] for x in flatten(pattern_1) if x.name == 'Note On']
    b = [x.data[0] for x in flatten(pattern_2) if x.name == 'Note On']

    # Build a similarity grid by calculating the differences between each pair
    # of pitch values. Optimize this eventually by not using append method.
    matrix = []
    for x in b:
        new_line = []
        for y in a:
            new_line.append((x - y) % 12)
        matrix.append(new_line)
    return matrix

def find_intervals(m, search_interval, values):
    # This algorithm takes a similarity matrix and turns on or turns off matrix
    # elements according to whether they match a given interval. The ON and OFF
    # values are customizable via the 'values' input.
    #
    # Inputs: m = a comparison matrix
    #         search_interval = the desired interval to find and highlight
    #         values = [a, b] where a is the OFF value and b is the ON value

    #Copy the input matrix so we do not modify it.
    matrix = [[x for x in y] for y in m]

    #Optionally, reduce the search interval mod 12
    #search_interval = search_interval % 12

    # Perform the filtering
    for x in xrange(len(matrix)):
        for y in xrange(len(matrix[x])):
            if matrix[x][y] != search_interval:
                matrix[x][y] = values[0]
            else:
                matrix[x][y] = values[1]
    return matrix

def explore(pattern_1, pattern_2, interval=None):
    # This function allows

    # Generate a comparison matrix for the two patterns
    matrix = comparison_matrix(pattern_1, pattern_2)

    # If a particular interval has been selected, filter the grid using the
    # find_intervals function, and plot in black and white. Otherwise, plot in
    # dazzling technicolor.
    if interval != None:
        # Show black dots where the interval appears
        matrix = find_intervals(matrix, interval, [0, 255])
        # Plot in greyscale
        plt.imshow(matrix, cmap = 'Greys', interpolation='none')
    else:
        # Plot in color
        plt.imshow(matrix, interpolation='none')

    plt.show()

def flatten(pattern):
    # Takes a MIDI pattern (defined in the midi package) with multiple tracks
    # and returns a single track containing every event in the original pattern,
    # with absolute tick values instead of relative.

    # Copy the original pattern
    a = copy.copy(pattern)

    # Make the tick values absolute
    a.make_ticks_abs()

    # Make a new track, and append every event in every track of a.
    b = midi.Track()
    for track in a:
        for event in track:
            b.append(event)

    # Sort and output the result
    b.sort()
    return b

def identify_runs(matrix, n=0, threshold=10, plot = False):
    # Return both a filtered matrix, containing all runs of a given transpo-
    # sition value, and a list of runs, which are represented as lists of
    # points.

    # The allowable steps when creating a run, in +x, +y format. We can search
    # for only diagonal runs by setting steps = [[1, 1]], for example.
    steps = [[1, 1], [2, 2], [1, 2], [2, 1]]

    # Filter the matrix for the given interval.
    m = find_intervals(matrix, n, [0, 1])

    # Gonna be using these a lot.
    x_max = len(m)
    y_max = len(m[0])

    # p is an identically-sized array of Node objects, which will allow us
    # to define a tree structure.
    p = [[Node() for y in xrange(y_max)] for x in xrange(x_max)]

    # First, go through the matrix left to right, top to bottom. If we find a
    # black square, then for every allowable step, go a step in that direction
    # and see if we find another black square. If we do, then we test whether
    # this is the longest path to reach this square so far. If it is, then
    # give that square a new max_score, and record the max_origin for that
    # square as the one we just came from.
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

    # Go through the grid again, in the same direction. This time, if we find
    # a black square, call this [x, y] and use the Node array to step backward
    # through the longest path which reached [x, y]. Eventually, we will reach
    # a node [i, j] which has no max_origin, because it is the beginning of a
    # run. When this happens, test whether this is the longest path to reach
    # [i, j] so far. If it is, record [x, y] as the max_bottom of [i, j], and
    # record the path length as the max_score of [i, j].
    for x in xrange(x_max):
        for y in xrange(y_max):
            i = x
            j = y
            while p[i][j].max_origin != []:
                i, j = p[i][j].max_origin

            if p[i][j].max_score < p[x][y].max_score:
                p[i][j].max_score = p[x][y].max_score
                p[i][j].max_bottom = [x, y]

    # Finally, go through the grid again to collect all the filtered runs.
    # If you find a black dot which is a part of a run which is long enough,
    # (i.e. if p[x][y].max_score >= threshold), then walk backward through the
    # path until you reach the beginning. When you reach the beginning [i, j],
    # test whether the node you started at is the max_bottom of [i, j]. If it is
    # then you've found a complete run. Add it to the list. If not, then
    # there's yet another node downstream of [x, y].
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

    # Make a matrix of zeros and fill it in with all the runs we found
    matrix = [[0 for y in xrange(y_max)] for x in xrange(x_max)]
    for path in runs:
        for point in path:
            matrix[point[0]][point[1]] = 255

    # If we've recieved instructions to, plot the result.
    if plot:
        plt.imshow(matrix, cmap = 'Greys', interpolation='none')
        plt.show()

    # Return both the matrix, and the list of runs.
    return matrix, runs

def length(pattern):
    # Returns the number of 'Note On' events in a pattern.
    a = [x.data[0] for x in flatten(pattern) if x.name == 'Note On']
    return len(a)

def midi_import(file_name):
    # Just a wrapper for the midi.readfile() function, so that users don't have
    # to import the midi package themselves.

    return midi.read_midifile(file_name)

def note_range(pattern, a, b):
    # Attempts to build a new track, containing notes a through b (in chronolog-
    # ical order) of the original pattern.

    # Initialize things.
    p = flatten(pattern)
    output_track = midi.Track()

    # Count the number of 'Note On' events we have encountered as we go through
    # the list of all events.
    notes_passed = 0
    for i in range(len(p)):
        # If we find a Note On event, increment notes_passed. Now notes_passed
        # indicates the note number of the current note, so if the note number
        # is in the desired range, keep it.
        if (p[i].name == 'Note On'):
            notes_passed += 1
            if a <= notes_passed <= b:
                output_track.append(p[i])
                # Once we have decided to keep a note, we also have to turn it
                # off, so we go forward through the matrix until we find an
                # event which will cancel the current note.
                j = i
                pitch = p[i].data[0]
                while (p[j].name != 'Note Off') or (p[j].data[0] != pitch):
                    j += 1
                output_track.append(p[j])
        elif p[i].name == 'Note Off':
            pass
        else:
            # Keeps all non-note events.
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

def summarize_similarity(matrix, threshold = 10, quiet = False):
    # This is a function which is meant to give some insight into the similar
    # sections of two pieces. Input a similarity matrix, and a threshold, and
    # this function will:
    #       1. Find every run longer than the specified threshold
    #       2. Find the longest run matching each transposition value, and
    #          print some statistics on that run.
    #
    # We define a percent similarity score to be the number of notes contained
    # in the run divided by the number of possible notes in the run.

    if not quiet:
        print 'Summarizing similarity...'

    runs = all_runs(matrix, threshold, quiet)

    # For each possible transposition value, find the longest run matching that
    # value, and print statistics about it.
    for n in range(-12, 12):
        l = [x for x in runs if x['transposition'] == n]

        # If we found any runs, select the longest one.
        if len(l) > 0:
            arg_max = max(l, key=lambda x: x['length'])

            # K is either the x-distance of the run, or the y-distance. Which-
            # ever is longer.
            k = max( arg_max['end'][0] - arg_max['beginning'][0], \
                     arg_max['end'][1] - arg_max['beginning'][1])

            # Define percent similarity as the number of notes in the sequence
            # as a fraction of k. Separately in this project, if we had defined
            # k using min instead of the max, then this percentage would calcu-
            # late the density of the run instead.
            percent_similarity = 100 * float(arg_max['length'])/float(k)

            # Print a summary of the run.
            print 'A %i to %i vs. B %i to %i: %i notes (%l percent similar), transposed %i' \
                    % (arg_max['beginning'][0], \
                       arg_max['end'][0], \
                       arg_max['beginning'][1], \
                       arg_max['end'][1], \
                       arg_max['length'], \
                       percent_similarity, \
                       arg_max['transposition'])
