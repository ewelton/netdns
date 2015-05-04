#!/usr/bin/env python3

from math import sqrt

def get_joiner(above,below,left,right):
    # http://xahlee.info/comp/unicode_drawing_shapes.html
    if above and below and left and right:
        return '┼'
    elif above and below and left:
        return '┤'
    elif above and below and right:
        return '├'
    elif above and below:
        return '│'
    elif above and left and right:
        return '┴'
    elif above and left:
        return '┘'
    elif above and right:
        return '└'
    elif below and left and right:
        return '┬'
    elif below and left:
        return '┐'
    elif below and right:
        return '┌'
    elif left or right:
        return '─'
    else:
        return ' '

class Grid:

    def __init__(self,height,width):
        self.height = height
        self.width = width
        self.data = [[None for _ in range(0,width)] for _ in range(0,height)]

    def set_region(self,row1,col1,row2,col2,value):
        for row in range(row1,row2+1):
            for col in range(col1,col2+1):
                self.data[row][col] = value

    def get_cell(self,row,col,dflt):
        if col >= 0 and col < self.width and row >= 0 and row < self.height:
            return self.data[row][col]
        else:
            return dflt

    def _draw_chars(self,row_size,col_size,chars):
        for row in range(-1,self.height):
            for col in range(-1,self.width):

                up_left = self.get_cell(row,col,'OUTSIDE')
                up_right = self.get_cell(row,col+1,'OUTSIDE')
                down_left = self.get_cell(row+1,col,'OUTSIDE')
                down_right = self.get_cell(row+1,col+1,'OUTSIDE')

                above = (up_left != up_right)
                below = (down_left != down_right)
                left = (up_left != down_left)
                right = (up_right != down_right)

                chars[(row+1)*row_size][(col+1)*col_size] = get_joiner(above,below,left,right)

                if left:
                    for c in range(col*col_size+1,(col+1)*col_size):
                        chars[(row+1)*row_size][c] = '─'

                if above:
                    for r in range(row*row_size+1,(row+1)*row_size):
                        chars[r][(col+1)*col_size] = '│'

    def _find_labels(self):
        labels = set()
        for row in range(0,self.height):
            for col in range(0,self.width):
                l = self.data[row][col]
                if l != ' ':
                    labels.add(l)
        return frozenset(labels)

    def _find_centers(self,row_size,col_size,labels):
        rmin = {}
        rmax = {}
        cmin = {}
        cmax = {}

        for row in range(0,self.height):
            for col in range(0,self.width):
                l = self.data[row][col]
                if l == ' ':
                    continue
                drow = row_size*row + 1
                dcol = col_size*col + 1
                rmin.setdefault(l,drow)
                rmax.setdefault(l,drow)
                cmin.setdefault(l,dcol)
                cmax.setdefault(l,dcol)
                rmin[l] = min(rmin[l],drow)
                rmax[l] = max(rmax[l],drow+row_size-2)
                cmin[l] = min(cmin[l],dcol)
                cmax[l] = max(cmax[l],dcol+col_size-2)

        rcenter = {}
        ccenter = {}
        for l in labels:
            rcenter[l] = (rmin[l] + rmax[l])/2
            ccenter[l] = (cmin[l] + cmax[l])/2

        return (rcenter,ccenter)

    def _draw_labels(self,row_size,col_size,chars,content):
        all_labels = self._find_labels()

        (rcenter,ccenter) = self._find_centers(row_size,col_size,all_labels)

        def find_first_occurrence(label):
            for r in range(0,self.height):
                for c in range(0,self.width):
                    if self.data[r][c] == label:
                        return (r,c)
            return None

        def find_closest():

            def distance(l,row,col):
                dr = abs(row - rcenter[l])
                dc = abs(col - ccenter[l])
                return sqrt(dr*dr + dc*dc)

            def maybe_add(l,drow,dcol):
                d = distance(l,drow,dcol)
                clo = theclosest.get(l)
                if clo == None or clo[0] > d:
                    theclosest[l] = (d,drow,dcol)

            theclosest = {}

            for row in range(0,self.height):
                for col in range(0,self.width):
                    l = self.data[row][col]
                    if l == ' ':
                        continue

                    drow = row*row_size + 1
                    dcol = col*col_size + 1

                    maybe_add(l,drow,dcol)

                    for r in range(drow,drow+row_size-1):
                        for c in range(dcol,dcol+col_size-1):
                            maybe_add(l,r,c)

                    if self.get_cell(row+1,col,'OUT') == l:
                        r = drow+row_size-1
                        for c in range(dcol,dcol+col_size-1):
                            maybe_add(l,r,c)

                    if self.get_cell(row,col+1,'OUT') == l:
                        c = dcol+col_size-1
                        for r in range(drow,drow+row_size-1):
                            maybe_add(l,r,c)

                    if (self.get_cell(row+1,col,'OUT') == l and
                        self.get_cell(row,col+1,'OUT') == l and
                        self.get_cell(row+1,col+1,'OUT') == l):
                        r = drow+row_size-1
                        c = dcol+col_size-1
                        maybe_add(l,r,c)
            return theclosest

        closest = find_closest()

        for label in sorted(all_labels):
            if content.get(label) == None:
                clo = closest[label]
                drow = clo[1]
                dcol = clo[2]
                chars[drow][dcol] = label
            else:
                text = content[label]
                location = find_first_occurrence(label)
                if location == None:
                    continue
                (row1,col1) = location
                row2 = row1
                col2 = col1
                while col2+1 < self.width and self.data[row2][col2+1] == label:
                    col2 += 1
                while row2+1 < self.height:
                    if all(self.data[row2+1][c] == label for c in range(col1,col2+1)):
                        row2 += 1
                    else:
                        break

                drow1 = row1*row_size+1
                dcol1 = col1*col_size+1

                drow2 = (row2+1)*row_size
                dcol2 = (col2+1)*col_size

                lines = text.split('\n')
                while len(lines) > 0 and lines[-1] == '':
                    lines = lines[:-1]
                text_height = len(lines)
                text_width = max(len(line) for line in lines)

                area_height = drow2 - drow1
                area_width = dcol2 - dcol1

                start_row = max(drow1,int((drow1 + drow2)/2 - text_height/2))
                start_col = max(dcol1,int((dcol1 + dcol2)/2 - text_width/2))

                for tr in range(0,text_height):
                    for tc in range(0,text_width):
                        if (start_row+tr < len(chars) and
                            start_col+tc < len(chars[0]) and
                            tc < len(lines[tr])):
                            chars[start_row+tr][start_col+tc] = lines[tr][tc]

    def render(self,row_size=2,col_size=4,content=None):

        if content == None:
            content = {}

        chars = [[' ' for _ in range(0,col_size*self.width+1)]
                 for _ in range(0,row_size*self.height+1)]
        self._draw_chars(row_size,col_size,chars)
        self._draw_labels(row_size,col_size,chars,content)

        lines = []
        for row in range(0,row_size*self.height+1):
            lines.append(''.join(chars[row]))
        return '\n'.join(lines)

    def print(self,row_size=2,col_size=4):
        print(self.render(row_size,col_size))

def grid_from_lines(lines):
    height = len(lines)
    width = max([len(l) for l in lines])
    g = Grid(height,width)
    for row in range(0,height):
        for col in range(0,width):
            if col < len(lines[row]):
                g.data[row][col] = lines[row][col]
            else:
                g.data[row][col] = ' '
    return g

if __name__ == '__main__':
    # g = Grid(4,4)
    # g.set_region(0,0,1,1,'a')
    # g.set_region(2,0,3,1,'b')
    # g.set_region(1,2,2,2,'c')
    # g.print(2,4)

    l = ["  aaa        ",
         "  aaaaa cccc ",
         "   aaaaaaacc ",
         "   abbbaaacc ",
         "   abbb  ccc ",
         "    bbb    c "]

    g = grid_from_lines(l)
    g.print(2,4)
