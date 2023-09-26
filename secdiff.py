#!/usr/bin/env python3

"""
Section-by-section interactive diff tool using Python's curses.

Input:
    A file with some number of sections that have lines delimiting the sections.

Usage:
    secdiff.py [-h] -s SEPARATOR filename

    Provide a separator marker with '-s' and the file to diff the sections of.

Keybindings:
    l/h: Go to the next/prev pair of sections to diff.
    j/k: Scroll down/up in the current diff.

"""

import argparse
import curses
import re
import sys
from difflib import Differ


def exit(scr):
    """
    Exit from scr
    """
    curses.nocbreak()
    scr.keypad(False)
    curses.echo()
    curses.endwin()


def split_text(text, separator):
    """
    Use any lines starting with the separator to split the text
    into a list of sections, where each section is a list of lines
    """
    lines = text.splitlines()
    sections = []
    section = []
    title = ""
    for line in lines:
        if line.startswith(separator):
            if len(section) != 0:
                sections.append((title, section))
            title = line
            section = []
        else:
            section.append(line)
    sections.append((title, section))
    return sections


class State:
    """
    Hold the state to be displayed on the screen.
    """

    def __init__(self, fulltext, separator):
        self.sections = split_text(fulltext, separator)
        if len(self.sections) < 2:
            exit(scr)
            print("Failed to find at least 2 sections", file=sys.stderr)
            return
        self.top = 0
        self.left = 0
        self.right = 1

    def section_text(self, i):
        """Get the lines for section i"""
        return self.sections[i][1]

    def max_top(self):
        """Maximum scroll offset"""
        return (
            max(len(self.section_text(self.left)), len(self.section_text(self.right)))
            - 1
        )

    def clamp_top(self):
        """Clamp the scroll offset ('top') to the maximum"""
        self.top = min(self.top, self.max_top())

    def next(self):
        """Go to the next pair of sections"""
        if self.right < len(self.sections) - 1:
            self.left += 1
            self.right += 1
        self.clamp_top()

    def prev(self):
        """Go to the prev pair of sections"""
        if self.left > 0:
            self.left -= 1
            self.right -= 1
        self.clamp_top()

    def down(self):
        """Scroll down if possible"""
        if self.top < self.max_top():
            self.top += 1

    def up(self):
        """Scroll up if possible"""
        if self.top > 0:
            self.top -= 1

    def make_diff(self):
        """
        Compute a simple side-by-side diff using the difflib Differ.
        """
        left = []
        right = []
        differ = Differ()
        result = list(
            differ.compare(self.sections[self.left][1], self.sections[self.right][1])
        )
        for line in result:
            if line[0] == " ":
                while len(left) < len(right):
                    left.append(" ")
                while len(right) < len(left):
                    right.append(" ")
                left.append(line)
                right.append(line)
            elif line[0] == "+":
                right.append(line)
            elif line[0] == "-":
                left.append(line)
        return (left, right)


class Renderer:
    """
    Curses-specific rendering structures.
    """

    def __init__(self):
        halfwidth = curses.COLS // 2
        self.ltitle = curses.newwin(1, halfwidth, 0, 0)
        self.rtitle = curses.newwin(1, halfwidth, 0, halfwidth)
        self.lwin = curses.newwin(curses.LINES, halfwidth, 2, 0)
        self.rwin = curses.newwin(curses.LINES, halfwidth, 2, halfwidth)
        curses.init_pair(1, curses.COLOR_RED, -1)
        curses.init_pair(2, curses.COLOR_GREEN, -1)

    def render_title(self, win, text):
        win.clear()
        win.addstr(0, 0, text, curses.A_BOLD)

    def render_section(self, win, file, top):
        """
        Write a section to the screen.
        """
        win.clear()
        row = 0
        for i in range(top, len(file)):
            line = file[i]
            if line[0] == "-":
                color = curses.color_pair(1)
            elif line[0] == "+":
                color = curses.color_pair(2)
            else:
                color = curses.A_DIM
            win.addstr(row, 0, file[i], color)
            row += 1

    def render(self, state):
        """Render state to the windows for this renderer"""
        ltitle = state.sections[state.left][0]
        rtitle = state.sections[state.right][0]
        (lsec, rsec) = state.make_diff()
        self.render_title(self.ltitle, ltitle)
        self.render_section(self.lwin, lsec, state.top)
        self.render_title(self.rtitle, rtitle)
        self.render_section(self.rwin, rsec, state.top)
        self.ltitle.refresh()
        self.rtitle.refresh()
        self.lwin.refresh()
        self.rwin.refresh()


def parse_args():
    parser = argparse.ArgumentParser(prog="secdiff")
    parser.add_argument("filename")
    parser.add_argument("-s", "--separator", required=True)
    return parser.parse_args()


def run(scr, state):
    """
    Main run loop for the curses program.
    """
    curses.noecho()
    curses.cbreak()
    curses.start_color()
    curses.use_default_colors()
    curses.curs_set(0)
    scr.keypad(True)
    scr.refresh()


    renderer = Renderer()

    while True:
        renderer.render(state)
        c = scr.getch()
        if c == ord("q"):
            exit(scr)
            break
        elif c == ord("l"):
            state.next()
        elif c == ord("h"):
            state.prev()
        elif c == ord("j"):
            state.down()
        elif c == ord("k"):
            state.up()


def main():
    """
    Main method for the program.
    """
    scr = None
    try:
        args = parse_args()
        with open(args.filename, "r") as f:
            state = State(f.read(), args.separator)
        scr = curses.initscr()
        run(scr, state)
    except:
        if scr:
            exit(scr)
        raise


if __name__ == "__main__":
    main()
