#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from __future__ import print_function
import pystache

def main():
    template = "Hi {{person}}!"
    context = {"person": "Mom"}
    print(pystache.render(template, context))

if __name__ == '__main__':
    main()
